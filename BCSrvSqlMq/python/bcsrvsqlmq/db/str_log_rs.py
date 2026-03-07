# str_log_rs.py - STR Log recordset (port of STRLogRS.cpp/h)

from datetime import datetime
from bcsrvsqlmq.db.bc_database import CBCDatabase


class CSTRLogRS:
    """Recordset for STR sequential transaction log."""

    COLUMNS = [
        'mq_msg_id', 'mq_correl_id', 'db_datetime', 'status_msg',
        'mq_qn_origem', 'mq_datetime', 'mq_header', 'security_header',
        'nu_ope', 'cod_msg', 'msg',
    ]

    def __init__(self, database: CBCDatabase = None, table_name: str = ''):
        self.m_pDatabase = database
        self.m_sTblName = table_name

        if database:
            self.m_sDbName = database.m_sDbName
            self.m_sMQServer = database.m_sMQServer
            self.m_iPorta = database.m_iPorta
            self.m_iMaxLenMsg = database.m_iMaxLenMsg
        else:
            self.m_sDbName = ''
            self.m_sMQServer = ''
            self.m_iPorta = 0
            self.m_iMaxLenMsg = 8000

        # Field data
        self.m_MQ_MSG_ID = b''
        self.m_MQ_CORREL_ID = b''
        self.m_DB_DATETIME = None
        self.m_STATUS_MSG = ''
        self.m_MQ_QN_ORIGEM = ''
        self.m_MQ_DATETIME = None
        self.m_MQ_HEADER = b''
        self.m_SECURITY_HEADER = b''
        self.m_NU_OPE = ''
        self.m_COD_MSG = ''
        self.m_MSG = ''

        # Parameter data
        self.m_ParamMQ_MSG_ID = b''
        self.m_ParamNU_OPE = ''

        # Cursor state
        self._cursor = None
        self._current_row = None
        self._eof = True

        # DDL SQL
        tbl = self.m_sTblName
        self.m_sDrop = f'DROP TABLE {tbl}'
        self.m_sCreate = f'''CREATE TABLE {tbl} (
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
            msg             TEXT                     NULL
        )'''
        self.m_sPriKey = f'''ALTER TABLE {tbl} ADD
            CONSTRAINT pk_{tbl} PRIMARY KEY (db_datetime, mq_msg_id)'''
        self.m_sIndex1 = f'CREATE INDEX ix1_{tbl} ON {tbl} (nu_ope)'

    def open(self, filter_str: str = '', sort_str: str = ''):
        sql = f'SELECT {", ".join(self.COLUMNS)} FROM {self.m_sTblName}'
        params = []

        if self.m_ParamNU_OPE:
            sql += ' WHERE nu_ope = %s'
            params.append(self.m_ParamNU_OPE)
        elif filter_str:
            sql += f' WHERE {filter_str}'

        if sort_str:
            sql += f' ORDER BY {sort_str}'

        self._cursor = self.m_pDatabase.connection.cursor()
        self._cursor.execute(sql, params if params else None)
        self._fetch_current()

    def _fetch_current(self):
        row = self._cursor.fetchone() if self._cursor else None
        if row is None:
            self._eof = True
            self._current_row = None
        else:
            self._eof = False
            self._current_row = row
            self._map_fields(row)

    def _map_fields(self, row):
        (self.m_MQ_MSG_ID, self.m_MQ_CORREL_ID, self.m_DB_DATETIME,
         self.m_STATUS_MSG, self.m_MQ_QN_ORIGEM, self.m_MQ_DATETIME,
         self.m_MQ_HEADER, self.m_SECURITY_HEADER,
         self.m_NU_OPE, self.m_COD_MSG, self.m_MSG) = row

        for attr in ('m_MQ_MSG_ID', 'm_MQ_CORREL_ID', 'm_MQ_HEADER', 'm_SECURITY_HEADER'):
            val = getattr(self, attr)
            if isinstance(val, memoryview):
                setattr(self, attr, bytes(val))
            elif val is None:
                setattr(self, attr, b'')

        self.m_STATUS_MSG = (self.m_STATUS_MSG or '').strip()
        self.m_MQ_QN_ORIGEM = self.m_MQ_QN_ORIGEM or ''
        self.m_NU_OPE = self.m_NU_OPE or ''
        self.m_COD_MSG = self.m_COD_MSG or ''
        self.m_MSG = self.m_MSG or ''

    def move_next(self):
        self._fetch_current()

    def is_eof(self) -> bool:
        return self._eof

    def add_new(self):
        self.m_MQ_MSG_ID = b''
        self.m_MQ_CORREL_ID = b''
        self.m_DB_DATETIME = datetime.now()
        self.m_STATUS_MSG = ''
        self.m_MQ_QN_ORIGEM = ''
        self.m_MQ_DATETIME = datetime.now()
        self.m_MQ_HEADER = b''
        self.m_SECURITY_HEADER = b''
        self.m_NU_OPE = ''
        self.m_COD_MSG = ''
        self.m_MSG = ''

    def update(self):
        import psycopg2
        sql = f'''INSERT INTO {self.m_sTblName}
            ({", ".join(self.COLUMNS)})
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        cursor = self.m_pDatabase.connection.cursor()
        try:
            cursor.execute(sql, (
                psycopg2.Binary(self.m_MQ_MSG_ID),
                psycopg2.Binary(self.m_MQ_CORREL_ID),
                self.m_DB_DATETIME,
                self.m_STATUS_MSG,
                self.m_MQ_QN_ORIGEM,
                self.m_MQ_DATETIME,
                psycopg2.Binary(self.m_MQ_HEADER),
                psycopg2.Binary(self.m_SECURITY_HEADER) if self.m_SECURITY_HEADER else None,
                self.m_NU_OPE or None,
                self.m_COD_MSG or None,
                self.m_MSG or None,
            ))
        finally:
            cursor.close()

    def edit(self):
        pass

    def close(self):
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        self._eof = True
        self._current_row = None

    def create_table(self):
        cursor = self.m_pDatabase.connection.cursor()
        try:
            cursor.execute(self.m_sCreate)
            cursor.execute(self.m_sPriKey)
            cursor.execute(self.m_sIndex1)
            self.m_pDatabase.connection.commit()
        finally:
            cursor.close()

    def drop_table(self):
        cursor = self.m_pDatabase.connection.cursor()
        try:
            cursor.execute(self.m_sDrop)
            self.m_pDatabase.connection.commit()
        finally:
            cursor.close()
