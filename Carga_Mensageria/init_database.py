"""
Initializes the SQLite database with all tables required by Carga Mensageria.

Creates both INPUT tables (to be populated with message specifications)
and OUTPUT tables (populated by the etapas).

Usage:
    python init_database.py              # creates BCSPBSTR.db in current dir
    python init_database.py mydata.db    # creates at specified path
"""

import os
import sqlite3
import sys


SCHEMA_SQL = """
-- =====================================================================
-- INPUT TABLES (must be populated before running the etapas)
-- =====================================================================

-- Message catalog: one row per SPB message
CREATE TABLE IF NOT EXISTS PLAN_MENSAGEM (
    CodMsg          TEXT PRIMARY KEY,   -- e.g. 'GEN0001'
    Tag             TEXT,               -- XML root tag, e.g. 'GENReqECO'
    Nome_Mensagem   TEXT,               -- description
    EntidadeOrigem  TEXT,               -- sender type: IF, AC, TC, etc.
    EntidadeDestino TEXT,               -- receiver type
    TipoFluxo       TEXT                -- flow type
);

-- Event descriptions linked to messages
CREATE TABLE IF NOT EXISTS PLAN_EVENTO (
    Cod_Evento      TEXT PRIMARY KEY,   -- matches PLAN_MENSAGEM.CodMsg
    Nome_Evento     TEXT,
    Descricao       TEXT,
    Observacao      TEXT
);

-- Data dictionary: field definitions
CREATE TABLE IF NOT EXISTS PLAN_DADOS (
    Tag             TEXT PRIMARY KEY,   -- field tag name, e.g. 'CodMsg'
    Tipologia       TEXT,               -- type category (FK to PLAN_TIPOLOGIA)
    Nome_Dado       TEXT                -- human-readable field name
);

-- Type definitions: format and size for each tipologia
CREATE TABLE IF NOT EXISTS PLAN_TIPOLOGIA (
    Tipologia       TEXT PRIMARY KEY,   -- e.g. 'CodMsg'
    Formato         TEXT,               -- 'Alfanumérico', 'Numérico'
    Tam             TEXT                -- size: '7' or '15,2' (integer,decimal)
);

-- Message field structure: which fields belong to each message, in order
-- Special Tag prefixes:
--   'Repet_xxx'  = start of repeating group
--   'Grupo_xxx'  = start of optional group
--   '/Repet_xxx' = end of repeating group
--   '/Grupo_xxx' = end of optional group
CREATE TABLE IF NOT EXISTS PLAN_Mensagem_Dados (
    Mensagem        TEXT,               -- message code (FK to PLAN_MENSAGEM)
    Seq             INTEGER,            -- field sequence number
    Tag             TEXT,               -- field tag (FK to PLAN_DADOS)
    [Obrig#]        TEXT,               -- required: 'X' = yes, '' = no
    PRIMARY KEY (Mensagem, Seq)
);

-- Domain value lists (lookup tables for field validation)
CREATE TABLE IF NOT EXISTS SPB_DOMINIOS (
    TipoDado        TEXT,               -- domain type name
    CodDominio      TEXT,               -- code value
    DescrDominio    TEXT,               -- description
    CtrlPosicional  TEXT,
    PRIMARY KEY (TipoDado, CodDominio)
);

-- Institution registry (ISPB codes)
CREATE TABLE IF NOT EXISTS SPB_ISPB (
    ISPB            TEXT PRIMARY KEY,   -- 8-digit ISPB code
    Nome            TEXT                -- institution name
);


-- =====================================================================
-- OUTPUT TABLES (populated by the etapas)
-- =====================================================================

-- Etapa 0A: Grade schedules
CREATE TABLE IF NOT EXISTS PLAN_Grade (
    GRADE                   TEXT PRIMARY KEY,
    [Horário Abertura]      TEXT,
    [Horário Fechamento]    TEXT
);

-- Etapa 0: Grade-to-message associations
CREATE TABLE IF NOT EXISTS PLAN_Grade_X_Msg (
    GRADE           TEXT,
    MENSAGENS       TEXT,
    PRIMARY KEY (GRADE, MENSAGENS)
);

-- Etapa 1: Grade codes with ISPB routing
CREATE TABLE IF NOT EXISTS SPB_CODGRADE (
    COD_GRADE           TEXT,
    DESC_GRADE          TEXT,
    ISPBOrigem          TEXT,
    ISPBDestino         TEXT,
    Status_Grade        TEXT,
    Horario_Inicio_Perm TEXT,
    Horario_Fim_Perm    TEXT
);

-- Etapa 2: Grade-message-destination mapping
CREATE TABLE IF NOT EXISTS APP_CODGRADE_X_MSG (
    ISPB_Destino    TEXT,
    Cod_Msg         TEXT,
    Cod_Grade       TEXT,
    MSG_FLUXO       TEXT
);

-- Etapa 3: Consolidated message table
CREATE TABLE IF NOT EXISTS SPB_MENSAGEM (
    MSG_ID              TEXT PRIMARY KEY,
    MSG_TAG             TEXT,
    MSG_DESCR           TEXT,
    MSG_EMISSOR         TEXT,
    MSG_DESTINATARIO    TEXT,
    EVENTO_NOME         TEXT,
    EVENTO_DESCR        TEXT,
    EVENTO_OBS          TEXT,
    MSG_FLUXO           TEXT
);

-- Etapa 4: Data dictionary with domain counts
CREATE TABLE IF NOT EXISTS SPB_DICIONARIO (
    MSG_CPOTAG      TEXT PRIMARY KEY,
    MSG_DESCRTAG    TEXT,
    MSG_CPOTIPO     TEXT,
    MSG_CPOTAM      TEXT,
    MSG_CPOFORMATO  TEXT,
    ITENS_DOMINIO   INTEGER
);

-- Etapa 5: Message field structure (denormalized)
CREATE TABLE IF NOT EXISTS SPB_MSGFIELD (
    MSG_ID              TEXT,
    MSG_TAG             TEXT,
    MSG_DESCR           TEXT,
    MSG_EMISSOR         TEXT,
    MSG_DESTINATARIO    TEXT,
    MSG_SEQ             TEXT,
    MSG_CPOTAG          TEXT,
    MSG_CPONOME         TEXT,
    MSG_CPOOBRIG        TEXT
);

-- Etapa A: Generated XML/XSL per message
CREATE TABLE IF NOT EXISTS SPB_XMLXSL (
    MSG_ID          TEXT PRIMARY KEY,
    form_xml        TEXT,
    form_xsl        TEXT
);
"""


def init_database(db_path: str):
    """Create all tables in the SQLite database."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        print(f"Banco de dados inicializado: {db_path}")

        # List created tables
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tabelas criadas ({len(tables)}):")
        for t in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
            print(f"  {t:<25} ({count} registros)")
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BCSPBSTR.db")

    init_database(path)
