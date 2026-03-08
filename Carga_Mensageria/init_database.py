"""
Initializes the PostgreSQL database with all tables required by Carga Mensageria.

Creates both INPUT tables (to be populated with message specifications)
and OUTPUT tables (populated by the etapas).

Usage:
    python init_database.py
"""

import sys
import psycopg
from config import DB_CONFIG


SCHEMA_SQL = """
-- =====================================================================
-- INPUT TABLES (must be populated before running the etapas)
-- =====================================================================

-- Message catalog: one row per SPB message
CREATE TABLE IF NOT EXISTS PLAN_MENSAGEM (
    CodMsg          VARCHAR(50) PRIMARY KEY,
    Tag             TEXT,
    Nome_Mensagem   TEXT,
    EntidadeOrigem  TEXT,
    EntidadeDestino TEXT,
    TipoFluxo       TEXT
);

-- Event descriptions linked to messages
CREATE TABLE IF NOT EXISTS PLAN_EVENTO (
    Cod_Evento      VARCHAR(50) PRIMARY KEY,
    Nome_Evento     TEXT,
    Descricao       TEXT,
    Observacao      TEXT
);

-- Data dictionary: field definitions
CREATE TABLE IF NOT EXISTS PLAN_DADOS (
    Tag             VARCHAR(100) PRIMARY KEY,
    Tipologia       TEXT,
    Nome_Dado       TEXT
);

-- Type definitions: format and size for each tipologia
CREATE TABLE IF NOT EXISTS PLAN_TIPOLOGIA (
    Tipologia       VARCHAR(100) PRIMARY KEY,
    Formato         TEXT,
    Tam             TEXT
);

-- Message field structure: which fields belong to each message, in order
CREATE TABLE IF NOT EXISTS PLAN_Mensagem_Dados (
    Mensagem        VARCHAR(50),
    Seq             INTEGER,
    Tag             VARCHAR(100),
    "Obrig#"        TEXT,
    PRIMARY KEY (Mensagem, Seq)
);

-- Domain value lists (lookup tables for field validation)
CREATE TABLE IF NOT EXISTS SPB_DOMINIOS (
    TipoDado        TEXT,
    CodDominio      TEXT,
    DescrDominio    TEXT,
    CtrlPosicional  TEXT,
    PRIMARY KEY (TipoDado, CodDominio)
);

-- Institution registry (ISPB codes)
CREATE TABLE IF NOT EXISTS SPB_ISPB (
    ISPB            VARCHAR(20) PRIMARY KEY,
    Nome            TEXT
);


-- =====================================================================
-- OUTPUT TABLES (populated by the etapas)
-- =====================================================================

-- Etapa 0A: Grade schedules
CREATE TABLE IF NOT EXISTS PLAN_Grade (
    GRADE                   VARCHAR(20) PRIMARY KEY,
    "Horário Abertura"      TEXT,
    "Horário Fechamento"    TEXT
);

-- Etapa 0: Grade-to-message associations
CREATE TABLE IF NOT EXISTS PLAN_Grade_X_Msg (
    GRADE           VARCHAR(20),
    MENSAGENS       VARCHAR(50),
    PRIMARY KEY (GRADE, MENSAGENS)
);

-- Etapa 1: Grade codes with ISPB routing
CREATE TABLE IF NOT EXISTS SPB_CODGRADE (
    COD_GRADE           VARCHAR(20),
    DESC_GRADE          TEXT,
    ISPBOrigem          VARCHAR(20),
    ISPBDestino         VARCHAR(20),
    Status_Grade        VARCHAR(1),
    Horario_Inicio_Perm VARCHAR(10),
    Horario_Fim_Perm    VARCHAR(10)
);

-- Etapa 2: Grade-message-destination mapping
CREATE TABLE IF NOT EXISTS APP_CODGRADE_X_MSG (
    ISPB_Destino    VARCHAR(20),
    Cod_Msg         VARCHAR(50),
    Cod_Grade       VARCHAR(20),
    MSG_FLUXO       TEXT
);

-- Etapa 3: Consolidated message table
CREATE TABLE IF NOT EXISTS SPB_MENSAGEM (
    MSG_ID              VARCHAR(50) PRIMARY KEY,
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
    MSG_CPOTAG      VARCHAR(100) PRIMARY KEY,
    MSG_DESCRTAG    TEXT,
    MSG_CPOTIPO     TEXT,
    MSG_CPOTAM      TEXT,
    MSG_CPOFORMATO  TEXT,
    ITENS_DOMINIO   INTEGER
);

-- Etapa 5: Message field structure (denormalized)
CREATE TABLE IF NOT EXISTS SPB_MSGFIELD (
    MSG_ID              VARCHAR(50),
    MSG_TAG             TEXT,
    MSG_DESCR           TEXT,
    MSG_EMISSOR         TEXT,
    MSG_DESTINATARIO    TEXT,
    MSG_SEQ             VARCHAR(10),
    MSG_CPOTAG          VARCHAR(100),
    MSG_CPONOME         TEXT,
    MSG_CPOOBRIG        TEXT
);

-- Etapa A: Generated XML/XSL per message
CREATE TABLE IF NOT EXISTS SPB_XMLXSL (
    MSG_ID          VARCHAR(50) PRIMARY KEY,
    form_xml        TEXT,
    form_xsl        TEXT
);
"""


def init_database(db_config: dict = None):
    """Create all tables in the PostgreSQL database."""
    config = db_config or DB_CONFIG

    print(f"Conectando ao PostgreSQL em {config['host']}:{config['port']}/{config['database']}...")

    conn = psycopg.connect(
        host=config["host"],
        port=config["port"],
        dbname=config["database"],
        user=config["user"],
        password=config["password"],
    )

    try:
        cursor = conn.cursor()

        # Execute schema creation
        cursor.execute(SCHEMA_SQL)
        conn.commit()

        print(f"✓ Banco de dados inicializado: {config['database']}")

        # List created tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        print(f"\nTabelas criadas ({len(tables)}):")
        for t in tables:
            cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
            count = cursor.fetchone()[0]
            print(f"  {t:<25} ({count} registros)")

    except Exception as e:
        print(f"✗ Erro ao inicializar banco: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Allow custom config via command line (future enhancement)
    init_database()
