# test_database.py - Integration tests for database layer
# These tests require a running PostgreSQL instance.
# Skip with: pytest -m "not integration"

import pytest

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

pytestmark = pytest.mark.skipif(not HAS_PSYCOPG2, reason='psycopg2 not installed')


# Database connection parameters - operational database
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'BCSPB',
    'user': 'postgres',
    'password': 'Rama1248',
}


def db_available():
    """Check if test database is accessible."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        return True
    except Exception:
        return False


@pytest.fixture
def db_conn():
    """Provide a database connection that rolls back after each test."""
    if not db_available():
        pytest.skip('PostgreSQL not available')
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


@pytest.mark.integration
class TestCBCDatabase:
    """Integration tests for CBCDatabase wrapper."""

    def test_import(self):
        from bcsrvsqlmq.db.bc_database import CBCDatabase

    def test_open_close(self):
        if not db_available():
            pytest.skip('PostgreSQL not available')
        from bcsrvsqlmq.db.bc_database import CBCDatabase
        db = CBCDatabase()
        result = db.open(
            DB_CONFIG['host'], DB_CONFIG['port'],
            DB_CONFIG['dbname'], DB_CONFIG['user'], DB_CONFIG['password'],
        )
        assert result is True
        db.close()

    def test_open_bad_host(self):
        from bcsrvsqlmq.db.bc_database import CBCDatabase
        db = CBCDatabase(db_server='badhost', db_port=9999,
                         db_name='nodb', db_user='nouser', db_password='nopass')
        result = db.open()
        assert result is False


@pytest.mark.integration
class TestRecordsets:
    """Integration tests for recordset classes (require tables to exist)."""

    def test_bacen_app_rs_import(self):
        from bcsrvsqlmq.db.bacen_app_rs import CBacenAppRS

    def test_if_app_rs_import(self):
        from bcsrvsqlmq.db.if_app_rs import CIFAppRS

    def test_str_log_rs_import(self):
        from bcsrvsqlmq.db.str_log_rs import CSTRLogRS

    def test_controle_rs_import(self):
        from bcsrvsqlmq.db.controle_rs import CControleRS

    def test_controle_lock_unlock(self, db_conn):
        """Test control table lock/unlock if spb_controle exists."""
        from bcsrvsqlmq.db.controle_rs import CControleRS
        try:
            cur = db_conn.cursor()
            cur.execute("SELECT 1 FROM spb_controle LIMIT 1")
            cur.close()
        except Exception:
            pytest.skip('spb_controle table not found')

        rs = CControleRS(db_conn)
        # Just verify the methods exist and don't crash
        assert hasattr(rs, 'lock')
        assert hasattr(rs, 'unlock')
