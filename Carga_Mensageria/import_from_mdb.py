"""
Imports data from legacy Access .mdb files into the SQLite database.

Reads from:
  - bdnew.mdb (Access 97, Jet3) via access-parser (pure Python)
  - Spb.mdb   (Access 2000, Jet4) via pyodbc + Access ODBC driver

Data mapping:
  bdnew.mdb -> MENSAGEM_SPB  (261 rows)  -> SPB_MENSAGEM + PLAN_MENSAGEM
  bdnew.mdb -> MSGFIELD_SPB  (3006 rows) -> SPB_MSGFIELD + PLAN_Mensagem_Dados
  bdnew.mdb -> DICIONARIO_SPB (395 rows) -> SPB_DICIONARIO + PLAN_DADOS + PLAN_TIPOLOGIA
  bdnew.mdb -> XMLXSL_SPB    (261 rows)  -> SPB_XMLXSL
  bdnew.mdb -> Instituicao   (2464 rows) -> SPB_ISPB

Requirements:
  pip install access-parser pyodbc

Usage:
  python import_from_mdb.py
"""

import os
import sqlite3
import sys

# ---------------------------------------------------------------------------
# Paths (edit these if your files are elsewhere)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB = os.path.join(SCRIPT_DIR, "BCSPBSTR.db")

MDB_DIR = os.path.join(
    os.path.dirname(SCRIPT_DIR),
    "SPBCidade", "SPB1", "SPB_FULL", "SPB_MIGUEL",
)
# Fallback: look in the original location
if not os.path.isdir(MDB_DIR):
    MDB_DIR = r"C:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\SPBCidade\SPB1\SPB_FULL\SPB_MIGUEL"

BDNEW_MDB = os.path.join(MDB_DIR, "bdnew.mdb")
SPB_MDB = os.path.join(MDB_DIR, "Spb.mdb")


def _strip(val):
    """Strip whitespace from a value, handle None and bytes."""
    if val is None:
        return ""
    if isinstance(val, bytes):
        try:
            return val.decode("cp1252").strip()
        except Exception:
            return val.decode("latin-1").strip()
    return str(val).strip()


# ---------------------------------------------------------------------------
# Read bdnew.mdb (Access 97 / Jet3) using access-parser
# ---------------------------------------------------------------------------
def read_bdnew(mdb_path):
    """Read all relevant tables from bdnew.mdb using access-parser."""
    from access_parser import AccessParser

    print(f"Abrindo {mdb_path} (access-parser)...")
    db = AccessParser(mdb_path)

    result = {}
    for table_name in ["MENSAGEM_SPB", "MSGFIELD_SPB", "DICIONARIO_SPB",
                        "XMLXSL_SPB", "Instituicao"]:
        data = db.parse_table(table_name)
        # access-parser returns {col: [values]} dict
        cols = list(data.keys())
        n = len(data[cols[0]]) if cols else 0
        rows = []
        for i in range(n):
            row = {c: _strip(data[c][i]) for c in cols}
            rows.append(row)
        result[table_name] = rows
        print(f"  {table_name}: {len(rows)} registros lidos")

    return result


# ---------------------------------------------------------------------------
# Read Spb.mdb (Access 2000 / Jet4) using pyodbc
# ---------------------------------------------------------------------------
def read_spb_mdb(mdb_path):
    """Read DICIONARIOSPB from Spb.mdb via ODBC (backup for dictionary data)."""
    import pyodbc

    print(f"Abrindo {mdb_path} (pyodbc)...")
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + mdb_path
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM DICIONARIOSPB")
    cols = [d[0] for d in cursor.description]
    rows = []
    for row in cursor.fetchall():
        rows.append({c: _strip(v) for c, v in zip(cols, row)})
    conn.close()
    print(f"  DICIONARIOSPB: {len(rows)} registros lidos")
    return rows


# ---------------------------------------------------------------------------
# Import into SQLite
# ---------------------------------------------------------------------------
def import_to_sqlite(sqlite_path, bdnew_data, spb_dicionario):
    """Load all data into the SQLite database."""
    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()

    # ---------------------------------------------------------------
    # 1. SPB_MENSAGEM + PLAN_MENSAGEM from MENSAGEM_SPB
    # ---------------------------------------------------------------
    mensagens = bdnew_data["MENSAGEM_SPB"]
    count = 0
    for r in mensagens:
        msg_id = r["MSG_ID"]
        msg_tag = r["MSG_TAG"]
        msg_descr = r.get("MSG_DESCR", "")
        msg_emissor = r["MSG_EMISSOR"]
        msg_dest = r["MSG_DESTINATARIO"]

        # SPB_MENSAGEM (output table - pre-populate for convenience)
        cur.execute(
            "INSERT OR IGNORE INTO SPB_MENSAGEM "
            "(MSG_ID, MSG_TAG, MSG_DESCR, MSG_EMISSOR, MSG_DESTINATARIO) "
            "VALUES (?, ?, ?, ?, ?)",
            (msg_id, msg_tag, msg_descr, msg_emissor, msg_dest),
        )

        # PLAN_MENSAGEM (input table for Etapa 3)
        cur.execute(
            "INSERT OR IGNORE INTO PLAN_MENSAGEM "
            "(CodMsg, Tag, Nome_Mensagem, EntidadeOrigem, EntidadeDestino) "
            "VALUES (?, ?, ?, ?, ?)",
            (msg_id, msg_tag, msg_descr, msg_emissor, msg_dest),
        )
        count += 1
    print(f"  SPB_MENSAGEM + PLAN_MENSAGEM: {count} registros importados")

    # ---------------------------------------------------------------
    # 2. SPB_MSGFIELD + PLAN_Mensagem_Dados from MSGFIELD_SPB
    # ---------------------------------------------------------------
    msgfields = bdnew_data["MSGFIELD_SPB"]
    count_field = 0
    count_plan = 0
    seen_plan = set()
    for r in msgfields:
        msg_id = r["MSG_ID"]
        msg_tag = r["MSG_TAG"]
        msg_descr = r.get("MSG_DESCR", "")
        msg_emissor = r["MSG_EMISSOR"]
        msg_dest = r["MSG_DESTINATARIO"]
        msg_seq = r["MSG_SEQ"]
        msg_cpotag = r["MSG_CPOTAG"]
        msg_cponome = r.get("MSG_CPONOME", "")
        msg_cpoobrig = r["MSG_CPOOBRIG"]

        # SPB_MSGFIELD
        cur.execute(
            "INSERT INTO SPB_MSGFIELD "
            "(MSG_ID, MSG_TAG, MSG_DESCR, MSG_EMISSOR, MSG_DESTINATARIO, "
            "MSG_SEQ, MSG_CPOTAG, MSG_CPONOME, MSG_CPOOBRIG) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (msg_id, msg_tag, msg_descr, msg_emissor, msg_dest,
             msg_seq, msg_cpotag, msg_cponome, msg_cpoobrig),
        )
        count_field += 1

        # PLAN_Mensagem_Dados (input table for Etapa 5)
        key = (msg_id, msg_seq)
        if key not in seen_plan:
            try:
                seq_int = int(msg_seq)
            except ValueError:
                seq_int = 0
            cur.execute(
                "INSERT OR IGNORE INTO PLAN_Mensagem_Dados "
                "(Mensagem, Seq, Tag, [Obrig#]) VALUES (?, ?, ?, ?)",
                (msg_id, seq_int, msg_cpotag, msg_cpoobrig),
            )
            seen_plan.add(key)
            count_plan += 1
    print(f"  SPB_MSGFIELD: {count_field} registros importados")
    print(f"  PLAN_Mensagem_Dados: {count_plan} registros importados")

    # ---------------------------------------------------------------
    # 3. SPB_DICIONARIO + PLAN_DADOS + PLAN_TIPOLOGIA from DICIONARIO_SPB
    # ---------------------------------------------------------------
    dicionario = bdnew_data["DICIONARIO_SPB"]
    count_dic = 0
    tipologias = set()
    for r in dicionario:
        tag = r["MSG_CPOTAG"]
        nome = r.get("MSG_CPONOME", "")
        tipo = r.get("MSG_CPOTIPO", "")
        tam = r.get("MSG_CPOTAM", "")

        # SPB_DICIONARIO
        cur.execute(
            "INSERT OR IGNORE INTO SPB_DICIONARIO "
            "(MSG_CPOTAG, MSG_DESCRTAG, MSG_CPOTIPO, MSG_CPOTAM, MSG_CPOFORMATO) "
            "VALUES (?, ?, ?, ?, ?)",
            (tag, nome, tipo, tam, ""),
        )

        # PLAN_DADOS (input table for Etapa 4)
        cur.execute(
            "INSERT OR IGNORE INTO PLAN_DADOS (Tag, Tipologia, Nome_Dado) "
            "VALUES (?, ?, ?)",
            (tag, tipo, nome),
        )

        # Collect tipologias for PLAN_TIPOLOGIA
        if tipo and tipo not in tipologias:
            tipologias.add(tipo)
            # Determine Formato from tipo name
            tipo_lower = tipo.lower()
            if "num" in tipo_lower:
                formato = "Numérico"
            elif "data" in tipo_lower:
                formato = "Data"
            elif "hora" in tipo_lower:
                formato = "Hora"
            else:
                formato = "Alfanumérico"
            cur.execute(
                "INSERT OR IGNORE INTO PLAN_TIPOLOGIA (Tipologia, Formato, Tam) "
                "VALUES (?, ?, ?)",
                (tipo, formato, tam),
            )
        count_dic += 1
    print(f"  SPB_DICIONARIO + PLAN_DADOS: {count_dic} registros importados")
    print(f"  PLAN_TIPOLOGIA: {len(tipologias)} tipologias importadas")

    # Supplement with Spb.mdb dictionary (has MSG_CPONOME filled in)
    count_spb = 0
    for r in spb_dicionario:
        tag = r["MSGCPOTAG"]
        nome = r.get("MSGCPONOME", "")
        tipo = r.get("MSGCPOTIPO", "")
        tam = r.get("MSGCPOTAM", "")

        if nome:
            # Update name if bdnew didn't have it
            cur.execute(
                "UPDATE SPB_DICIONARIO SET MSG_DESCRTAG = ? "
                "WHERE MSG_CPOTAG = ? AND (MSG_DESCRTAG IS NULL OR MSG_DESCRTAG = '')",
                (nome, tag),
            )
            cur.execute(
                "UPDATE PLAN_DADOS SET Nome_Dado = ? "
                "WHERE Tag = ? AND (Nome_Dado IS NULL OR Nome_Dado = '')",
                (nome, tag),
            )
            if cur.rowcount > 0:
                count_spb += 1
    if count_spb:
        print(f"  Spb.mdb supplemented {count_spb} field names")

    # ---------------------------------------------------------------
    # 4. SPB_XMLXSL from XMLXSL_SPB
    # ---------------------------------------------------------------
    xmlxsl = bdnew_data["XMLXSL_SPB"]
    count_xml = 0
    for r in xmlxsl:
        cur.execute(
            "INSERT OR IGNORE INTO SPB_XMLXSL (MSG_ID, form_xml, form_xsl) "
            "VALUES (?, ?, ?)",
            (r["MSG_ID"], r.get("FORM_XML", ""), r.get("FORM_XSL", "")),
        )
        count_xml += 1
    print(f"  SPB_XMLXSL: {count_xml} registros importados")

    # ---------------------------------------------------------------
    # 5. SPB_ISPB from Instituicao
    # ---------------------------------------------------------------
    instituicao = bdnew_data["Instituicao"]
    count_ispb = 0
    seen_ispb = set()
    for r in instituicao:
        cgc = r.get("CGCIF", "")
        nome = r.get("IF", "")
        # Extract 8-digit ISPB from the 14-digit CNPJ (first 8 chars)
        ispb = cgc[:8] if len(cgc) >= 8 else cgc
        if ispb and ispb not in seen_ispb:
            cur.execute(
                "INSERT OR IGNORE INTO SPB_ISPB (ISPB, Nome) VALUES (?, ?)",
                (ispb, nome),
            )
            seen_ispb.add(ispb)
            count_ispb += 1
    print(f"  SPB_ISPB: {count_ispb} instituições importadas")

    # ---------------------------------------------------------------
    # Commit and summarize
    # ---------------------------------------------------------------
    conn.commit()

    print("\n=== Resumo do banco SQLite ===")
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    for (tname,) in cursor.fetchall():
        cnt = conn.execute(f"SELECT COUNT(*) FROM [{tname}]").fetchone()[0]
        if cnt > 0:
            print(f"  {tname:<25} {cnt:>6} registros")
    conn.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else SQLITE_DB

    if not os.path.exists(db_path):
        print(f"Banco SQLite não encontrado: {db_path}")
        print("Execute primeiro: python init_database.py")
        sys.exit(1)

    if not os.path.exists(BDNEW_MDB):
        print(f"Arquivo não encontrado: {BDNEW_MDB}")
        sys.exit(1)

    print(f"Destino SQLite: {db_path}\n")

    # Read from .mdb files
    bdnew_data = read_bdnew(BDNEW_MDB)
    print()

    spb_dicionario = []
    if os.path.exists(SPB_MDB):
        spb_dicionario = read_spb_mdb(SPB_MDB)
        print()

    # Import to SQLite
    print("Importando para SQLite...")
    import_to_sqlite(db_path, bdnew_data, spb_dicionario)
    print("\nImportação concluída!")


if __name__ == "__main__":
    main()
