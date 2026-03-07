# bacen_sup.py - Bacen Support task (port of BacenSup.cpp/h)
#
# CBacenSup: Reads from QLBacenCidadeSup queue, stores support
# messages directly into BacenApp and STRLog tables.
# Simplest Bacen task - no crypto, no XML parsing.

import time
from datetime import datetime

import pymqi
import pymqi.CMQC

from bcsrvsqlmq.thread_mq import CThreadMQ, THREAD_EVENT_STOP, connect_qmgr
from bcsrvsqlmq.msg_sgr import SECHDR_SIZE
from bcsrvsqlmq.db.bc_database import CBCDatabase
from bcsrvsqlmq.db.bacen_app_rs import CBacenAppRS
from bcsrvsqlmq.db.str_log_rs import CSTRLogRS


class CBacenSup(CThreadMQ):
    """Bacen Support task - reads and stores support messages.

    MQ Queue: QLBacenCidadeSup (local input, exclusive)
    DB Tables: BacenCidadeApp, STRLog (2 DBs)
    No cryptography. No XML parsing.
    """

    def __init__(self, name: str = '', automatic_thread: bool = True,
                 handle_mq: int = 0, main_srv=None):
        super().__init__(name, automatic_thread, handle_mq, main_srv)

        # Database connections and recordsets (2 DBs only)
        self.m_pDb1 = None   # BacenApp DB
        self.m_pDb2 = None   # STRLog DB
        self.m_pRS = None    # CBacenAppRS
        self.m_pRSLog = None  # CSTRLogRS

        # MQ connection state
        self.m_qmgr = None
        self.m_queue = None
        self.m_QMName = ''
        self.m_OpenCode = pymqi.CMQC.MQCC_OK
        self.m_CReason = pymqi.CMQC.MQRC_NONE
        self.m_CompCode = pymqi.CMQC.MQCC_OK
        self.m_Reason = pymqi.CMQC.MQRC_NONE

        # Message buffer
        self.m_buffermsg = None
        self.m_buflen = 0
        self.m_messlen = 0
        self.m_md = None
        self.m_t = None

    # ------------------------------------------------------------------
    # Thread lifecycle
    # ------------------------------------------------------------------
    def run_thread(self, main_srv=None):
        if main_srv is not None:
            self.pMainSrv = main_srv

        self.run_init()

        if not self.run_init_db_mq():
            self.run_wait_post()

        self.run_term_db_mq()
        self.run_term()

    # ------------------------------------------------------------------
    # RunInitDBeMQ
    # ------------------------------------------------------------------
    def run_init_db_mq(self) -> bool:
        """Initialize 2 DB connections, 2 recordsets, and open MQ queue.

        Returns True on error (matches C++ convention).
        """
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog

        self.m_pDb1 = None
        self.m_pDb2 = None
        self.m_pRS = None
        self.m_pRSLog = None

        self.m_buffermsg = bytearray(init_srv.m_MaxLenMsg)
        self.m_szQueueName = init_srv.m_MqQlBacenCidadeSup
        self.m_QMName = init_srv.m_QueueMgr

        # ---- Connect to queue manager ----
        try:
            self.m_qmgr = connect_qmgr(self.m_QMName, init_srv.m_MQChannel, init_srv.m_MQConnInfo)
            self.m_CReason = pymqi.CMQC.MQRC_NONE
        except pymqi.MQMIError as e:
            write_log(self.m_szTaskName, 8018, False, str(e.reason))
            self.m_CReason = e.reason
            return True

        # ---- Open queue ----
        open_options = pymqi.CMQC.MQOO_INPUT_EXCLUSIVE | pymqi.CMQC.MQOO_FAIL_IF_QUIESCING
        try:
            self.m_queue = pymqi.Queue(self.m_qmgr, self.m_szQueueName, open_options)
            self.m_OpenCode = pymqi.CMQC.MQCC_OK
        except pymqi.MQMIError as e:
            if e.reason != pymqi.CMQC.MQRC_NONE:
                write_log(self.m_szTaskName, 8019, False, str(e.reason))
            self.m_OpenCode = pymqi.CMQC.MQCC_FAILED
            return True

        # ---- Create DB connections (2) ----
        db_params = dict(
            db_name=init_srv.m_DBName,
            mq_server=init_srv.m_MQServer,
            porta=init_srv.m_MonitorPort,
            max_len_msg=init_srv.m_MaxLenMsg,
        )
        if hasattr(init_srv, 'm_DBServer'):
            db_params['db_server'] = init_srv.m_DBServer
        if hasattr(init_srv, 'm_DBPort'):
            db_params['db_port'] = init_srv.m_DBPort
        if hasattr(init_srv, 'm_DBUser'):
            db_params['db_user'] = init_srv.m_DBUser
        if hasattr(init_srv, 'm_DBPassword'):
            db_params['db_password'] = init_srv.m_DBPassword

        self.m_pDb1 = CBCDatabase(**db_params)
        self.m_pDb1.set_transactions()
        self.m_pDb2 = CBCDatabase(**db_params)
        self.m_pDb2.set_transactions()

        self.m_pRS = CBacenAppRS(self.m_pDb1, init_srv.m_DbTbBacenCidadeApp)
        self.m_pRSLog = CSTRLogRS(self.m_pDb2, init_srv.m_DbTbStrLog)

        # ---- Open DB1 and BacenApp recordset ----
        if not self._open_db_and_rs(self.m_pDb1, self.m_pRS, index=2):
            return True

        # ---- Open DB2 and STRLog recordset ----
        if not self._open_db_and_rs(self.m_pDb2, self.m_pRSLog):
            return True

        return False

    def _open_db_and_rs(self, db, rs, index=None) -> bool:
        """Open a database and its recordset. Returns True on success, False on error.

        Handles table-not-found (S0002/42P01) by creating the table and retrying.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        try:
            if not db.open():
                return False
            if index is not None:
                rs.m_index = index
            rs.open()
            return True
        except Exception as ex:
            err_str = str(ex)
            # Table does not exist - try to create it (matches C++ S0002 handling)
            if 'does not exist' in err_str or '42P01' in err_str:
                try:
                    db.rollback()
                    time.sleep(30)  # matches C++ Sleep(30000)
                    rs.create_table()
                    if index is not None:
                        rs.m_index = index
                    rs.open()
                    return True
                except Exception as ex2:
                    write_log(self.m_szTaskName, 8071, False, str(ex2))
                    return False
            else:
                write_log(self.m_szTaskName, 8071, False, err_str)
                return False

    # ------------------------------------------------------------------
    # RunTermDBeMQ
    # ------------------------------------------------------------------
    def run_term_db_mq(self) -> bool:
        """Close MQ queue and disconnect, close recordsets and DBs.

        Returns True on error.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        rt = False

        # ---- Close queue ----
        if self.m_queue is not None:
            try:
                self.m_queue.close()
            except pymqi.MQMIError as e:
                if e.reason != pymqi.CMQC.MQRC_NONE:
                    write_log(self.m_szTaskName, 8021, False, str(e.reason))

        # ---- Disconnect from queue manager ----
        if self.m_qmgr is not None and self.m_CReason != pymqi.CMQC.MQRC_ALREADY_CONNECTED:
            try:
                self.m_qmgr.disconnect()
            except pymqi.MQMIError as e:
                if e.reason != pymqi.CMQC.MQRC_NONE:
                    write_log(self.m_szTaskName, 8022, False, str(e.reason))

        # ---- Close recordsets and DBs ----
        try:
            for obj in [self.m_pRS, self.m_pRSLog]:
                if obj is not None:
                    obj.close()
            for obj in [self.m_pDb1, self.m_pDb2]:
                if obj is not None:
                    obj.close()
        except Exception as ex:
            write_log(self.m_szTaskName, 8071, False, str(ex))
            rt = True

        # ---- Cleanup references ----
        self.m_buffermsg = None
        self.m_pRS = None
        self.m_pRSLog = None
        self.m_pDb1 = None
        self.m_pDb2 = None
        self.m_queue = None
        self.m_qmgr = None

        return rt

    # ------------------------------------------------------------------
    # ProcessaQueue - Main MQGET loop for support messages
    # ------------------------------------------------------------------
    def processa_queue(self):
        """MQGET loop for support messages. Direct storage, no crypto/XML."""
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog
        erro = False

        while not erro:
            erro = False
            self.m_buflen = init_srv.m_MaxLenMsg - 1

            md = pymqi.MD()
            gmo = pymqi.GMO()
            gmo.Options = pymqi.CMQC.MQGMO_WAIT | pymqi.CMQC.MQGMO_SYNCPOINT
            gmo.Version = pymqi.CMQC.MQGMO_VERSION_2
            gmo.MatchOptions = pymqi.CMQC.MQMO_NONE
            gmo.WaitInterval = 5000  # 5 second wait

            # ---- MQGET ----
            try:
                message = self.m_queue.get(self.m_buflen, md, gmo)
                self.m_md = md
                self.m_messlen = len(message)
                self.m_buffermsg = bytearray(message)
                self.m_buflen = self.m_messlen
            except pymqi.MQMIError as e:
                if e.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
                    return
                write_log(self.m_szTaskName, 8023, False,
                          str(e.reason), str(e.comp))
                if e.reason == pymqi.CMQC.MQRC_TRUNCATED_MSG_FAILED:
                    erro = True
                continue

            write_log(self.m_szTaskName, 8024, True,
                      init_srv.m_QueueMgr,
                      init_srv.m_MqQlBacenCidadeSup,
                      str(self.m_messlen))
            self.dump_header(self._md_to_dict(md))
            if hasattr(init_srv, 'm_WriteReg'):
                init_srv.m_WriteReg(self.m_szTaskName, True,
                                    self.m_messlen, bytes(self.m_buffermsg))

            self.m_t = datetime.utcnow()

            # ---- UpdateDB (BacenApp + STRLog) ----
            if not erro:
                erro = self.update_db()

            # ---- Audit log ----
            if not erro:
                if hasattr(self.pMainSrv, 'monta_audit'):
                    self.pMainSrv.monta_audit(self.m_t, self.m_md,
                                              self.m_buflen, self.m_buffermsg)

            # ---- Commit or Backout ----
            if erro:
                self.m_event_stop.set()
                self._rollback_all()
                try:
                    self.m_qmgr.backout()
                    write_log(self.m_szTaskName, 8025, True)
                except pymqi.MQMIError as e:
                    write_log(self.m_szTaskName, 8027, False,
                              str(e.reason), str(e.comp))
            else:
                self._commit_all()
                try:
                    self.m_qmgr.commit()
                    write_log(self.m_szTaskName, 8026, True)
                except pymqi.MQMIError as e:
                    write_log(self.m_szTaskName, 8028, False,
                              str(e.reason), str(e.comp))

    def _rollback_all(self):
        """Rollback both DB transactions."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        for db_name, db in [('BacenApp', self.m_pDb1), ('STRLog', self.m_pDb2)]:
            try:
                if db is not None:
                    db.rollback()
            except Exception as ex:
                write_log(self.m_szTaskName, 8029, False, f'{db_name}: {ex}')

    def _commit_all(self):
        """Commit both DB transactions."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        for db_name, db in [('BacenApp', self.m_pDb1), ('STRLog', self.m_pDb2)]:
            try:
                if db is not None:
                    db.commit_trans()
            except Exception as ex:
                write_log(self.m_szTaskName, 8029, False, f'{db_name}: {ex}')

    # ------------------------------------------------------------------
    # UpdateDB - Insert into both BacenApp and STRLog
    # ------------------------------------------------------------------
    def update_db(self) -> bool:
        """Insert support message into BacenApp and STRLog tables.

        Returns True on error.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        # ---- BacenApp insert ----
        try:
            self.m_pDb1.begin_trans()
            self.m_pRS.add_new()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRS.m_sTblName}: {ex}')
            return True

        self.monta_db_reg_app()

        try:
            self.m_pRS.update()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRS.m_sTblName}: {ex}')
            return True

        # ---- STRLog insert ----
        try:
            self.m_pDb2.begin_trans()
            self.m_pRSLog.add_new()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSLog.m_sTblName}: {ex}')
            return True

        self.monta_db_reg_log()

        try:
            self.m_pRSLog.update()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSLog.m_sTblName}: {ex}')
            return True

        return False

    # ------------------------------------------------------------------
    # MontaDbRegApp - Populate BacenAppRS fields for support message
    # ------------------------------------------------------------------
    def monta_db_reg_app(self) -> bool:
        """Fill BacenAppRS fields for a support message."""
        md = self.m_md

        # MQ Message ID
        self.m_pRS.m_MQ_MSG_ID = md.MsgId if hasattr(md, 'MsgId') else md['MsgId']

        # MQ Correlation ID
        self.m_pRS.m_MQ_CORREL_ID = md.CorrelId if hasattr(md, 'CorrelId') else md['CorrelId']

        # DB_DATETIME - current timestamp
        self.m_pRS.m_DB_DATETIME = self.m_t

        # Status: N = Normal
        self.m_pRS.m_STATUS_MSG = 'N'

        # Flag de processamento: N = no insert
        self.m_pRS.m_FLAG_PROC = 'N'

        # Fila de origem MQ
        self.m_pRS.m_MQ_QN_ORIGEM = self.pMainSrv.pInitSrv.m_MqQlBacenCidadeSup

        # Data e Hora do Put do MQ
        self.m_pRS.m_MQ_DATETIME = self._parse_mq_datetime(md)

        # MQ Header (MQMD serialized to binary, 512 bytes)
        self.m_pRS.m_MQ_HEADER = self._serialize_md(md)

        # Security header - use MQMD bytes (matches C++ which copies md into both)
        self.m_pRS.m_SECURITY_HEADER = self._serialize_md(md)[:SECHDR_SIZE].ljust(SECHDR_SIZE, b'\x00')

        # NU_OPE not used for support messages
        self.m_pRS.m_NU_OPE = ''

        # COD_MSG = "SUPORTE"
        self.m_pRS.m_COD_MSG = 'SUPORTE'

        # MSG = raw message buffer
        self.m_pRS.m_MSG = bytes(self.m_buffermsg[:self.m_buflen])

        return False

    # ------------------------------------------------------------------
    # MontaDbRegLog - Populate STRLogRS fields for support message
    # ------------------------------------------------------------------
    def monta_db_reg_log(self) -> bool:
        """Fill STRLogRS fields for a support message."""
        md = self.m_md

        # MQ Message ID
        self.m_pRSLog.m_MQ_MSG_ID = md.MsgId if hasattr(md, 'MsgId') else md['MsgId']

        # MQ Correlation ID
        self.m_pRSLog.m_MQ_CORREL_ID = md.CorrelId if hasattr(md, 'CorrelId') else md['CorrelId']

        # DB_DATETIME - current timestamp
        self.m_pRSLog.m_DB_DATETIME = self.m_t

        # Status: N = Normal
        self.m_pRSLog.m_STATUS_MSG = 'N'

        # Fila de origem MQ
        self.m_pRSLog.m_MQ_QN_ORIGEM = self.pMainSrv.pInitSrv.m_MqQlBacenCidadeSup

        # Data e Hora do Put do MQ
        self.m_pRSLog.m_MQ_DATETIME = self._parse_mq_datetime(md)

        # MQ Header (MQMD serialized to binary, 512 bytes)
        self.m_pRSLog.m_MQ_HEADER = self._serialize_md(md)

        # Security header - zeros (matches C++ which fills with 0x00)
        self.m_pRSLog.m_SECURITY_HEADER = b'\x00' * SECHDR_SIZE

        # MSG = raw message buffer
        self.m_pRSLog.m_MSG = bytes(self.m_buffermsg[:self.m_buflen])

        return False

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_mq_datetime(md) -> datetime:
        """Parse PutDate + PutTime from MQMD into a datetime object."""
        try:
            put_date = md.PutDate if hasattr(md, 'PutDate') else md['PutDate']
            put_time = md.PutTime if hasattr(md, 'PutTime') else md['PutTime']
            if isinstance(put_date, bytes):
                put_date = put_date.decode('ascii').strip()
            if isinstance(put_time, bytes):
                put_time = put_time.decode('ascii').strip()
            date_str = str(put_date) + str(put_time)
            year = int(date_str[0:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            hour = int(date_str[8:10])
            minute = int(date_str[10:12])
            second = int(date_str[12:14])
            frac = int(date_str[14:16]) * 10000 if len(date_str) > 14 else 0
            return datetime(year, month, day, hour, minute, second, frac)
        except Exception:
            return datetime.utcnow()

    @staticmethod
    def _serialize_md(md) -> bytes:
        """Serialize MQMD to bytes (512 bytes, zero-padded)."""
        try:
            return md.pack()
        except Exception:
            parts = []
            for attr in ('MsgId', 'CorrelId', 'PutDate', 'PutTime'):
                val = getattr(md, attr, None)
                if val is None:
                    val = md.get(attr, b'')
                if isinstance(val, str):
                    val = val.encode('ascii')
                parts.append(val)
            return b''.join(parts).ljust(512, b'\x00')[:512]

    @staticmethod
    def _md_to_dict(md) -> dict:
        """Convert MQMD to dictionary for dump_header."""
        result = {}
        for attr in ('StrucId', 'Version', 'Report', 'MsgType', 'Expiry',
                      'Feedback', 'Encoding', 'CodedCharSetId', 'Format',
                      'Priority', 'Persistence', 'MsgId', 'CorrelId',
                      'BackoutCount', 'ReplyToQ', 'ReplyToQMgr',
                      'UserIdentifier', 'AccountingToken', 'ApplIdentityData',
                      'PutApplType', 'PutApplName', 'PutDate', 'PutTime',
                      'ApplOriginData', 'GroupId', 'MsgSeqNumber', 'Offset',
                      'MsgFlags', 'OriginalLength'):
            try:
                val = getattr(md, attr, None)
                if val is None:
                    val = md.get(attr, None)
                if val is not None:
                    result[attr] = val
            except Exception:
                pass
        return result
