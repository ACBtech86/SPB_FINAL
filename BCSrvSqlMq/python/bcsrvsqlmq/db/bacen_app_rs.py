# bacen_app_rs.py - Bacen application recordset (port of BacenAppRS.cpp/h)

from datetime import datetime
from bcsrvsqlmq.db.bc_database import CBCDatabase


class CBacenAppRS:
    """Recordset for Bacen application messages (replaces MFC CRecordset)."""

    COLUMNS = [
        'mq_msg_id', 'mq_correl_id', 'db_datetime', 'status_msg',
        'flag_proc', 'mq_qn_origem', 'mq_datetime', 'mq_header',
        'security_header', 'nu_ope', 'cod_msg', 'msg',
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
        self.m_FLAG_PROC = ''
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
        self.m_index = 0

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
            flag_proc       CHAR(1)              NOT NULL,
            mq_qn_origem    VARCHAR(48)          NOT NULL,
            mq_datetime     TIMESTAMP            NOT NULL,
            mq_header       BYTEA               NOT NULL,
            security_header BYTEA               NOT NULL,
            nu_ope          VARCHAR(23)              NULL,
            cod_msg         VARCHAR(9)               NULL,
            msg             TEXT                     NULL
        )'''
        self.m_sPriKey = f'''ALTER TABLE {tbl} ADD
            CONSTRAINT pk_{tbl} PRIMARY KEY (db_datetime, mq_msg_id)'''
        self.m_sIndex1 = f'CREATE INDEX ix1_{tbl} ON {tbl} (nu_ope)'
        self.m_sIndex2 = f'CREATE INDEX ix2_{tbl} ON {tbl} (flag_proc, mq_qn_origem)'

    def open(self, filter_str: str = '', sort_str: str = ''):
        sql = f'SELECT {", ".join(self.COLUMNS)} FROM {self.m_sTblName}'
        params = []

        if self.m_index == 1 and self.m_ParamMQ_MSG_ID:
            sql += ' WHERE mq_msg_id = %s'
            params.append(psycopg2.Binary(self.m_ParamMQ_MSG_ID))
        elif self.m_index == 2 and self.m_ParamNU_OPE:
            sql += ' WHERE nu_ope = %s'
            params.append(self.m_ParamNU_OPE)
        elif filter_str:
            sql += f' WHERE {filter_str}'

        if sort_str:
            sql += f' ORDER BY {sort_str}'

        import psycopg2
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
         self.m_STATUS_MSG, self.m_FLAG_PROC, self.m_MQ_QN_ORIGEM,
         self.m_MQ_DATETIME, self.m_MQ_HEADER, self.m_SECURITY_HEADER,
         self.m_NU_OPE, self.m_COD_MSG, self.m_MSG) = row
        # Convert memoryview to bytes
        if isinstance(self.m_MQ_MSG_ID, memoryview):
            self.m_MQ_MSG_ID = bytes(self.m_MQ_MSG_ID)
        if isinstance(self.m_MQ_CORREL_ID, memoryview):
            self.m_MQ_CORREL_ID = bytes(self.m_MQ_CORREL_ID)
        if isinstance(self.m_MQ_HEADER, memoryview):
            self.m_MQ_HEADER = bytes(self.m_MQ_HEADER)
        if isinstance(self.m_SECURITY_HEADER, memoryview):
            self.m_SECURITY_HEADER = bytes(self.m_SECURITY_HEADER)
        # Handle None values
        self.m_STATUS_MSG = (self.m_STATUS_MSG or '').strip()
        self.m_FLAG_PROC = (self.m_FLAG_PROC or '').strip()
        self.m_MQ_QN_ORIGEM = self.m_MQ_QN_ORIGEM or ''
        self.m_NU_OPE = self.m_NU_OPE or ''
        self.m_COD_MSG = self.m_COD_MSG or ''
        self.m_MSG = self.m_MSG or ''

    def move_next(self):
        self._fetch_current()

    def is_eof(self) -> bool:
        return self._eof

    def add_new(self):
        """Prepare for insert (clear fields)."""
        self.m_MQ_MSG_ID = b''
        self.m_MQ_CORREL_ID = b''
        self.m_DB_DATETIME = datetime.now()
        self.m_STATUS_MSG = ''
        self.m_FLAG_PROC = ''
        self.m_MQ_QN_ORIGEM = ''
        self.m_MQ_DATETIME = datetime.now()
        self.m_MQ_HEADER = b''
        self.m_SECURITY_HEADER = b''
        self.m_NU_OPE = ''
        self.m_COD_MSG = ''
        self.m_MSG = ''

    def update(self):
        """Insert the current record into the database."""
        import psycopg2
        sql = f'''INSERT INTO {self.m_sTblName}
            ({", ".join(self.COLUMNS)})
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        cursor = self.m_pDatabase.connection.cursor()
        try:
            cursor.execute(sql, (
                psycopg2.Binary(self.m_MQ_MSG_ID),
                psycopg2.Binary(self.m_MQ_CORREL_ID),
                self.m_DB_DATETIME,
                self.m_STATUS_MSG,
                self.m_FLAG_PROC,
                self.m_MQ_QN_ORIGEM,
                self.m_MQ_DATETIME,
                psycopg2.Binary(self.m_MQ_HEADER),
                psycopg2.Binary(self.m_SECURITY_HEADER),
                self.m_NU_OPE or None,
                self.m_COD_MSG or None,
                self.m_MSG or None,
            ))
        finally:
            cursor.close()

    def edit(self):
        """Prepare for update (no-op, fields are already loaded)."""
        pass

    def update_existing(self, where_clause: str, params: list):
        """Update existing records matching where clause."""
        set_parts = []
        values = []
        for col in self.COLUMNS:
            val = getattr(self, f'm_{col.upper()}', None)
            set_parts.append(f'{col} = %s')
            if isinstance(val, (bytes, bytearray)):
                import psycopg2
                values.append(psycopg2.Binary(val))
            else:
                values.append(val)
        values.extend(params)

        sql = f'UPDATE {self.m_sTblName} SET {", ".join(set_parts)} WHERE {where_clause}'
        cursor = self.m_pDatabase.connection.cursor()
        try:
            cursor.execute(sql, values)
        finally:
            cursor.close()

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
            cursor.execute(self.m_sIndex2)
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
