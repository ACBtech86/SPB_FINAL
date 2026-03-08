"""
import_from_xsd.py

Parses per-message XSD files from spb_schemas.zip and populates:
  - SPB_MENSAGEM    (message catalog)
  - SPB_DICIONARIO  (field dictionary)
  - SPB_MSGFIELD    (message field structure)
  - SPB_XMLXSL      (generated via Etapa A after the other 3 are loaded)

Also updates the PLAN_ input tables so that Etapas 3-5 remain functional:
  - PLAN_MENSAGEM, PLAN_EVENTO, PLAN_Mensagem_Dados, PLAN_DADOS, PLAN_TIPOLOGIA

Usage:
    python import_from_xsd.py
    python import_from_xsd.py  path/to/database.db  path/to/spb_schemas.zip
"""

import os
import sys
import zipfile
import xml.etree.ElementTree as ET

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from db_connection import DatabaseManager
from etapas import EtapaExecutor

# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------
DEFAULT_ZIP_PATH = os.path.join(SCRIPT_DIR, "spb_schemas.zip")

# ---------------------------------------------------------------------------
# XML Namespace constants
# ---------------------------------------------------------------------------
XS = "{http://www.w3.org/2001/XMLSchema}"
CAT = "{http://www.bcb.gov.br/catalogomsg}"


# ---------------------------------------------------------------------------
# XSD parsing helpers
# ---------------------------------------------------------------------------

def _find_cat_text(elem, cat_tag):
    """Find text inside a cat: namespaced child element."""
    node = elem.find(f".//{CAT}{cat_tag}")
    if node is not None and node.text:
        return node.text.strip()
    return ""


def _parse_simple_types(root):
    """Parse all xs:simpleType definitions and return a dict name→info."""
    types = {}
    for st in root.findall(f"{XS}simpleType"):
        name = st.get("name")
        if not name:
            continue

        info = {
            "name": name,
            "base": "",
            "maxLength": "",
            "minLength": "",
            "totalDigits": "",
            "fractionDigits": "",
            "pattern": "",
            "description": "",
            "format": "",
            "size": "",
            "enumerations": 0,
        }

        # Description from cat:DescricaoTipo
        doc = st.find(f".//{CAT}DescricaoTipo")
        if doc is not None and doc.text:
            info["description"] = doc.text.strip()

        # Restriction facets
        restr = st.find(f"{XS}restriction")
        if restr is not None:
            info["base"] = restr.get("base", "")
            enum_count = 0
            for child in restr:
                local_tag = child.tag.split("}")[-1]
                if local_tag in (
                    "maxLength", "minLength", "totalDigits",
                    "fractionDigits", "pattern",
                ):
                    info[local_tag] = child.get("value", "")
                elif local_tag == "enumeration":
                    enum_count += 1
            info["enumerations"] = enum_count

        # Derive format and size from base type
        base = info["base"]
        if "string" in base:
            info["format"] = "Alfanumérico"
            info["size"] = info["maxLength"]
        elif "integer" in base:
            info["format"] = "Numérico"
            info["size"] = info["totalDigits"]
        elif "decimal" in base:
            info["format"] = "Numérico"
            if info["totalDigits"] and info["fractionDigits"]:
                info["size"] = f"{info['totalDigits']},{info['fractionDigits']}"
            else:
                info["size"] = info["totalDigits"]
        elif "dateTime" in base:
            info["format"] = "DataHora"
            info["size"] = "24"
        elif "date" in base:
            info["format"] = "Data"
            info["size"] = "10"

        types[name] = info
    return types


def _index_complex_types(root):
    """Build a dict of complexType name→element."""
    cts = {}
    for ct in root.findall(f"{XS}complexType"):
        name = ct.get("name", "")
        if name:
            cts[name] = ct
    return cts


def _flatten_sequence(seq_elem, complex_types, fields):
    """Recursively flatten an xs:sequence into a flat field list."""
    for child in seq_elem:
        local_tag = child.tag.split("}")[-1]

        if local_tag == "element":
            _process_element(child, complex_types, fields)
        elif local_tag == "choice":
            # All choice alternatives are effectively optional
            for choice_child in child:
                choice_tag = choice_child.tag.split("}")[-1]
                if choice_tag == "element":
                    _process_element(choice_child, complex_types, fields,
                                     force_optional=True)

def _process_element(elem, complex_types, fields, force_optional=False):
    """Process a single xs:element and append to fields list."""
    field_name = elem.get("name", "")
    field_type = elem.get("type", "")
    min_occurs = elem.get("minOccurs", "1")

    required = "N" if (min_occurs == "0" or force_optional) else "S"

    field_info = {
        "tag": field_name,
        "type": field_type,
        "required": required,
        "name": "",
        "description": "",
    }

    # Get annotation (cat:InfCampo)
    inf_campo = elem.find(f".//{CAT}InfCampo")
    if inf_campo is not None:
        nc = inf_campo.find(f"{CAT}NomeCampo")
        dc = inf_campo.find(f"{CAT}DescricaoCampo")
        if nc is not None and nc.text:
            field_info["name"] = nc.text.strip()
        if dc is not None and dc.text:
            field_info["description"] = dc.text.strip()

    # Check if the type resolves to a complexType (Grupo_/Repet_ group)
    if field_type in complex_types:
        # Add the group element itself as a marker
        fields.append(field_info)
        # Recurse into its children
        ct = complex_types[field_type]
        sub_seq = ct.find(f"{XS}sequence")
        if sub_seq is not None:
            _flatten_sequence(sub_seq, complex_types, fields)
    else:
        fields.append(field_info)


def parse_xsd(content, filename):
    """
    Parse a single XSD file.

    Returns:
        messages:      list of dicts with SPB_MENSAGEM column data
        fields_by_msg: dict of msg_id → list of field dicts
        types:         dict of simpleType name → type info
    """
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"  WARNING: Cannot parse {filename}: {e}")
        return [], {}, {}

    simple_types = _parse_simple_types(root)
    complex_types = _index_complex_types(root)

    # --- Event-level annotation from <DOC> element ---
    evento_info = {}
    doc_elem = root.find(f"{XS}element[@name='DOC']")
    if doc_elem is not None:
        inf_ev = doc_elem.find(f".//{CAT}InfEvento")
        if inf_ev is not None:
            for tag_name in ("Evento", "Descricao", "Servico", "TipoFluxo"):
                el = inf_ev.find(f"{CAT}{tag_name}")
                evento_info[tag_name] = (
                    el.text.strip() if el is not None and el.text else ""
                )

    # --- Messages from SISMSGComplexType ---
    messages = []
    fields_by_msg = {}

    sismsg_ct = complex_types.get("SISMSGComplexType")
    if sismsg_ct is None:
        return messages, fields_by_msg, simple_types

    choice = sismsg_ct.find(f"{XS}choice")
    if choice is None:
        return messages, fields_by_msg, simple_types

    for elem in choice.findall(f"{XS}element"):
        msg_id = elem.get("name", "")
        msg_type_name = elem.get("type", "")

        msg_info = {
            "MSG_ID": msg_id,
            "MSG_TAG": msg_id,
            "MSG_DESCR": "",
            "MSG_EMISSOR": "",
            "MSG_DESTINATARIO": "",
            "MSG_FLUXO": evento_info.get("TipoFluxo", ""),
            "EVENTO_NOME": evento_info.get("Servico", ""),
            "EVENTO_DESCR": evento_info.get("Descricao", ""),
            "EVENTO_OBS": "",
        }

        # Message-level annotation (cat:InfMensagem)
        inf_msg = elem.find(f".//{CAT}InfMensagem")
        if inf_msg is not None:
            m = inf_msg.find(f"{CAT}Mensagem")
            e = inf_msg.find(f"{CAT}Emissor")
            d = inf_msg.find(f"{CAT}Destinatario")
            if m is not None and m.text:
                msg_info["MSG_DESCR"] = m.text.strip()
            if e is not None and e.text:
                msg_info["MSG_EMISSOR"] = e.text.strip()
            if d is not None and d.text:
                msg_info["MSG_DESTINATARIO"] = d.text.strip()

        messages.append(msg_info)

        # Flatten message body fields
        fields = []
        ct = complex_types.get(msg_type_name)
        if ct is not None:
            seq = ct.find(f"{XS}sequence")
            if seq is not None:
                _flatten_sequence(seq, complex_types, fields)
        fields_by_msg[msg_id] = fields

    return messages, fields_by_msg, simple_types


def get_type_info(type_name, all_types):
    """Return format/size info for a field's type attribute."""
    if type_name in all_types:
        return all_types[type_name]

    # Built-in XSD types
    if "dateTime" in type_name:
        return {"format": "DataHora", "size": "24", "enumerations": 0}
    if "date" in type_name:
        return {"format": "Data", "size": "10", "enumerations": 0}
    if "integer" in type_name or "decimal" in type_name:
        return {"format": "Numérico", "size": "", "enumerations": 0}
    if "string" in type_name:
        return {"format": "Alfanumérico", "size": "", "enumerations": 0}

    # Complex type used as field type (Grupo_/Repet_) — no size
    return {"format": "", "size": "", "enumerations": 0}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Resolve paths
    if len(sys.argv) > 1:
        zip_path = sys.argv[1]
    else:
        zip_path = DEFAULT_ZIP_PATH

    print(f"ZIP file : {zip_path}")

    if not os.path.exists(zip_path):
        print(f"ERROR: ZIP file not found: {zip_path}")
        sys.exit(1)

    # ---------------------------------------------------------------
    # Phase 1: Parse all XSD files
    # ---------------------------------------------------------------
    print(f"\nOpening ZIP...")
    z = zipfile.ZipFile(zip_path)
    xsd_files = sorted(n for n in z.namelist() if n.upper().endswith(".XSD"))
    print(f"Found {len(xsd_files)} XSD files")

    all_messages = []       # list of msg_info dicts (deduplicated)
    seen_msg_ids = set()    # track inserted MSG_IDs to avoid duplicates
    all_fields = {}         # msg_id → [field_info, ...]
    all_types = {}          # type_name → type info (merged from all files)
    skipped = 0
    dup_skipped = 0

    for xsd_path in xsd_files:
        content = z.read(xsd_path).decode("iso-8859-1")
        filename = xsd_path.split("/")[-1]

        messages, fields_by_msg, types = parse_xsd(content, filename)

        if not messages:
            skipped += 1
            continue

        # Deduplicate: E-variant XSDs redefine the base message;
        # since files are sorted alphabetically, the base XSD
        # (e.g. BMC0102.XSD with R1/R2) is processed before the
        # E variant (BMC0102E.XSD with just the base). First wins.
        for msg in messages:
            mid = msg["MSG_ID"]
            if mid not in seen_msg_ids:
                all_messages.append(msg)
                seen_msg_ids.add(mid)
                all_fields[mid] = fields_by_msg.get(mid, [])
            else:
                dup_skipped += 1

        # Merge simple types (first occurrence wins — they're identical across files)
        for name, info in types.items():
            if name not in all_types:
                all_types[name] = info

    z.close()

    print(f"\nParsing complete:")
    print(f"  Messages (unique)   : {len(all_messages)}")
    print(f"  Duplicates skipped  : {dup_skipped}")
    print(f"  Unique simple types : {len(all_types)}")
    print(f"  XSD files skipped   : {skipped}")

    # Build unique field dictionary (tag → best info)
    dict_entries = {}
    for msg_id, fields in all_fields.items():
        for field in fields:
            tag = field["tag"]
            if tag not in dict_entries:
                dict_entries[tag] = field
            else:
                # Prefer the entry that has a name
                if not dict_entries[tag]["name"] and field["name"]:
                    dict_entries[tag] = field

    print(f"  Unique field tags   : {len(dict_entries)}")

    # ---------------------------------------------------------------
    # Phase 2: Populate database
    # ---------------------------------------------------------------
    from config import DB_CONFIG
    print(f"\nConnecting to PostgreSQL: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    db = DatabaseManager()
    db.connect()

    try:
        # --- Clear all target tables ---
        print("Clearing tables...")
        for tbl in (
            "SPB_MENSAGEM", "SPB_DICIONARIO", "SPB_MSGFIELD", "SPB_XMLXSL",
            "PLAN_MENSAGEM", "PLAN_EVENTO", "PLAN_Mensagem_Dados",
            "PLAN_DADOS", "PLAN_TIPOLOGIA",
        ):
            db.connection.execute(f'DELETE FROM "{tbl}"')

        # --- SPB_MENSAGEM ---
        print("Populating SPB_MENSAGEM...")
        msg_count = 0
        for msg in all_messages:
            db.execute_insert("SPB_MENSAGEM", {
                "MSG_ID":           msg["MSG_ID"],
                "MSG_TAG":          msg["MSG_TAG"],
                "MSG_DESCR":        msg["MSG_DESCR"],
                "MSG_EMISSOR":      msg["MSG_EMISSOR"],
                "MSG_DESTINATARIO": msg["MSG_DESTINATARIO"],
                "EVENTO_NOME":      msg["EVENTO_NOME"],
                "EVENTO_DESCR":     msg["EVENTO_DESCR"],
                "EVENTO_OBS":       msg["EVENTO_OBS"],
                "MSG_FLUXO":        msg["MSG_FLUXO"],
            })
            msg_count += 1
        print(f"  {msg_count} messages inserted")

        # --- PLAN_MENSAGEM + PLAN_EVENTO (input tables for Etapas 3) ---
        print("Populating PLAN_MENSAGEM and PLAN_EVENTO...")
        plan_msg_count = 0
        plan_evt_count = 0
        for msg in all_messages:
            db.execute_insert("PLAN_MENSAGEM", {
                "CodMsg":          msg["MSG_ID"],
                "Tag":             msg["MSG_TAG"],
                "Nome_Mensagem":   msg["MSG_DESCR"],
                "EntidadeOrigem":  msg["MSG_EMISSOR"],
                "EntidadeDestino": msg["MSG_DESTINATARIO"],
                "TipoFluxo":      msg["MSG_FLUXO"],
            })
            plan_msg_count += 1

            if msg["EVENTO_NOME"] or msg["EVENTO_DESCR"]:
                try:
                    db.execute_insert("PLAN_EVENTO", {
                        "Cod_Evento":  msg["MSG_ID"],
                        "Nome_Evento": msg["EVENTO_NOME"],
                        "Descricao":   msg["EVENTO_DESCR"],
                        "Observacao":  msg["EVENTO_OBS"],
                    })
                    plan_evt_count += 1
                except Exception:
                    pass  # Duplicate Cod_Evento (R1/R2 share same event)
        print(f"  {plan_msg_count} PLAN_MENSAGEM, {plan_evt_count} PLAN_EVENTO")

        # --- SPB_DICIONARIO + PLAN_DADOS + PLAN_TIPOLOGIA ---
        print("Populating SPB_DICIONARIO, PLAN_DADOS, PLAN_TIPOLOGIA...")
        dict_count = 0
        tipologia_inserted = set()

        for tag in sorted(dict_entries.keys()):
            field = dict_entries[tag]
            type_info = get_type_info(field["type"], all_types)
            fmt = type_info.get("format", "")
            size = type_info.get("size", "")
            enums = type_info.get("enumerations", 0)

            db.execute_insert("SPB_DICIONARIO", {
                "MSG_CPOTAG":    tag,
                "MSG_DESCRTAG":  field["name"],
                "MSG_CPOTIPO":   field["type"],
                "MSG_CPOTAM":    size,
                "MSG_CPOFORMATO": fmt,
                "ITENS_DOMINIO": enums,
            })
            dict_count += 1

            # PLAN_DADOS (field tag → tipologia mapping)
            try:
                db.execute_insert("PLAN_DADOS", {
                    "Tag":       tag,
                    "Tipologia": field["type"],
                    "Nome_Dado": field["name"],
                })
            except Exception:
                pass  # Duplicate tag

            # PLAN_TIPOLOGIA (type definitions)
            tipo = field["type"]
            if tipo and tipo not in tipologia_inserted:
                try:
                    db.execute_insert("PLAN_TIPOLOGIA", {
                        "Tipologia": tipo,
                        "Formato":   fmt,
                        "Tam":       size,
                    })
                    tipologia_inserted.add(tipo)
                except Exception:
                    tipologia_inserted.add(tipo)

        print(f"  {dict_count} SPB_DICIONARIO, "
              f"{dict_count} PLAN_DADOS, "
              f"{len(tipologia_inserted)} PLAN_TIPOLOGIA")

        # --- SPB_MSGFIELD + PLAN_Mensagem_Dados ---
        print("Populating SPB_MSGFIELD and PLAN_Mensagem_Dados...")
        field_count = 0
        pmd_count = 0

        for msg in all_messages:
            msg_id = msg["MSG_ID"]
            fields = all_fields.get(msg_id, [])

            for seq_num, field in enumerate(fields, 1):
                seq_str = f"{seq_num:02d}"

                db.execute_insert("SPB_MSGFIELD", {
                    "MSG_ID":           msg_id,
                    "MSG_TAG":          msg["MSG_TAG"],
                    "MSG_DESCR":        msg["MSG_DESCR"],
                    "MSG_EMISSOR":      msg["MSG_EMISSOR"],
                    "MSG_DESTINATARIO": msg["MSG_DESTINATARIO"],
                    "MSG_SEQ":          seq_str,
                    "MSG_CPOTAG":       field["tag"],
                    "MSG_CPONOME":      field["name"],
                    "MSG_CPOOBRIG":     field["required"],
                })
                field_count += 1

                # PLAN_Mensagem_Dados
                obrig = "X" if field["required"] == "S" else ""
                try:
                    db.execute_insert("PLAN_Mensagem_Dados", {
                        "Mensagem": msg_id,
                        "Seq":      seq_num,
                        "Tag":      field["tag"],
                        "Obrig#":   obrig,
                    })
                    pmd_count += 1
                except Exception:
                    pass  # Duplicate (Mensagem, Seq)

        print(f"  {field_count} SPB_MSGFIELD, {pmd_count} PLAN_Mensagem_Dados")

        db.commit()
        print("\nAll tables populated successfully!")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

    # ---------------------------------------------------------------
    # Phase 3: Generate SPB_XMLXSL via Etapa A
    # ---------------------------------------------------------------
    print("\nGenerating SPB_XMLXSL (Etapa A)...")
    try:
        executor = EtapaExecutor()
        result = executor.etapa_a(db)
        print(f"  {result}")
    except Exception as e:
        print(f"  WARNING: SPB_XMLXSL generation failed: {e}")
        print("  You can generate it later by clicking Etapa A in the GUI.")

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    db2 = DatabaseManager()
    db2.connect()
    try:
        for tbl in (
            "SPB_MENSAGEM", "SPB_DICIONARIO", "SPB_MSGFIELD", "SPB_XMLXSL",
            "PLAN_MENSAGEM", "PLAN_EVENTO", "PLAN_Mensagem_Dados",
            "PLAN_DADOS", "PLAN_TIPOLOGIA",
        ):
            cnt = db2.execute_scalar(f'SELECT COUNT(*) FROM "{tbl}"')
            print(f"  {tbl:<25} {cnt:>6} rows")
    finally:
        db2.close()

    print("\nDone!")


if __name__ == "__main__":
    main()
