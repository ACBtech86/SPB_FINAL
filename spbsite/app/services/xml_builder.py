"""XML message builder.

Replaces MsgFormXml.asp — builds SPBDOC XML documents from validated form data.
Uses lxml.etree instead of microsoft.xmldom.
"""

from datetime import datetime

from lxml import etree
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from spb_shared.models import SPBDicionario, SPBMsgField
from spb_shared.models import SPBLocalToBacen, SPBLocalToSelic
from app.services.operation_number import generate_operation_number


def _add_xml_node(parent: etree._Element, tag: str, text: str = "") -> etree._Element:
    """Create an XML sub-element (replaces AddXmlNode from ASP)."""
    node = etree.SubElement(parent, tag)
    if text:
        node.text = text
    return node


def _determine_destination(cod_grade: str) -> tuple[str, str]:
    """Determine ISPB destination and SQL table based on COD_GRADE.

    Returns (ispb, table_name).
    """
    if cod_grade == "SEL01":
        return settings.ispb_selic, "selic"
    return settings.ispb_bacen, "bacen"


def _determine_queue_name(msg_id: str, ispb_dest: str) -> str:
    """Determine the MQ queue destination name based on message type."""
    ispb_local = settings.ispb_local
    if "R1" in msg_id or "R2" in msg_id:
        return f"QR.RSP.{ispb_local}.{ispb_dest}.01"
    return f"QR.REQ.{ispb_local}.{ispb_dest}.01"


def _convert_date(value: str) -> str:
    """Convert dd/mm/yyyy to yyyymmdd format."""
    cleaned = value.replace("/", "")
    if len(cleaned) >= 8:
        dia = cleaned[0:2]
        mes = cleaned[2:4]
        ano = cleaned[4:8]
        return f"{ano}{mes}{dia}"
    return value


def _convert_datetime(value: str) -> str:
    """Convert dd/mm/yyyy HH:MM:SS to yyyymmddHHMMSS format."""
    cleaned = value.replace("/", "").replace(" ", "").replace(":", "")
    if len(cleaned) >= 14:
        dia = cleaned[0:2]
        mes = cleaned[2:4]
        ano = cleaned[4:8]
        hora = cleaned[8:10]
        minuto = cleaned[10:12]
        segundo = cleaned[12:14]
        return f"{ano}{mes}{dia}{hora}{minuto}{segundo}"
    return value


def _convert_time(value: str) -> str:
    """Convert HH:MM:SS to HHMMSS format."""
    return value.replace(":", "")


async def build_spb_xml(
    db: AsyncSession, msg_id: str, form_data: dict
) -> tuple[str, str, str, str]:
    """Build an SPBDOC XML document from form data.

    Returns (xml_string, operation_number, destination_table, queue_name).
    """
    # Load field definitions with dictionary info
    query = (
        select(
            SPBMsgField.cod_grade,
            SPBMsgField.msg_id,
            SPBMsgField.msg_tag,
            SPBMsgField.msg_descr,
            SPBMsgField.msg_emissor,
            SPBMsgField.msg_destinatario,
            SPBMsgField.msg_seq,
            SPBMsgField.msg_cpotag,
            SPBMsgField.msg_cponome,
            SPBMsgField.msg_cpoobrig,
            SPBDicionario.msg_cpotipo,
            SPBDicionario.msg_cpotam,
            SPBDicionario.msg_cpoform,
        )
        .outerjoin(SPBDicionario, SPBMsgField.msg_cpotag == SPBDicionario.msg_cpotag)
        .where(SPBMsgField.msg_id == msg_id)
        .order_by(SPBMsgField.msg_id, SPBMsgField.msg_seq)
    )
    result = await db.execute(query)
    fields = result.all()

    if not fields:
        raise ValueError(f"Mensagem nao encontrada: {msg_id}")

    # Generate operation number
    nu_ope = generate_operation_number()

    # Determine destination
    cod_grade = (fields[0].cod_grade or "").strip()
    ispb_dest, dest_channel = _determine_destination(cod_grade)
    queue_name = _determine_queue_name(msg_id, ispb_dest)

    # Build XML document
    root = etree.Element("SPBDOC")
    bcmsg = _add_xml_node(root, "BCMSG")
    sismsg = _add_xml_node(root, "SISMSG")

    # BCMSG header
    grupo_emissor = _add_xml_node(bcmsg, "Grupo_EmissorMsg")
    _add_xml_node(grupo_emissor, "TipoId_Emissor", "P")
    _add_xml_node(grupo_emissor, "Id_Emissor", settings.ispb_local)
    dest_msg = _add_xml_node(bcmsg, "DestinatarioMsg")
    _add_xml_node(dest_msg, "TipoId_Destinatario", "P")
    _add_xml_node(dest_msg, "Id_Destinatario", ispb_dest)
    _add_xml_node(bcmsg, "NUOp", nu_ope)

    # Build SISMSG body from field definitions
    collection = [sismsg] + [None] * 10
    nivel = 0
    valor_lanc = "0,00"
    prioridade = ""

    for field in fields:
        cpotag = (field.msg_cpotag or "").strip()
        cpotipo = (field.msg_cpotipo or "").strip().lower()
        cpoform = (field.msg_cpoform or "").strip().lower()

        # Determine field type
        if not cpotipo:
            if cpotag.startswith("Grupo_"):
                cpotipo = "grupo"
            elif cpotag.startswith("Repet_"):
                cpotipo = "repeticao"
            elif cpotag.startswith("/Grupo_") or cpotag.startswith("/Repet_"):
                cpotipo = ""

        # Get form value
        form_value = form_data.get(cpotag, "")

        if not cpotipo:
            if cpotag.startswith("/"):
                nivel -= 1
            else:
                collection[0] = _add_xml_node(sismsg, cpotag)
            continue
        elif cpotipo == "grupo":
            nivel_ant = nivel
            nivel += 1
            collection[nivel] = _add_xml_node(collection[nivel_ant], cpotag)
            continue
        elif cpotipo in ("repeticao", "repetição"):
            nivel_ant = nivel
            nivel += 1
            collection[nivel] = _add_xml_node(collection[nivel_ant], cpotag)
            continue

        # Apply format conversions
        if cpoform == "data" and form_value:
            form_value = _convert_date(form_value)
        elif cpoform == "data hora" and form_value:
            form_value = _convert_datetime(form_value)
        elif cpoform == "hora" and form_value:
            form_value = _convert_time(form_value)

        # Add field to XML
        if cpotipo:
            _add_xml_node(collection[nivel], cpotag, form_value)

        # Track special values
        if cpotag == "VlrLanc":
            valor_lanc = form_value
        if cpotag == "NivelPref":
            prioridade = form_value

    # Generate final XML string
    xml_declaration = '<?xml version="1.0"?>'
    doctype = '<!DOCTYPE SPBDOC SYSTEM "SPBDOC.DTD">'
    xml_body = etree.tostring(root, encoding="unicode")
    xml_string = f"{xml_declaration}{doctype}{xml_body}"

    dest_table = "spb_local_to_selic" if dest_channel == "selic" else "spb_local_to_bacen"

    return xml_string, nu_ope, dest_table, queue_name


async def submit_message(
    db: AsyncSession, xml_string: str, msg_id: str, nu_ope: str, dest_table: str, queue_name: str
) -> None:
    """Insert the generated message into the outbound table."""
    now = datetime.now()

    if dest_table == "spb_local_to_selic":
        record = SPBLocalToSelic(
            nu_ope=nu_ope,
            cod_msg=msg_id,
            db_datetime=now,
            msg=xml_string,
            status_msg="P",
            flag_proc="P",
            mq_qn_destino=queue_name,
        )
    else:
        record = SPBLocalToBacen(
            db_datetime=now,
            status_msg="P",
            flag_proc="P",
            mq_qn_destino=queue_name,
            nu_ope=nu_ope,
            cod_msg=msg_id,
            msg=xml_string,
        )

    db.add(record)
    await db.commit()
