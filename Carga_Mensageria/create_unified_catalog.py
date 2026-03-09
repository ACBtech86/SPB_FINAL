#!/usr/bin/env python3
"""
Create unified SPB catalog database.

This database will be shared across all SPB projects:
  - Carga_Mensageria (ETL tool - writes catalog)
  - BCSrvSqlMq (message processor - reads catalog)
  - SPBSite (web interface - reads catalog)

Database: spb_catalog
Purpose: Single source of truth for SPB message definitions
"""

import sys
import psycopg
from psycopg import sql
from psycopg.errors import DuplicateDatabase

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': '',  # Set via environment or edit here
}
CATALOG_DB = 'spb_catalog'

# Unified schema combining best features from all projects
SCHEMA_SQL = """
-- =====================================================================
-- UNIFIED SPB CATALOG SCHEMA
-- Single source of truth for all SPB projects
-- =====================================================================

-- Message catalog: comprehensive message definitions
CREATE TABLE IF NOT EXISTS SPB_MENSAGEM (
    MSG_ID              VARCHAR(50)  PRIMARY KEY,
    MSG_TAG             VARCHAR(100),
    MSG_DESCR           TEXT,
    MSG_EMISSOR         VARCHAR(100),
    MSG_DESTINATARIO    VARCHAR(100),
    EVENTO_NOME         TEXT,
    EVENTO_DESCR        TEXT,
    EVENTO_OBS          TEXT,
    MSG_FLUXO           VARCHAR(50),

    -- Audit fields
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_spb_mensagem_fluxo ON SPB_MENSAGEM(MSG_FLUXO);
COMMENT ON TABLE SPB_MENSAGEM IS 'Comprehensive SPB message type catalog';

-- Field type dictionary: data type definitions
CREATE TABLE IF NOT EXISTS SPB_DICIONARIO (
    MSG_CPOTAG          VARCHAR(100) PRIMARY KEY,
    MSG_DESCRTAG        TEXT,
    MSG_CPOTIPO         VARCHAR(100),
    MSG_CPOTAM          VARCHAR(20),
    MSG_CPOFORMATO      VARCHAR(50),
    ITENS_DOMINIO       INTEGER DEFAULT 0,

    -- Audit fields
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_spb_dicionario_tipo ON SPB_DICIONARIO(MSG_CPOTIPO);
COMMENT ON TABLE SPB_DICIONARIO IS 'Field type dictionary and data definitions';

-- Message field structure: denormalized field definitions per message
CREATE TABLE IF NOT EXISTS SPB_MSGFIELD (
    id                  SERIAL PRIMARY KEY,
    MSG_ID              VARCHAR(50)  NOT NULL,
    MSG_TAG             VARCHAR(100),
    MSG_DESCR           TEXT,
    MSG_EMISSOR         VARCHAR(100),
    MSG_DESTINATARIO    VARCHAR(100),
    MSG_SEQ             VARCHAR(10),
    MSG_CPOTAG          VARCHAR(100),
    MSG_CPONOME         TEXT,
    MSG_CPOOBRIG        VARCHAR(10),
    COD_GRADE           VARCHAR(50),

    -- Foreign keys
    FOREIGN KEY (MSG_ID) REFERENCES SPB_MENSAGEM(MSG_ID) ON DELETE CASCADE,
    FOREIGN KEY (MSG_CPOTAG) REFERENCES SPB_DICIONARIO(MSG_CPOTAG) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_spb_msgfield_msg_id ON SPB_MSGFIELD(MSG_ID);
CREATE INDEX IF NOT EXISTS idx_spb_msgfield_seq ON SPB_MSGFIELD(MSG_ID, MSG_SEQ);
CREATE INDEX IF NOT EXISTS idx_spb_msgfield_tag ON SPB_MSGFIELD(MSG_CPOTAG);
CREATE INDEX IF NOT EXISTS idx_spb_msgfield_grade ON SPB_MSGFIELD(COD_GRADE);
COMMENT ON TABLE SPB_MSGFIELD IS 'Denormalized message field structures';

-- XML/XSL form definitions
CREATE TABLE IF NOT EXISTS SPB_XMLXSL (
    MSG_ID              VARCHAR(50)  PRIMARY KEY,
    form_xml            TEXT,
    form_xsl            TEXT,

    -- Audit fields
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key
    FOREIGN KEY (MSG_ID) REFERENCES SPB_MENSAGEM(MSG_ID) ON DELETE CASCADE
);

COMMENT ON TABLE SPB_XMLXSL IS 'Generated XML form schemas and XSL stylesheets';

-- Domain value lists (for field validation)
CREATE TABLE IF NOT EXISTS SPB_DOMINIOS (
    TipoDado            VARCHAR(100) NOT NULL,
    CodDominio          VARCHAR(100) NOT NULL,
    DescrDominio        TEXT,
    CtrlPosicional      VARCHAR(10),

    PRIMARY KEY (TipoDado, CodDominio)
);

CREATE INDEX IF NOT EXISTS idx_spb_dominios_tipo ON SPB_DOMINIOS(TipoDado);
COMMENT ON TABLE SPB_DOMINIOS IS 'Domain value lists for field validation';

-- Institution registry (ISPB codes)
CREATE TABLE IF NOT EXISTS SPB_ISPB (
    ISPB                VARCHAR(20)  PRIMARY KEY,
    Nome                TEXT,

    -- Audit fields
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE SPB_ISPB IS 'Brazilian payment system institution registry';

-- =====================================================================
-- COMPATIBILITY VIEWS FOR LEGACY PROJECTS
-- =====================================================================

-- View for BCSrvSqlMq (simplified schema)
CREATE OR REPLACE VIEW spb_mensagem_simple AS
SELECT
    MSG_ID,
    MSG_DESCR
FROM SPB_MENSAGEM;

COMMENT ON VIEW spb_mensagem_simple IS 'Simplified message catalog for BCSrvSqlMq compatibility';

-- View for SPBSite (lowercase naming)
CREATE OR REPLACE VIEW spb_mensagem_view AS
SELECT
    MSG_ID as msg_id,
    MSG_DESCR as msg_descr,
    MSG_TAG as msg_tag,
    MSG_EMISSOR as msg_emissor,
    MSG_DESTINATARIO as msg_destinatario
FROM SPB_MENSAGEM;

CREATE OR REPLACE VIEW spb_dicionario_view AS
SELECT
    MSG_CPOTAG as msg_cpotag,
    MSG_CPOTIPO as msg_cpotipo,
    MSG_CPOTAM as msg_cpotam,
    MSG_CPOFORMATO as msg_cpoform
FROM SPB_DICIONARIO;

CREATE OR REPLACE VIEW spb_msgfield_view AS
SELECT
    id,
    COD_GRADE as cod_grade,
    MSG_ID as msg_id,
    MSG_TAG as msg_tag,
    MSG_DESCR as msg_descr,
    MSG_EMISSOR as msg_emissor,
    MSG_DESTINATARIO as msg_destinatario,
    MSG_SEQ::INTEGER as msg_seq,
    MSG_CPOTAG as msg_cpotag,
    MSG_CPONOME as msg_cponome,
    MSG_CPOOBRIG as msg_cpoobrig
FROM SPB_MSGFIELD
ORDER BY MSG_ID, MSG_SEQ;

COMMENT ON VIEW spb_mensagem_view IS 'SPBSite compatibility view (lowercase)';
COMMENT ON VIEW spb_dicionario_view IS 'SPBSite compatibility view (lowercase)';
COMMENT ON VIEW spb_msgfield_view IS 'SPBSite compatibility view (lowercase)';

-- =====================================================================
-- HELPER FUNCTIONS
-- =====================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_spb_mensagem_updated_at
    BEFORE UPDATE ON SPB_MENSAGEM
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spb_dicionario_updated_at
    BEFORE UPDATE ON SPB_DICIONARIO
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spb_xmlxsl_updated_at
    BEFORE UPDATE ON SPB_XMLXSL
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spb_ispb_updated_at
    BEFORE UPDATE ON SPB_ISPB
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""


def create_catalog_database():
    """Create the unified catalog database."""
    print("=" * 70)
    print("UNIFIED SPB CATALOG DATABASE SETUP")
    print("=" * 70)
    print(f"Database: {CATALOG_DB}")
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"User: {DB_CONFIG['user']}")
    print("=" * 70)

    # Step 1: Create database
    print("\n[Step 1/3] Creating database...")
    try:
        conn = psycopg.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()

        # Check if database exists
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (CATALOG_DB,)
        )
        exists = cur.fetchone()

        if exists:
            print(f"  [WARN]  Database '{CATALOG_DB}' already exists")
            response = input("  Delete and recreate? [y/N]: ").strip().lower()
            if response == 'y':
                # Terminate existing connections
                cur.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{CATALOG_DB}'
                    AND pid <> pg_backend_pid()
                """)
                cur.execute(f'DROP DATABASE "{CATALOG_DB}"')
                print(f"  [OK] Old database dropped")
            else:
                print("  [INFO]  Using existing database")
                cur.close()
                conn.close()
                return True

        if not exists or response == 'y':
            cur.execute(f'CREATE DATABASE "{CATALOG_DB}" ENCODING \'UTF8\'')
            print(f"  [OK] Database '{CATALOG_DB}' created")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        return False


def create_schema():
    """Create tables and views in the catalog database."""
    print("\n[Step 2/3] Creating schema...")
    try:
        conn = psycopg.connect(**DB_CONFIG, dbname=CATALOG_DB)
        conn.autocommit = True
        cur = conn.cursor()

        # Execute schema
        cur.execute(SCHEMA_SQL)
        print("  [OK] Schema created successfully")

        # List created tables
        cur.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_type, table_name
        """)

        tables = []
        views = []
        for name, ttype in cur.fetchall():
            if ttype == 'BASE TABLE':
                tables.append(name)
            elif ttype == 'VIEW':
                views.append(name)

        print(f"\n  [STAT] Created {len(tables)} tables:")
        for t in tables:
            print(f"     • {t}")

        print(f"\n  [VIEW]  Created {len(views)} views:")
        for v in views:
            print(f"     • {v}")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_schema():
    """Verify the schema was created correctly."""
    print("\n[Step 3/3] Verifying schema...")
    try:
        conn = psycopg.connect(**DB_CONFIG, dbname=CATALOG_DB)
        cur = conn.cursor()

        # Check table counts
        tables = ['SPB_MENSAGEM', 'SPB_DICIONARIO', 'SPB_MSGFIELD',
                  'SPB_XMLXSL', 'SPB_DOMINIOS', 'SPB_ISPB']

        print("\n  [LIST] Table status:")
        for table in tables:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cur.fetchone()[0]
            print(f"     {table:<20} {count:>6} rows")

        # Check views
        views = ['spb_mensagem_view', 'spb_dicionario_view', 'spb_msgfield_view']
        print("\n  [VIEW]  View status:")
        for view in views:
            cur.execute(f'SELECT COUNT(*) FROM {view}')
            count = cur.fetchone()[0]
            print(f"     {view:<25} {count:>6} rows")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        return False


def print_next_steps():
    """Print instructions for next steps."""
    print("\n" + "=" * 70)
    print("[OK] UNIFIED CATALOG DATABASE CREATED SUCCESSFULLY!")
    print("=" * 70)
    print("\n📝 Next Steps:")
    print("\n1. Populate catalog with data:")
    print(f"   python migrate_to_unified_catalog.py")
    print("\n2. Update project configurations:")
    print("   • Carga_Mensageria: Update config.py to use 'spb_catalog'")
    print("   • BCSrvSqlMq: Update connection to spb_catalog")
    print("   • SPBSite: Update catalog_database_url to spb_catalog")
    print("\n3. Connection URLs:")
    print(f"   postgresql://user:pass@{DB_CONFIG['host']}:{DB_CONFIG['port']}/spb_catalog")
    print("\n4. Test connections from all projects")
    print("=" * 70)


def main():
    """Main setup function."""
    if not DB_CONFIG['password']:
        password = input("Enter PostgreSQL password: ").strip()
        if not password:
            print("[ERROR] Password required")
            sys.exit(1)
        DB_CONFIG['password'] = password

    # Create database
    if not create_catalog_database():
        print("\n[ERROR] Failed to create database")
        sys.exit(1)

    # Create schema
    if not create_schema():
        print("\n[ERROR] Failed to create schema")
        sys.exit(1)

    # Verify
    if not verify_schema():
        print("\n[ERROR] Failed to verify schema")
        sys.exit(1)

    # Print next steps
    print_next_steps()


if __name__ == '__main__':
    main()
