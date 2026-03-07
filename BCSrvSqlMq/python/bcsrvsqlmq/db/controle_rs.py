# controle_rs.py - Control table recordset (port of ControleRS.cpp/h)

import threading
from datetime import datetime
from bcsrvsqlmq.db.bc_database import CBCDatabase


class CControleRS:
    """Recordset for control/coordination table."""

    COLUMNS = [
        'ispb', 'nome_ispb', 'status_geral',
        'dthr_eco', 'ultmsg', 'dthr_ultmsg', 'certificadora',
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
        self.m_ISPB = ''
        self.m_NOME_ISPB = ''
        self.m_STATUS_GERAL = ''
        self.m_DTHR_ECO = None
        self.m_ULTMSG = ''
        self.m_DTHR_ULTMSG = None
        self.m_CERTIFICADORA = ''

        # Parameter data
        self.m_ParamISPB = ''

        # Lock state
        self.m_islock = False
        self._lock = threading.Lock()

        # Cursor state
        self._cursor = None
        self._current_row = None
        self._eof = True

        # DDL SQL
        tbl = self.m_sTblName
        self.m_sDrop = f'DROP TABLE {tbl}'
        self.m_sCreate = f'''CREATE TABLE {tbl} (
            ispb            VARCHAR(8)           NOT NULL,
            nome_ispb       VARCHAR(15)          NOT NULL,
            msg_seq         SMALLINT                 NULL,
            status_geral    CHAR(1)              NOT NULL,
            dthr_eco        TIMESTAMP                NULL,
            ultmsg          VARCHAR(23)              NULL,
            dthr_ultmsg     TIMESTAMP                NULL,
            certificadora   VARCHAR(50)              NULL
        )'''
        self.m_sPriKey = f'''ALTER TABLE {tbl} ADD
            CONSTRAINT pk_{tbl} PRIMARY KEY (ispb)'''

    def lock(self) -> bool:
        self._lock.acquire()
        self.m_islock = True
        return True

    def unlock(self) -> bool:
        self.m_islock = False
        self._lock.release()
        return True

    def is_locked(self) -> bool:
        return self.m_islock

    def open(self, filter_str: str = '', sort_str: str = ''):
        sql = f'SELECT {", ".join(self.COLUMNS)} FROM {self.m_sTblName}'
        params = []

        if self.m_ParamISPB:
            sql += ' WHERE ispb = %s'
            params.append(self.m_ParamISPB)
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
        (self.m_ISPB, self.m_NOME_ISPB, self.m_STATUS_GERAL,
         self.m_DTHR_ECO, self.m_ULTMSG, self.m_DTHR_ULTMSG,
         self.m_CERTIFICADORA) = row

        self.m_ISPB = (self.m_ISPB or '').strip()
        self.m_NOME_ISPB = (self.m_NOME_ISPB or '').strip()
        self.m_STATUS_GERAL = (self.m_STATUS_GERAL or '').strip()
        self.m_ULTMSG = self.m_ULTMSG or ''
        self.m_CERTIFICADORA = self.m_CERTIFICADORA or ''

    def move_next(self):
        self._fetch_current()

    def is_eof(self) -> bool:
        return self._eof

    def add_new(self):
        self.m_ISPB = ''
        self.m_NOME_ISPB = ''
        self.m_STATUS_GERAL = ''
        self.m_DTHR_ECO = None
        self.m_ULTMSG = ''
        self.m_DTHR_ULTMSG = None
        self.m_CERTIFICADORA = ''

    def update(self):
        sql = f'''INSERT INTO {self.m_sTblName}
            ({", ".join(self.COLUMNS)})
            VALUES (%s, %s, %s, %s, %s, %s, %s)'''
        cursor = self.m_pDatabase.connection.cursor()
        try:
            cursor.execute(sql, (
                self.m_ISPB,
                self.m_NOME_ISPB,
                self.m_STATUS_GERAL,
                self.m_DTHR_ECO,
                self.m_ULTMSG or None,
                self.m_DTHR_ULTMSG,
                self.m_CERTIFICADORA or None,
            ))
        finally:
            cursor.close()

    def edit(self):
        pass

    def update_existing(self, where_clause: str, params: list):
        set_parts = []
        values = []
        for col in self.COLUMNS:
            attr_name = f'm_{col.upper()}'
            val = getattr(self, attr_name, None)
            set_parts.append(f'{col} = %s')
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
