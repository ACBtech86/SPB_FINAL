# bacen_rep.py - Bacen Report task (port of BacenRep.cpp/h)
#
# CBacenRep: Reads from QLBacenCidadeRep queue, processes report
# messages (COA, COD, general reports). Updates BacenApp, STRLog,
# and IFApp tables. Simpler than Req/Rsp - no crypto, no XML parsing.

import time
from datetime import datetime

import pymqi
import pymqi.CMQC

from bcsrvsqlmq.thread_mq import CThreadMQ, THREAD_EVENT_STOP, connect_qmgr
from bcsrvsqlmq.msg_sgr import SECHDR, SECHDR_SIZE
from bcsrvsqlmq.db.bc_database import CBCDatabase
from bcsrvsqlmq.db.bacen_app_rs import CBacenAppRS
from bcsrvsqlmq.db.str_log_rs import CSTRLogRS
from bcsrvsqlmq.db.if_app_rs import CIFAppRS


# MQ Feedback constants
MQFB_COA = 259   # Confirm On Arrival
MQFB_COD = 260   # Confirm On Delivery


class CBacenRep(CThreadMQ):
    """Bacen Report task - reads report messages (COA/COD/reports).

    MQ Queue: QLBacenCidadeRep (local input, exclusive)
    DB Tables: BacenCidadeApp, STRLog, CidadeBacenApp (3 DBs)
    """

    def __init__(self, name: str = '', automatic_thread: bool = True,
                 handle_mq: int = 0, main_srv=None):
        super().__init__(name, automatic_thread, handle_mq, main_srv)

        # Database connections and recordsets (3 DBs, no Controle)
        self.m_pDb1 = None   # BacenApp DB
        self.m_pDb2 = None   # STRLog DB
        self.m_pDb3 = None   # IFApp DB
        self.m_pRS = None    # CBacenAppRS
        self.m_pRSLog = None  # CSTRLogRS
        self.m_pRSApp = None  # CIFAppRS

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
        """Initialize 3 DB connections, 3 recordsets, and open MQ queue.

        Returns True on error.
        """
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog

        self.m_pDb1 = None
        self.m_pDb2 = None
        self.m_pDb3 = None
        self.m_pRS = None
        self.m_pRSLog = None
        self.m_pRSApp = None

        self.m_buffermsg = bytearray(init_srv.m_MaxLenMsg)
        self.m_szQueueName = init_srv.m_MqQlBacenCidadeRep
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

        # ---- Create DB connections (3) ----
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
        self.m_pDb3 = CBCDatabase(**db_params)
        self.m_pDb3.set_transactions()

        self.m_pRS = CBacenAppRS(self.m_pDb1, init_srv.m_DbTbBacenCidadeApp)
        self.m_pRSLog = CSTRLogRS(self.m_pDb2, init_srv.m_DbTbStrLog)
        self.m_pRSApp = CIFAppRS(self.m_pDb3, init_srv.m_DbTbCidadeBacenApp)

        # ---- Open DBs and recordsets ----
        for db, rs, kw in [
            (self.m_pDb1, self.m_pRS, dict(index=2)),
            (self.m_pDb2, self.m_pRSLog, {}),
            (self.m_pDb3, self.m_pRSApp, dict(index=1)),
        ]:
            if not self._open_db_and_rs(db, rs, **kw):
                return True

        return False

    def _open_db_and_rs(self, db, rs, index=None) -> bool:
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
            if 'does not exist' in err_str or '42P01' in err_str:
                try:
                    db.rollback()
                    rs.create_table()
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
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        rt = False

        if self.m_queue is not None:
            try:
                self.m_queue.close()
            except pymqi.MQMIError as e:
                if e.reason != pymqi.CMQC.MQRC_NONE:
                    write_log(self.m_szTaskName, 8021, False, str(e.reason))

        if self.m_qmgr is not None and self.m_CReason != pymqi.CMQC.MQRC_ALREADY_CONNECTED:
            try:
                self.m_qmgr.disconnect()
            except pymqi.MQMIError as e:
                if e.reason != pymqi.CMQC.MQRC_NONE:
                    write_log(self.m_szTaskName, 8022, False, str(e.reason))

        try:
            for obj in [self.m_pRS, self.m_pRSLog, self.m_pRSApp]:
                if obj is not None:
                    obj.close()
            for obj in [self.m_pDb1, self.m_pDb2, self.m_pDb3]:
                if obj is not None:
                    obj.close()
        except Exception as ex:
            write_log(self.m_szTaskName, 8071, False, str(ex))
            rt = True

        self.m_buffermsg = None
        self.m_pRS = None
        self.m_pRSLog = None
        self.m_pRSApp = None
        self.m_pDb1 = None
        self.m_pDb2 = None
        self.m_pDb3 = None
        self.m_queue = None
        self.m_qmgr = None

        return rt

    # ------------------------------------------------------------------
    # ProcessaQueue - Main MQGET loop for reports
    # ------------------------------------------------------------------
    def processa_queue(self):
        """MQGET loop for report messages. Handles COA, COD, and general reports."""
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
            gmo.WaitInterval = getattr(init_srv, 'm_QueueTimeout', 5) * 1000

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
                      init_srv.m_MqQlBacenCidadeRep,
                      str(self.m_messlen))

            self.m_t = datetime.utcnow()

            # ---- Process based on feedback type ----
            feedback = self._get_feedback(md)

            if feedback in (MQFB_COA, MQFB_COD):
                # COA/COD: update log + update IFApp (no BacenApp insert)
                if not erro:
                    erro = self.update_db_log()
                if not erro:
                    erro = self.update_db_app()
            else:
                # General report: insert BacenApp + update log + update IFApp
                if not erro:
                    erro = self.update_db()
                if not erro:
                    erro = self.update_db_log()
                if not erro:
                    erro = self.update_db_app()

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
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        for db_name, db in [('BacenApp', self.m_pDb1), ('STRLog', self.m_pDb2),
                            ('IFApp', self.m_pDb3)]:
            try:
                if db is not None:
                    db.rollback()
            except Exception as ex:
                write_log(self.m_szTaskName, 8029, False, f'{db_name}: {ex}')

    def _commit_all(self):
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        for db_name, db in [('BacenApp', self.m_pDb1), ('STRLog', self.m_pDb2),
                            ('IFApp', self.m_pDb3)]:
            try:
                if db is not None:
                    db.commit_trans()
            except Exception as ex:
                write_log(self.m_szTaskName, 8029, False, f'{db_name}: {ex}')

    # ------------------------------------------------------------------
    # UpdateDB - Insert report into BacenApp table
    # ------------------------------------------------------------------
    def update_db(self) -> bool:
        """Insert report into BacenApp table. Returns True on error."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

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

        return False

    # ------------------------------------------------------------------
    # UpdateDBLog - Insert report into STRLog table
    # ------------------------------------------------------------------
    def update_db_log(self) -> bool:
        """Insert report log entry into STRLog table. Returns True on error."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

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
    # UpdateDBApp - Update IFApp table with COA/COD/Report info
    # ------------------------------------------------------------------
    def update_db_app(self) -> bool:
        """Look up original message in IFApp by CorrelId, update status.

        For COA: set MQ_MSG_ID_COA + MQ_DATETIME_COA, status='N'
        For COD: set MQ_MSG_ID_COD + MQ_DATETIME_COD, status='N'
        For others: set MQ_MSG_ID_REP + MQ_DATETIME_REP, status='R'

        Returns True on error.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        md = self.m_md

        # Use CorrelId to look up original message
        correl_id = md.CorrelId if hasattr(md, 'CorrelId') else md['CorrelId']
        self.m_pRSApp.m_ParamMQ_MSG_ID = correl_id

        try:
            self.m_pDb3.begin_trans()
            self.m_pRSApp.m_index = 1
            self.m_pRSApp.close()
            self.m_pRSApp.open()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSApp.m_sTblName}: {ex}')
            return True

        if self.m_pRSApp.is_eof():
            # Original message not found
            self.m_pDb3.rollback()
            write_log(self.m_szTaskName, 8108, False)
            return False  # Not an error - just log and continue

        # Prepare update fields
        feedback = self._get_feedback(md)
        mq_datetime = self._parse_mq_datetime(md)
        msg_id = md.MsgId if hasattr(md, 'MsgId') else md['MsgId']

        # Build update SET clause based on feedback type
        update_fields = {}
        if feedback == MQFB_COA:
            self.m_pRSApp.m_STATUS_MSG = 'N'
            update_fields['status_msg'] = 'N'
            update_fields['mq_msg_id_coa'] = msg_id
            update_fields['mq_datetime_coa'] = mq_datetime
        elif feedback == MQFB_COD:
            self.m_pRSApp.m_STATUS_MSG = 'N'
            update_fields['status_msg'] = 'N'
            update_fields['mq_msg_id_cod'] = msg_id
            update_fields['mq_datetime_cod'] = mq_datetime
        else:
            self.m_pRSApp.m_STATUS_MSG = 'R'
            update_fields['status_msg'] = 'R'
            update_fields['mq_msg_id_rep'] = msg_id
            update_fields['mq_datetime_rep'] = mq_datetime

        # Execute UPDATE
        try:
            import psycopg2
            set_parts = []
            values = []
            for col, val in update_fields.items():
                set_parts.append(f'{col} = %s')
                if isinstance(val, (bytes, bytearray)):
                    values.append(psycopg2.Binary(val))
                else:
                    values.append(val)
            values.append(psycopg2.Binary(correl_id))

            sql = f'UPDATE {self.m_pRSApp.m_sTblName} SET {", ".join(set_parts)} WHERE mq_msg_id = %s'
            cursor = self.m_pDb3.connection.cursor()
            try:
                cursor.execute(sql, values)
            finally:
                cursor.close()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSApp.m_sTblName}: {ex}')
            return True

        return False

    # ------------------------------------------------------------------
    # MontaDbRegApp - Populate BacenAppRS fields for report
    # ------------------------------------------------------------------
    def monta_db_reg_app(self) -> bool:
        """Fill BacenAppRS fields for a report message."""
        md = self.m_md

        self.m_pRS.m_MQ_MSG_ID = md.MsgId if hasattr(md, 'MsgId') else md['MsgId']
        self.m_pRS.m_MQ_CORREL_ID = md.CorrelId if hasattr(md, 'CorrelId') else md['CorrelId']
        self.m_pRS.m_DB_DATETIME = self.m_t
        self.m_pRS.m_STATUS_MSG = 'N'
        self.m_pRS.m_FLAG_PROC = 'N'
        self.m_pRS.m_MQ_QN_ORIGEM = self.pMainSrv.pInitSrv.m_MqQlBacenCidadeRep
        self.m_pRS.m_MQ_DATETIME = self._parse_mq_datetime(md)
        self.m_pRS.m_MQ_HEADER = self._serialize_md(md)

        # Reports have no security header - fill with zeros
        self.m_pRS.m_SECURITY_HEADER = b'\x00' * SECHDR_SIZE

        # Reports have no NuOpe
        self.m_pRS.m_NU_OPE = ''

        # CodMsg based on feedback type
        feedback = self._get_feedback(md)
        if feedback == MQFB_COA:
            self.m_pRS.m_COD_MSG = 'COA'
        elif feedback == MQFB_COD:
            self.m_pRS.m_COD_MSG = 'COD'
        else:
            self.m_pRS.m_COD_MSG = 'REPORT'

        return False

    # ------------------------------------------------------------------
    # MontaDbRegLog - Populate STRLogRS fields for report
    # ------------------------------------------------------------------
    def monta_db_reg_log(self) -> bool:
        """Fill STRLogRS fields for a report message."""
        md = self.m_md

        self.m_pRSLog.m_MQ_MSG_ID = md.MsgId if hasattr(md, 'MsgId') else md['MsgId']
        self.m_pRSLog.m_MQ_CORREL_ID = md.CorrelId if hasattr(md, 'CorrelId') else md['CorrelId']
        self.m_pRSLog.m_DB_DATETIME = self.m_t
        self.m_pRSLog.m_STATUS_MSG = 'N'
        self.m_pRSLog.m_MQ_QN_ORIGEM = self.pMainSrv.pInitSrv.m_MqQlBacenCidadeRep
        self.m_pRSLog.m_MQ_DATETIME = self._parse_mq_datetime(md)
        self.m_pRSLog.m_MQ_HEADER = self._serialize_md(md)
        self.m_pRSLog.m_SECURITY_HEADER = b'\x00' * SECHDR_SIZE

        # Feedback-based CodMsg
        feedback = self._get_feedback(md)
        if feedback == MQFB_COA:
            self.m_pRSLog.m_COD_MSG = 'COA'
        elif feedback == MQFB_COD:
            self.m_pRSLog.m_COD_MSG = 'COD'
        else:
            self.m_pRSLog.m_COD_MSG = 'REPORT'

        return False

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------
    @staticmethod
    def _get_feedback(md) -> int:
        """Extract Feedback field from message descriptor."""
        try:
            return md.Feedback if hasattr(md, 'Feedback') else md['Feedback']
        except Exception:
            return 0

    @staticmethod
    def _parse_mq_datetime(md) -> datetime:
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
