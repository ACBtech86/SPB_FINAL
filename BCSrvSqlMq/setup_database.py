#!/usr/bin/env python3
"""
Complete database setup for BCSrvSqlMq on Ubuntu
Creates database and all required tables
"""
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'Rama1248',
}
DB_NAME = 'bcspbstr'

def create_database():
    """Create the database if it doesn't exist."""
    print("=" * 70)
    print("Step 1: Creating Database")
    print("=" * 70)

    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cur.fetchone()

        if exists:
            print(f"✅ Database '{DB_NAME}' already exists")
        else:
            # Create database
            cur.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(DB_NAME)
            ))
            print(f"✅ Database '{DB_NAME}' created successfully")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def create_tables():
    """Create all required tables."""
    print("\n" + "=" * 70)
    print("Step 2: Creating Tables")
    print("=" * 70)

    try:
        # Connect to the database
        conn = psycopg2.connect(**DB_CONFIG, database=DB_NAME)
        conn.autocommit = True
        cur = conn.cursor()

        # 1. SPB_LOG_BACEN table
        print("\n[1/7] Creating SPB_LOG_BACEN table...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS SPB_LOG_BACEN (
                mq_msg_id       BYTEA               NOT NULL,
                mq_correl_id    BYTEA               NOT NULL,
                db_datetime     TIMESTAMP            NOT NULL,
                status_msg      CHAR(1)              NOT NULL,
                mq_qn_origem    VARCHAR(48)          NOT NULL,
                mq_datetime     TIMESTAMP            NOT NULL,
                mq_header       BYTEA               NOT NULL,
                security_header BYTEA                    NULL,
                nu_ope          VARCHAR(23)              NULL,
                cod_msg         VARCHAR(9)               NULL,
                msg             TEXT                     NULL,
                CONSTRAINT pk_SPB_LOG_BACEN PRIMARY KEY (db_datetime, mq_msg_id)
            )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS ix1_SPB_LOG_BACEN ON SPB_LOG_BACEN (nu_ope)')
        print("✅ SPB_LOG_BACEN created")

        # 2. SPB_BACEN_TO_LOCAL table
        print("\n[2/7] Creating SPB_BACEN_TO_LOCAL table...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS SPB_BACEN_TO_LOCAL (
                mq_msg_id       BYTEA               NOT NULL,
                mq_correl_id    BYTEA               NOT NULL,
                db_datetime     TIMESTAMP            NOT NULL,
                status_msg      CHAR(1)              NOT NULL,
                flag_proc       CHAR(1)              NOT NULL,
                mq_qn_origem    VARCHAR(48)          NOT NULL,
                mq_datetime     TIMESTAMP            NOT NULL,
                mq_header       BYTEA               NOT NULL,
                security_header BYTEA               NOT NULL,
                nu_ope          VARCHAR(23)              NULL,
                cod_msg         VARCHAR(9)               NULL,
                msg             TEXT                     NULL,
                CONSTRAINT pk_SPB_BACEN_TO_LOCAL PRIMARY KEY (db_datetime, mq_msg_id)
            )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS ix1_SPB_BACEN_TO_LOCAL ON SPB_BACEN_TO_LOCAL (nu_ope)')
        cur.execute('CREATE INDEX IF NOT EXISTS ix2_SPB_BACEN_TO_LOCAL ON SPB_BACEN_TO_LOCAL (flag_proc, mq_qn_origem)')
        print("✅ SPB_BACEN_TO_LOCAL created")

        # 3. SPB_LOCAL_TO_BACEN table
        print("\n[3/7] Creating SPB_LOCAL_TO_BACEN table...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS SPB_LOCAL_TO_BACEN (
                mq_msg_id       BYTEA               NOT NULL,
                mq_correl_id    BYTEA               NOT NULL,
                db_datetime     TIMESTAMP            NOT NULL,
                status_msg      CHAR(1)              NOT NULL,
                flag_proc       CHAR(1)              NOT NULL,
                mq_qn_origem    VARCHAR(48)          NOT NULL,
                mq_datetime     TIMESTAMP            NOT NULL,
                mq_header       BYTEA               NOT NULL,
                security_header BYTEA               NOT NULL,
                nu_ope          VARCHAR(23)              NULL,
                cod_msg         VARCHAR(9)               NULL,
                msg             TEXT                     NULL,
                CONSTRAINT pk_SPB_LOCAL_TO_BACEN PRIMARY KEY (db_datetime, mq_msg_id)
            )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS ix1_SPB_LOCAL_TO_BACEN ON SPB_LOCAL_TO_BACEN (nu_ope)')
        cur.execute('CREATE INDEX IF NOT EXISTS ix2_SPB_LOCAL_TO_BACEN ON SPB_LOCAL_TO_BACEN (flag_proc, mq_qn_origem)')
        print("✅ SPB_LOCAL_TO_BACEN created")

        # 4. SPB_CONTROLE table
        print("\n[4/7] Creating SPB_CONTROLE table...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS SPB_CONTROLE (
                ispb            VARCHAR(8)           NOT NULL,
                nome_ispb       VARCHAR(15)          NOT NULL,
                msg_seq         SMALLINT                 NULL,
                status_geral    CHAR(1)              NOT NULL,
                dthr_eco        TIMESTAMP                NULL,
                ultmsg          VARCHAR(23)              NULL,
                dthr_ultmsg     TIMESTAMP                NULL,
                certificadora   VARCHAR(50)              NULL,
                CONSTRAINT pk_SPB_CONTROLE PRIMARY KEY (ispb)
            )
        ''')
        print("✅ SPB_CONTROLE created")

        # Insert default control record
        cur.execute("""
            INSERT INTO SPB_CONTROLE (ispb, nome_ispb, status_geral)
            VALUES ('36266751', 'FINVEST', 'A')
            ON CONFLICT (ispb) DO NOTHING
        """)
        print("✅ Default control record inserted")

        # 5. SPB_MENSAGEM table (catalog)
        print("\n[5/7] Creating SPB_MENSAGEM table...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS SPB_MENSAGEM (
                MSG_ID VARCHAR(50) PRIMARY KEY,
                MSG_DESCR VARCHAR(500)
            )
        ''')
        print("✅ SPB_MENSAGEM created")

        # 6. SPB_DICIONARIO table (catalog)
        print("\n[6/7] Creating SPB_DICIONARIO table...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS SPB_DICIONARIO (
                MSG_CPOTAG VARCHAR(100) PRIMARY KEY,
                MSG_CPOTIPO VARCHAR(50),
                MSG_CPOTAM VARCHAR(20),
                MSG_CPOFORM VARCHAR(50)
            )
        ''')
        print("✅ SPB_DICIONARIO created")

        # 7. SPB_MSGFIELD table (catalog)
        print("\n[7/7] Creating SPB_MSGFIELD table...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS SPB_MSGFIELD (
                COD_GRADE VARCHAR(50),
                MSG_ID VARCHAR(50),
                MSG_TAG VARCHAR(100),
                MSG_DESCR VARCHAR(500),
                MSG_EMISSOR VARCHAR(100),
                MSG_DESTINATARIO VARCHAR(100),
                MSG_SEQ INTEGER,
                MSG_CPOTAG VARCHAR(100),
                MSG_CPONOME VARCHAR(200),
                MSG_CPOOBRIG VARCHAR(10),
                PRIMARY KEY (COD_GRADE, MSG_ID, MSG_SEQ)
            )
        ''')
        print("✅ SPB_MSGFIELD created")

        # Create views for compatibility
        print("\n[+] Creating compatibility views...")
        cur.execute('DROP VIEW IF EXISTS spb_mensagem_view CASCADE')
        cur.execute('''
            CREATE VIEW spb_mensagem_view AS
            SELECT MSG_ID as msg_id, MSG_DESCR as msg_descr
            FROM SPB_MENSAGEM
        ''')

        cur.execute('DROP VIEW IF EXISTS spb_dicionario_view CASCADE')
        cur.execute('''
            CREATE VIEW spb_dicionario_view AS
            SELECT MSG_CPOTAG as msg_cpotag, MSG_CPOTIPO as msg_cpotipo,
                   MSG_CPOTAM as msg_cpotam, MSG_CPOFORM as msg_cpoform
            FROM SPB_DICIONARIO
        ''')

        cur.execute('DROP VIEW IF EXISTS spb_msgfield_view CASCADE')
        cur.execute('''
            CREATE VIEW spb_msgfield_view AS
            SELECT
                ROW_NUMBER() OVER (ORDER BY COD_GRADE, MSG_ID, MSG_SEQ) as id,
                COD_GRADE as cod_grade,
                MSG_ID as msg_id,
                MSG_TAG as msg_tag,
                MSG_DESCR as msg_descr,
                MSG_EMISSOR as msg_emissor,
                MSG_DESTINATARIO as msg_destinatario,
                MSG_SEQ as msg_seq,
                MSG_CPOTAG as msg_cpotag,
                MSG_CPONOME as msg_cponome,
                MSG_CPOOBRIG as msg_cpoobrig
            FROM SPB_MSGFIELD
        ''')
        print("✅ Compatibility views created")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_setup():
    """Verify database and tables exist."""
    print("\n" + "=" * 70)
    print("Step 3: Verifying Setup")
    print("=" * 70)

    try:
        conn = psycopg2.connect(**DB_CONFIG, database=DB_NAME)
        cur = conn.cursor()

        # Get list of tables
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        tables = [row[0] for row in cur.fetchall()]

        print("\n📋 Tables created:")
        for table in tables:
            print(f"  ✅ {table}")

        # Get record count from SPB_CONTROLE
        cur.execute("SELECT COUNT(*) FROM SPB_CONTROLE")
        count = cur.fetchone()[0]
        print(f"\n📊 SPB_CONTROLE records: {count}")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error verifying setup: {e}")
        return False

def main():
    """Main setup function."""
    print("\n" + "=" * 70)
    print("BCSrvSqlMq Database Setup for Ubuntu")
    print("=" * 70)
    print(f"Database: {DB_NAME}")
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"User: {DB_CONFIG['user']}")
    print("=" * 70)

    # Step 1: Create database
    if not create_database():
        print("\n❌ Failed to create database")
        sys.exit(1)

    # Step 2: Create tables
    if not create_tables():
        print("\n❌ Failed to create tables")
        sys.exit(1)

    # Step 3: Verify
    if not verify_setup():
        print("\n❌ Failed to verify setup")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("✅ Database setup completed successfully!")
    print("=" * 70)
    print("\nYou can now:")
    print("  1. Run the BCSrvSqlMq application")
    print("  2. Test database connection with verify_db_config.py")
    print("  3. Load catalog data (if available)")
    print("=" * 70)

if __name__ == '__main__':
    main()
