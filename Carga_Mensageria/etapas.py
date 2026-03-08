"""
Business logic for all ETL steps (Etapas) of the Carga Mensageria application.
Replaces all Etapa*_Click() event handlers from VB6 Etapas_Carga.frm.
"""

import os

from db_connection import DatabaseManager
from xml_generator import XmlSchemaGenerator, XslSchemaGenerator, encode_html_entities


# ---------------------------------------------------------------------------
# Constants: Hardcoded data from VB6 source
# ---------------------------------------------------------------------------

BANCO_CIDADE_ISPB = "61377677"

# Etapa 0A: Grade schedules (grade, hora_inicio, hora_fim)
GRADE_SCHEDULES = [
    ("PAG01", "08:00", "08:29"),
    ("PAG02", "08:30", "16:59"),
    ("PAG91", "17:15", "17:19"),
    ("PAG92", "17:20", "17:29"),
    ("BMC01", "08:00", "20:00"),
    ("CBL01", "08:00", "20:00"),
    ("CEN01", "08:00", "20:00"),
]

# Etapa 0: Grade-to-message mappings (grade, mensagem)
GRADE_MSG_MAPPINGS = [
    ("PAG01", "LDL0022"),
    ("PAG02", "PAG0104"), ("PAG02", "PAG0105"), ("PAG02", "PAG0106"),
    ("PAG02", "PAG0107"), ("PAG02", "PAG0108"), ("PAG02", "PAG0109"),
    ("PAG02", "PAG0110"), ("PAG02", "PAG0111"), ("PAG02", "PAG0112"),
    ("PAG02", "PAG0113"), ("PAG02", "PAG0114"), ("PAG02", "PAG0115"),
    ("PAG02", "PAG0116"), ("PAG02", "PAG0117"), ("PAG02", "PAG0118"),
    ("PAG02", "PAG0119"), ("PAG02", "PAG0120"), ("PAG02", "PAG0121"),
    ("PAG91", "PAG0112"),
    ("PAG92", "LDL0022"),
    ("BMC01", "BMC0102"), ("BMC01", "BMC0201"), ("BMC01", "BMC0202"),
    ("BMC01", "BMC0203"), ("BMC01", "BMC0204"), ("BMC01", "BMC0205"),
    ("BMC01", "BMC0250"),
    ("CBL01", "CBL0402"), ("CBL01", "CBL0406"), ("CBL01", "CBL0407"),
    ("CBL01", "CBL0409"), ("CBL01", "CBL0410"), ("CBL01", "CBL0414"),
    ("CBL01", "CBL0416"), ("CBL01", "CBL0417"), ("CBL01", "CBL1502"),
    ("CBL01", "CBL1503"), ("CBL01", "CBL1504"), ("CBL01", "CBL1904"),
    ("CEN01", "CEN0005"), ("CEN01", "CEN0007"), ("CEN01", "CEN1001"),
    ("CEN01", "CEN1002"), ("CEN01", "CEN1003"), ("CEN01", "CEN1006"),
    ("CEN01", "CEN3003"), ("CEN01", "CEN3004"), ("CEN01", "CEN3005"),
    ("CEN01", "CEN3035"), ("CEN01", "CEN4001"), ("CEN01", "CEN4002"),
    ("CEN01", "CEN4004"), ("CEN01", "CEN5004"), ("CEN01", "CEN5005"),
    ("CEN01", "CEN5006"), ("CEN01", "CEN5007"), ("CEN01", "CEN5008"),
    ("CEN01", "CEN5009"),
    ("LTR01", "LTR0002"), ("LTR01", "LTR0008"), ("LTR01", "LTR0009"),
    ("LDL01", "LDL0023"), ("LDL01", "LDL0026"), ("LDL01", "LDL1002"),
    ("LDL01", "LDL1003"), ("LDL01", "LDL1004"), ("LDL01", "LDL1005"),
    ("LDL01", "LDL1006"), ("LDL01", "LDL1007"), ("LDL01", "LDL1010"),
    ("LDL01", "LDL1012"), ("LDL01", "LDL1022"), ("LDL01", "LDL1013"),
    ("LDL01", "LDL1015"), ("LDL01", "LDL1016"), ("LDL01", "LDL1017"),
]

# Etapa 1: ISPB destination mapping per grade code
# Each entry: grade_code -> {"ispb": [list_of_ispbs], "descr": override_description_or_None}
ISPB_DESTINO_MAP = {
    "CIR01": {"ispb": ["00038166"], "descr": "Movimentação Mecir"},
    "CIR02": {"ispb": ["00038166"], "descr": "Estatistica/Ajustes/Remessas Mecir"},
    "CIR03": {"ispb": ["00038166"], "descr": "Consultas Mecir"},
    "GEN01": {
        "ispb": ["00038121", "00038166", "04391007", "04475149",
                 "28719664", "54641030", "60777661", "60934221", "51427102"],
        "descr": "Geral Genérico",
    },
    "GEN02": {
        "ispb": ["00038121", "00038166", "04391007", "04475149",
                 "28719664", "54641030", "60777661", "60934221", "51427102"],
        "descr": "Eco/Certificado",
    },
    "LDL01": {
        "ispb": ["00038166", "04391007", "04475149", "28719664",
                 "54641030", "60777661", "60934221", "51427102"],
        "descr": None,
    },
    "LDL03": {
        "ispb": ["04475149", "28719664", "54641030", "60777661", "60934221"],
        "descr": "LDL Câmaras - Confirmação",
    },
    "LTR01": {
        "ispb": ["00038166", "28719664", "60777661"],
        "descr": None,
    },
    "RCO01": {"ispb": ["00038166"], "descr": None},
    "RCO02": {"ispb": ["00038166"], "descr": "Avisos/Consultas Compulsório"},
    "RDC01": {"ispb": ["00038166"], "descr": None},
    "RDC02": {"ispb": ["00038166"], "descr": None},
    "RDC03": {"ispb": ["00038166"], "descr": None},
    "RDC05": {"ispb": ["00038166"], "descr": None},
    "RDC06": {"ispb": ["00038166"], "descr": "Liquidação associada a venda"},
    "RDC07": {"ispb": ["00038166"], "descr": "Conversão Redesconto"},
    "SEL01": {"ispb": ["00038121"], "descr": None},
    "SEL04": {"ispb": ["00038121"], "descr": "Consulta Selic"},
    "SEL05": {"ispb": ["00038121"], "descr": "Leilão Selic"},
    "SLB01": {"ispb": ["00038166"], "descr": None},
    "SLB02": {"ispb": ["00038166"], "descr": "Consulta SLB"},
    "STN01": {"ispb": ["00038166"], "descr": None},
    "STN02": {"ispb": ["00038166"], "descr": "Consulta STN"},
    "STR01": {"ispb": ["00038166"], "descr": None},
    "STR02": {"ispb": ["00038166"], "descr": None},
    "STR03": {"ispb": ["00038166"], "descr": None},
    "BMC01": {"ispb": ["60934221"], "descr": None},
    "CBL01": {"ispb": ["60777661"], "descr": None},
    "CEN01": {"ispb": ["04475149"], "descr": None},
    "CEN02": {"ispb": ["04475149"], "descr": None},
    "CEN03": {"ispb": ["04475149"], "descr": None},
    "CEN04": {"ispb": ["04475149"], "descr": None},
    "CEN05": {"ispb": ["04475149"], "descr": None},
    "CEN06": {"ispb": ["04475149"], "descr": None},
    "CEN07": {"ispb": ["04475149"], "descr": None},
    "CEN08": {"ispb": ["04475149"], "descr": None},
    "CEN09": {"ispb": ["04475149"], "descr": None},
    "CTP01": {"ispb": ["28719664"], "descr": None},
    "PAG01": {"ispb": ["00038166"], "descr": None},
    "PAG02": {"ispb": ["04391007"], "descr": None},
    "PAG03": {"ispb": ["00000000"], "descr": None},
    "PAG91": {"ispb": ["04391007"], "descr": None},
    "PAG92": {"ispb": ["00038166"], "descr": None},
    "PAG93": {"ispb": ["00000000"], "descr": None},
    "PAGC1": {"ispb": ["00000000"], "descr": None},
    "PAGC2": {"ispb": ["00000000"], "descr": None},
}

# Emitter types that are allowed to have a destination in Etapa 2
VALID_EMITTER_TYPES = {"AC ou TC", "AC", "IF", "IF-A", "IF-B", "IF-DEBITADA", "TC"}


# ---------------------------------------------------------------------------
# Default output paths (matching VB6 hardcoded paths)
# ---------------------------------------------------------------------------

DEFAULT_HTML_OUTPUT_DIR = r"C:\BCFONTES\SPB\Carga_Mensageria\HTML"
DEFAULT_ISPB_OUTPUT_DIR = r"C:\LIXO\HTML"


class EtapaExecutor:
    """Executes all ETL steps (Etapa 0A through Etapa C)."""

    def __init__(self, xsl_template_path=None, html_output_dir=None,
                 ispb_output_dir=None):
        if xsl_template_path is None:
            xsl_template_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "spbmodelo.xsl"
            )
        self.xsl_template_path = xsl_template_path
        self.html_output_dir = html_output_dir or DEFAULT_HTML_OUTPUT_DIR
        self.ispb_output_dir = ispb_output_dir or DEFAULT_ISPB_OUTPUT_DIR

    # ------------------------------------------------------------------
    # Etapa 0A - Atualiza PLAN_Grade
    # ------------------------------------------------------------------
    def etapa_0a(self, db: DatabaseManager, progress_cb=None):
        """Populate PLAN_Grade with hardcoded grade schedules."""
        db.connect()
        try:
            db.connection.execute("DELETE FROM PLAN_Grade")
            for grade, hora_ini, hora_fim in GRADE_SCHEDULES:
                db.execute_insert("PLAN_Grade", {
                    "GRADE": grade,
                    "Horário Abertura": hora_ini,
                    "Horário Fechamento": hora_fim,
                })
            db.commit()
            return f"Etapa 0A concluída: {len(GRADE_SCHEDULES)} grades inseridas."
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Etapa 0 - Atualiza PLAN_Grade_X_Msg
    # ------------------------------------------------------------------
    def etapa_0(self, db: DatabaseManager, progress_cb=None):
        """Populate PLAN_Grade_X_Msg with grade-to-message associations."""
        db.connect()
        try:
            db.connection.execute("DELETE FROM PLAN_Grade_X_Msg")
            for grade, msg in GRADE_MSG_MAPPINGS:
                db.execute_insert("PLAN_Grade_X_Msg", {
                    "GRADE": grade,
                    "MENSAGENS": msg,
                })
            db.commit()
            return f"Etapa 0 concluída: {len(GRADE_MSG_MAPPINGS)} associações inseridas."
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Etapa 1 - Geração da Tabela SPB_CODGRADE
    # ------------------------------------------------------------------
    def etapa_1(self, db: DatabaseManager, progress_cb=None):
        """Generate SPB_CODGRADE from PLAN_Grade + SPB_DOMINIOS."""
        db.connect()
        try:
            db.connection.execute("DELETE FROM SPB_CODGRADE")
            sql = (
                "SELECT PLAN_Grade.GRADE, SPB_DOMINIOS.TipoDado, "
                "SPB_DOMINIOS.CodDominio, SPB_DOMINIOS.DescrDominio, "
                'PLAN_Grade."Horário Abertura" AS HINI, '
                'PLAN_Grade."Horário Fechamento" AS HFIM '
                "FROM PLAN_Grade LEFT OUTER JOIN SPB_DOMINIOS "
                "ON PLAN_Grade.GRADE = SPB_DOMINIOS.CodDominio "
                "ORDER BY PLAN_Grade.GRADE"
            )
            rows = db.execute_query(sql)
            count = 0
            st = DatabaseManager.safe_trim

            for row in rows:
                grade = st(row.get("GRADE"))
                cod_dominio = st(row.get("CodDominio"))
                descr_dominio = st(row.get("DescrDominio"))
                hora_ini = st(row.get("HINI")) or "00:01"
                hora_fim = st(row.get("HFIM")) or "23:59"

                # Use CodDominio as grade if available
                if cod_dominio:
                    grade = cod_dominio
                if not descr_dominio:
                    descr_dominio = f"Grade {grade}"

                # Look up ISPB destinations from the mapping
                mapping = ISPB_DESTINO_MAP.get(grade)
                if mapping:
                    ispb_list = mapping["ispb"]
                    if mapping["descr"]:
                        descr_dominio = mapping["descr"]
                else:
                    ispb_list = ["00000000"]

                for ispb_dest in ispb_list:
                    db.execute_insert("SPB_CODGRADE", {
                        "COD_GRADE": grade,
                        "DESC_GRADE": descr_dominio,
                        "ISPBOrigem": BANCO_CIDADE_ISPB,
                        "ISPBDestino": ispb_dest,
                        "Status_Grade": "A",
                        "Horario_Inicio_Perm": hora_ini + "00",
                        "Horario_Fim_Perm": hora_fim + "00",
                    })
                    count += 1

            db.commit()
            return f"Etapa 1 concluída: {count} registros inseridos em SPB_CODGRADE."
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Etapa 2 - Geração da Tabela APP_CODGRADE_X_MSG
    # ------------------------------------------------------------------
    def etapa_2(self, db: DatabaseManager, progress_cb=None):
        """Generate APP_CODGRADE_X_MSG with emitter-type filtering rules."""
        db.connect()
        try:
            db.connection.execute("DELETE FROM APP_CODGRADE_X_MSG")
            # Rewritten from RIGHT JOIN (SQL Server) to LEFT JOINs for SQLite
            sql = (
                "SELECT GRADE, MSG_ID, MSG_EMISSOR, ISPBDestino, MSG_FLUXO "
                "FROM SPB_CODGRADE "
                "LEFT JOIN PLAN_Grade_X_Msg ON GRADE = COD_GRADE "
                "LEFT JOIN SPB_MENSAGEM ON MSG_ID = MENSAGENS "
                "WHERE GRADE IS NOT NULL "
                "ORDER BY GRADE, MSG_ID"
            )
            rows = db.execute_query(sql)
            count = 0
            st = DatabaseManager.safe_trim

            for row in rows:
                cod_grade = st(row.get("GRADE"))
                msg_id = st(row.get("MSG_ID"))
                msg_emissor = st(row.get("MSG_EMISSOR"))
                ispb_destino = st(row.get("ISPBDestino"))
                msg_fluxo = st(row.get("MSG_FLUXO"))

                # Filter by emitter type
                if msg_emissor not in VALID_EMITTER_TYPES:
                    ispb_destino = ""

                # R1 (response) messages have no destination
                if msg_id.endswith("R1"):
                    ispb_destino = ""

                # Special rules for GEN02
                if cod_grade == "GEN02":
                    if msg_id in ("GEN0006", "GEN0008"):
                        if ispb_destino != "00038166":
                            ispb_destino = ""

                # Special rules for LDL01
                if cod_grade == "LDL01":
                    ldl_bacen_msgs = {
                        "LDL0004", "LDL0008", "LDL0011", "LDL0014",
                        "LDL0022", "LDL0025", "LDL0027",
                    }
                    if msg_id in ldl_bacen_msgs:
                        if ispb_destino != "00038166":
                            ispb_destino = ""
                    else:
                        if ispb_destino == "00038166":
                            ispb_destino = ""
                        if ispb_destino == "51427102":
                            if msg_id == "LDL0003":
                                ispb_destino = ""
                        if ispb_destino == "04391007":
                            if msg_id not in ("LDL0003", "LDL0023", "LDL0026"):
                                ispb_destino = ""

                # Special rules for LTR01
                if cod_grade == "LTR01":
                    ltr_non_bacen_msgs = {"LTR0002", "LTR0008", "LTR0009"}
                    if msg_id in ltr_non_bacen_msgs:
                        if ispb_destino == "00038166":
                            ispb_destino = ""
                    else:
                        if ispb_destino != "00038166":
                            ispb_destino = ""

                if ispb_destino:
                    db.execute_insert("APP_CODGRADE_X_MSG", {
                        "ISPB_Destino": ispb_destino,
                        "Cod_Msg": msg_id,
                        "Cod_Grade": cod_grade,
                        "MSG_FLUXO": msg_fluxo,
                    })
                    count += 1

            db.commit()
            return f"Etapa 2 concluída: {count} registros inseridos em APP_CODGRADE_X_MSG."
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Etapa 3 - Geração da Tabela SPB_MENSAGEM
    # ------------------------------------------------------------------
    def etapa_3(self, db: DatabaseManager, progress_cb=None):
        """Generate SPB_MENSAGEM from PLAN_MENSAGEM + PLAN_EVENTO."""
        db.connect()
        try:
            db.connection.execute("DELETE FROM SPB_MENSAGEM")
            sql = (
                "SELECT * "
                "FROM PLAN_MENSAGEM M LEFT OUTER JOIN PLAN_EVENTO E "
                "ON M.CodMsg = E.Cod_Evento "
                "ORDER BY M.CodMsg"
            )
            rows = db.execute_query(sql)
            count = 0
            st = DatabaseManager.safe_trim

            for row in rows:
                db.execute_insert("SPB_MENSAGEM", {
                    "MSG_ID": st(row.get("CodMsg")),
                    "MSG_TAG": st(row.get("Tag")),
                    "MSG_DESCR": st(row.get("Nome_Mensagem")),
                    "MSG_EMISSOR": st(row.get("EntidadeOrigem")),
                    "MSG_DESTINATARIO": st(row.get("EntidadeDestino")),
                    "EVENTO_NOME": st(row.get("Nome_Evento")),
                    "EVENTO_DESCR": st(row.get("Descricao")),
                    "EVENTO_OBS": st(row.get("Observacao")),
                    "MSG_FLUXO": st(row.get("TipoFluxo")),
                })
                count += 1

            db.commit()
            return f"Etapa 3 concluída: {count} registros inseridos em SPB_MENSAGEM."
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Etapa 4 - Geração do Dicionário de Dados (SPB_DICIONARIO)
    # ------------------------------------------------------------------
    def etapa_4(self, db: DatabaseManager, progress_cb=None):
        """Generate SPB_DICIONARIO from PLAN_DADOS + PLAN_TIPOLOGIA."""
        db.connect()
        try:
            db.connection.execute("DELETE FROM SPB_DICIONARIO")
            sql = (
                "SELECT D.Tag, D.Tipologia, D.Nome_Dado, T.Formato, T.Tam "
                "FROM PLAN_DADOS D LEFT OUTER JOIN PLAN_TIPOLOGIA T "
                "ON D.Tipologia = T.Tipologia "
                "ORDER BY D.Tag"
            )
            rows = db.execute_query(sql)
            count = 0
            st = DatabaseManager.safe_trim

            for row in rows:
                tag = st(row.get("Tag"))
                tipologia = st(row.get("Tipologia"))
                nome_dado = st(row.get("Nome_Dado"))
                formato = st(row.get("Formato"))
                tam = st(row.get("Tam")).replace(".", ",")

                # Count domain entries for this tipologia
                domain_count = db.execute_scalar(
                    f"SELECT COUNT(*) FROM SPB_DOMINIOS "
                    f"WHERE TipoDado = '{tipologia}'"
                ) or 0

                db.execute_insert("SPB_DICIONARIO", {
                    "MSG_CPOTAG": tag,
                    "MSG_DESCRTAG": nome_dado,
                    "MSG_CPOTIPO": tipologia,
                    "MSG_CPOTAM": tam,
                    "MSG_CPOFORMATO": formato,
                    "ITENS_DOMINIO": int(domain_count),
                })
                count += 1

            db.commit()
            return f"Etapa 4 concluída: {count} registros inseridos em SPB_DICIONARIO."
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Etapa 5 - Geração da Tabela SPB_MSGFIELD
    # ------------------------------------------------------------------
    def etapa_5(self, db: DatabaseManager, progress_cb=None):
        """Generate SPB_MSGFIELD from PLAN_Mensagem_Dados + PLAN_Mensagem + PLAN_DADOS."""
        db.connect()
        try:
            db.connection.execute("DELETE FROM SPB_MSGFIELD")
            sql = (
                "SELECT V1.*, D.Tag AS Tipo_Tag, D.Nome_Dado FROM "
                "(SELECT M.CodMsg, M.Tag, M.Nome_Mensagem, M.EntidadeOrigem, "
                "M.EntidadeDestino, MD.Mensagem, MD.Seq, MD.Tag AS Cpo_Tag, "
                'MD."Obrig#" '
                "FROM PLAN_Mensagem_Dados MD "
                "LEFT JOIN PLAN_Mensagem M ON MD.Mensagem = M.CodMsg) AS V1 "
                "LEFT JOIN PLAN_DADOS D ON V1.Cpo_Tag = D.Tag "
                "ORDER BY V1.Mensagem, V1.Seq"
            )
            rows = db.execute_query(sql)
            count = 0
            st = DatabaseManager.safe_trim

            for row in rows:
                seq_str = st(row.get("Seq"))
                try:
                    seq_formatted = f"{int(seq_str):02d}"
                except (ValueError, TypeError):
                    seq_formatted = seq_str

                db.execute_insert("SPB_MSGFIELD", {
                    "MSG_ID": st(row.get("CodMsg")),
                    "MSG_TAG": st(row.get("Tag")),
                    "MSG_DESCR": st(row.get("Nome_Mensagem")),
                    "MSG_EMISSOR": st(row.get("EntidadeOrigem")),
                    "MSG_DESTINATARIO": st(row.get("EntidadeDestino")),
                    "MSG_SEQ": seq_formatted,
                    "MSG_CPOTAG": st(row.get("Cpo_Tag")),
                    "MSG_CPONOME": st(row.get("Nome_Dado")),
                    "MSG_CPOOBRIG": st(row.get("Obrig#")),
                })
                count += 1

            db.commit()
            return f"Etapa 5 concluída: {count} registros inseridos em SPB_MSGFIELD."
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Etapa A - Geração de Mensagens no Formato XML
    # ------------------------------------------------------------------
    def etapa_a(self, db: DatabaseManager, select_cod_msg="", progress_cb=None):
        """Generate XML schemas and XSL forms, store in SPB_XMLXSL."""
        db.connect()
        try:
            db.connection.execute("DELETE FROM SPB_XMLXSL")
            base_select = (
                "SELECT FLD.MSG_ID, FLD.MSG_TAG, FLD.MSG_DESCR, "
                "FLD.MSG_EMISSOR, FLD.MSG_DESTINATARIO, FLD.MSG_SEQ, "
                "FLD.MSG_CPOTAG, FLD.MSG_CPONOME, FLD.MSG_CPOOBRIG, "
                "DIC.MSG_CPOTIPO, DIC.MSG_CPOTAM, DIC.MSG_CPOFORMATO "
                "FROM SPB_MSGFIELD AS FLD LEFT JOIN SPB_DICIONARIO AS DIC "
                "ON FLD.MSG_CPOTAG = DIC.MSG_CPOTAG "
            )
            if select_cod_msg.strip():
                sql = base_select + f"WHERE FLD.MSG_ID = '{select_cod_msg.strip()}' "
            else:
                sql = base_select
            sql += "ORDER BY FLD.MSG_ID, FLD.MSG_SEQ"

            rows = db.execute_query(sql)

            xml_gen = XmlSchemaGenerator()
            xsl_gen = XslSchemaGenerator(self.xsl_template_path)
            st = DatabaseManager.safe_trim

            prev_msg_id = ""
            count = 0

            for row in rows:
                msg_id = st(row.get("MSG_ID"))
                msg_tag = st(row.get("MSG_TAG"))
                msg_descr = st(row.get("MSG_DESCR"))
                msg_seq = st(row.get("MSG_SEQ"))
                msg_cpotag = st(row.get("MSG_CPOTAG"))
                msg_cponome = st(row.get("MSG_CPONOME"))
                msg_cpoobrig = st(row.get("MSG_CPOOBRIG"))
                msg_cpotipo = st(row.get("MSG_CPOTIPO"))
                msg_cpotam = st(row.get("MSG_CPOTAM"))
                msg_cpoformato = st(row.get("MSG_CPOFORMATO"))

                # New message boundary: save previous and start new
                if msg_seq == "01":
                    # Save previous message's XML/XSL
                    if xml_gen.is_initialized:
                        db.execute_insert("SPB_XMLXSL", {
                            "MSG_ID": prev_msg_id,
                            "form_xml": xml_gen.get_xml_string(),
                            "form_xsl": xsl_gen.get_xsl_string(),
                        })
                        count += 1

                    # Start new message
                    xml_gen.start_new_message(msg_id, msg_tag, msg_descr)
                    xsl_gen.start_new_message()

                # Process field for XML generation
                xml_gen.process_field(
                    msg_id=msg_id,
                    msg_seq=msg_seq,
                    msg_cpotag=msg_cpotag,
                    msg_cponome=msg_cponome,
                    msg_cpoobrig=msg_cpoobrig,
                    msg_cpoformato=msg_cpoformato,
                    msg_cpotipo=msg_cpotipo,
                    msg_cpotam=msg_cpotam,
                    db_manager=db,
                )

                prev_msg_id = msg_id

            # Save the last message
            if xml_gen.is_initialized:
                db.execute_insert("SPB_XMLXSL", {
                    "MSG_ID": prev_msg_id,
                    "form_xml": xml_gen.get_xml_string(),
                    "form_xsl": xsl_gen.get_xsl_string(),
                })
                count += 1

            db.commit()
            return f"Etapa A concluída: {count} mensagens XML/XSL geradas em SPB_XMLXSL."
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Etapa B - Geração de HTML dos Domínios
    # ------------------------------------------------------------------
    def etapa_b(self, db: DatabaseManager, progress_cb=None):
        """Generate HTML files for SPB_DOMINIOS domain lists."""
        db.connect()
        try:
            sql = "SELECT * FROM SPB_DOMINIOS ORDER BY TipoDado"
            rows = db.execute_query(sql)
            st = DatabaseManager.safe_trim

            os.makedirs(self.html_output_dir, exist_ok=True)

            tipo_dado_ant = ""
            html_content = ""
            count = 0

            for row in rows:
                tipo_dado = st(row.get("TipoDado"))
                cod_dominio = st(row.get("CodDominio"))
                descr_dominio = st(row.get("DescrDominio"))

                # New domain type: save previous and start new
                if tipo_dado_ant != tipo_dado:
                    if tipo_dado_ant:
                        html_content += "</TABLE></BODY></HTML>"
                        filepath = os.path.join(
                            self.html_output_dir, f"{tipo_dado_ant}.htm"
                        )
                        with open(filepath, "w", encoding="utf-16") as f:
                            f.write(html_content)
                        count += 1
                        html_content = ""

                    tipo_dado_ant = tipo_dado
                    html_content = (
                        "<HTML xmlns:fo='http://www.w3.org/1999/XSL/Format'>"
                        "<HEAD><META http-equiv='Content-Type' content='text/html; charset=UTF-16'>"
                        f"<TITLE>Lista Tipo {tipo_dado_ant}</TITLE>"
                        "<SCRIPT language='javascript' src='../geradormsg/help.js'></SCRIPT></HEAD>"
                        "<BODY leftMargin='1' onblur='self.close()' rightMargin='1' topMargin='1'>"
                        "<TABLE align='center' border='0' cellPadding='1' cellSpacing='1' width='100%'>"
                        "<TR><TD align='middle' bgColor='midnightblue'>"
                        "<FONT color='white' face='Arial' size='2'>Lista</FONT></TD></TR>"
                        "<TR><TD bgColor='lightsteelblue'><FONT face='Arial' size='2'>"
                        "<A href='' onclick='window.close()' onmouseover=\"r('')\" "
                        "style='COLOR: navy'><FONT color='red'>Apagar</FONT></A>"
                        "</FONT></TD></TR>"
                    )

                encoded_descr = encode_html_entities(descr_dominio)
                html_content += (
                    f"<TR><TD bgColor='white'><FONT face='Arial' size='2'>"
                    f"<A href='' onclick='window.close()' "
                    f"onmouseover=\"r('{cod_dominio}')\">"
                    f"{encoded_descr}</A></FONT></TD></TR>"
                )

            # Save the last domain type
            if tipo_dado_ant:
                html_content += "</TABLE></BODY></HTML>"
                filepath = os.path.join(
                    self.html_output_dir, f"{tipo_dado_ant}.htm"
                )
                with open(filepath, "w", encoding="utf-16") as f:
                    f.write(html_content)
                count += 1

            return f"Etapa B concluída: {count} arquivos HTML de domínios gerados."
        except Exception as e:
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Etapa C - Geração de HTML do ISPB
    # ------------------------------------------------------------------
    def etapa_c(self, db: DatabaseManager, progress_cb=None):
        """Generate ISPB.htm from SPB_ISPB table."""
        db.connect()
        try:
            sql = "SELECT * FROM SPB_ISPB ORDER BY Nome"
            rows = db.execute_query(sql)
            st = DatabaseManager.safe_trim

            os.makedirs(self.ispb_output_dir, exist_ok=True)

            html_content = (
                "<HTML xmlns:fo='http://www.w3.org/1999/XSL/Format'>"
                "<HEAD><META http-equiv='Content-Type' content='text/html; charset=UTF-16'>"
                "<TITLE>Lista Tipo ISPB</TITLE>"
                "<SCRIPT language='javascript' src='../geradormsg/help.js'></SCRIPT></HEAD>"
                "<BODY leftMargin='1' onblur='self.close()' rightMargin='1' topMargin='1'>"
                "<TABLE align='center' border='0' cellPadding='1' cellSpacing='1' width='100%'>"
                "<TR><TD align='middle' bgColor='midnightblue'>"
                "<FONT color='white' face='Arial' size='2'>Lista</FONT></TD></TR>"
                "<TR><TD bgColor='lightsteelblue'><FONT face='Arial' size='2'>"
                "<A href='' onclick='window.close()' onmouseover=\"r('')\" "
                "style='COLOR: navy'><FONT color='red'>Apagar</FONT></A>"
                "</FONT></TD></TR>"
            )

            for row in rows:
                ispb = st(row.get("ISPB"))
                nome = st(row.get("Nome"))
                encoded_nome = encode_html_entities(nome)
                html_content += (
                    f"<TR><TD bgColor='white'><FONT face='Arial' size='2'>"
                    f"<A href='' onclick='window.close()' "
                    f"onmouseover=\"r('{ispb}')\">"
                    f"{encoded_nome}</A></FONT></TD></TR>"
                )

            html_content += "</TABLE></BODY></HTML>"

            filepath = os.path.join(self.ispb_output_dir, "ISPB.htm")
            with open(filepath, "w", encoding="utf-16") as f:
                f.write(html_content)

            return f"Etapa C concluída: ISPB.htm gerado com {len(rows)} registros."
        except Exception as e:
            raise
        finally:
            db.close()
