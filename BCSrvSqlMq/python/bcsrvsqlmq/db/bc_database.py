# bc_database.py - Database connection wrapper (port of CBCDb.h)

import psycopg2


class CBCDatabase:
    """PostgreSQL database connection wrapper (replaces MFC CDatabase via ODBC)."""

    def __init__(self, db_name: str = '', mq_server: str = '', porta: int = 0,
                 max_len_msg: int = 8000, db_server: str = 'localhost',
                 db_port: int = 5432, db_user: str = 'postgres',
                 db_password: str = ''):
        self.m_sDbName = db_name
        self.m_sMQServer = mq_server
        self.m_iPorta = porta
        self.m_iMaxLenMsg = max_len_msg

        self.db_server = db_server
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password

        self.connection = None
        self.m_bTransactions = False

    def open(self, connection_string: str = '') -> bool:
        try:
            self.connection = psycopg2.connect(
                host=self.db_server,
                port=self.db_port,
                dbname=self.m_sDbName,
                user=self.db_user,
                password=self.db_password,
            )
            self.connection.autocommit = not self.m_bTransactions
            return True
        except psycopg2.Error:
            return False

    def open_ex(self, connection_string: str, options: int = 0) -> bool:
        return self.open(connection_string)

    def close(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

    def is_open(self) -> bool:
        return self.connection is not None and not self.connection.closed

    def set_transactions(self):
        self.m_bTransactions = True
        if self.connection:
            self.connection.autocommit = False

    def begin_trans(self):
        pass  # psycopg2 auto-begins on first query when autocommit=False

    def commit_trans(self):
        if self.connection:
            self.connection.commit()

    def rollback(self):
        if self.connection:
            self.connection.rollback()

    def execute_sql(self, sql: str, params=None):
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, params)
            return cursor
        except Exception:
            cursor.close()
            raise

    @property
    def cursor(self):
        return self.connection.cursor()
