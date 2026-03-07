# if_sup.py - IF Support task (port of IFSup.cpp/h)
#
# IF (local institution) task that polls the database for pending support
# records and sends them as MQ messages via MQPUT to the remote queue
# QRCidadeBacenSup.  This is the outbound path: DB -> MQ.
#
# Key differences from IFReq/IFRsp:
#   - MontaBufferMQ copies raw message bytes (no security header, no
#     sign/encrypt).
#   - UpdateDbRegApp sets COD_MSG = 'SUPORTE'.
#   - MontaDbRegLog sets COD_MSG = 'SUPORTE'.
#   - MsgType is MQMT_REQUEST.

import time
from datetime import datetime

import pymqi
import pymqi.CMQC

from bcsrvsqlmq.thread_mq import CThreadMQ, connect_qmgr
from bcsrvsqlmq.msg_sgr import (
    COMHDR, SECHDR, SECHDR_SIZE, MAXMSGLENGTH,
)
from bcsrvsqlmq.db.bc_database import CBCDatabase
from bcsrvsqlmq.db.if_app_rs import CIFAppRS
from bcsrvsqlmq.db.str_log_rs import CSTRLogRS


class CIFSup(CThreadMQ):
    """IF Support task - reads pending DB records and sends to MQ (port of CIFSup)."""

    def __init__(self, name: str = '', automatic_thread: bool = True,
                 handle_mq: int = 0, main_srv=None):
        super().__init__(name, automatic_thread, handle_mq, main_srv)

        # Database objects
        self.m_pDb1 = None          # type: CBCDatabase
        self.m_pDb2 = None          # type: CBCDatabase
        self.m_pRS = None           # type: CIFAppRS
        self.m_pRSLog = None        # type: CSTRLogRS

        # MQ objects (pymqi)
        self.m_qmgr = None          # type: pymqi.QueueManager
        self.m_queue = None          # type: pymqi.Queue
        self.m_open_ok = False

        # MQ message buffer
        self.m_buffermsg = bytearray(MAXMSGLENGTH)
        self.m_buflen = 0
        self.m_messlen = 0

        # Timestamp for current processing cycle
        self.m_t = None              # type: datetime

        # Last MQ message descriptor
        self.m_last_md = None        # type: pymqi.MD

    # ------------------------------------------------------------------
    # Thread lifecycle
    # ------------------------------------------------------------------
    def run_thread(self, main_srv):
        """RunInit -> RunInitDBeMQ -> RunWaitPost -> RunTermDBeMQ -> RunTerm."""
        self.pMainSrv = main_srv
        self.run_init()
        if not self.run_init_db_mq():
            self.run_wait_post()
        self.run_term_db_mq()
        self.run_term()

    # ------------------------------------------------------------------
    # Initialise DB and MQ resources
    # ------------------------------------------------------------------
    def run_init_db_mq(self) -> bool:
        """Create DB connections, open recordsets, connect to MQ.
        Returns True on error, False on success."""
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog

        self.m_pDb1 = None
        self.m_pDb2 = None
        self.m_pRS = None
        self.m_pRSLog = None
        self.m_open_ok = False

        # Queue names
        local_queue_name = init_srv.m_MqQlIFCidadeSup
        self.m_szQueueName = local_queue_name.ljust(48)
        remote_queue_name = init_srv.m_MqQrCidadeBacenSup
        queue_manager_name = init_srv.m_QueueMgr

        # -- MQ connect --
        try:
            self.m_qmgr = connect_qmgr(queue_manager_name, init_srv.m_MQChannel, init_srv.m_MQConnInfo)
        except pymqi.MQMIError as exc:
            write_log(self.m_szTaskName, 8018, False,
                      f'MQCONN failed: cc={exc.comp} rc={exc.reason}')
            return True

        # -- MQ open queue for output --
        open_opts = pymqi.CMQC.MQOO_OUTPUT | pymqi.CMQC.MQOO_FAIL_IF_QUIESCING
        try:
            self.m_queue = pymqi.Queue(self.m_qmgr, local_queue_name, open_opts)
            self.m_open_ok = True
        except pymqi.MQMIError as exc:
            write_log(self.m_szTaskName, 8019, False,
                      f'MQOPEN failed: cc={exc.comp} rc={exc.reason}')
            return True

        # -- Database 1 (application recordset) --
        self.m_pDb1 = CBCDatabase(
            db_name=init_srv.m_DBName, mq_server=init_srv.m_MQServer,
            porta=init_srv.m_MonitorPort, max_len_msg=init_srv.m_MaxLenMsg,
            db_server=init_srv.m_DBServer, db_port=init_srv.m_DBPort,
            db_user=init_srv.m_DBUser, db_password=init_srv.m_DBPassword)
        self.m_pDb1.set_transactions()

        self.m_pRS = CIFAppRS(self.m_pDb1, init_srv.m_DbTbCidadeBacenApp)

        if not self.m_pDb1.open():
            write_log(self.m_szTaskName, 8071, False, 'DB1 open failed')
            return True

        self.m_pRS.m_index = 2
        self.m_pRS.m_ParamMQ_QN_DESTINO = remote_queue_name
        self.m_pRS.m_ParamFLAG_PROC = 'P'

        try:
            self.m_pRS.open()
        except Exception as exc:
            try:
                self.m_pDb1.rollback()
                time.sleep(30)
                self.m_pRS.m_index = 2
                self.m_pRS.m_ParamMQ_QN_DESTINO = remote_queue_name
                self.m_pRS.m_ParamFLAG_PROC = 'P'
                self.m_pRS.open()
            except Exception as exc2:
                write_log(self.m_szTaskName, 8071, False, str(exc2))
                return True

        # -- Database 2 (log recordset) --
        self.m_pDb2 = CBCDatabase(
            db_name=init_srv.m_DBName, mq_server=init_srv.m_MQServer,
            porta=init_srv.m_MonitorPort, max_len_msg=init_srv.m_MaxLenMsg,
            db_server=init_srv.m_DBServer, db_port=init_srv.m_DBPort,
            db_user=init_srv.m_DBUser, db_password=init_srv.m_DBPassword)
        self.m_pDb2.set_transactions()

        self.m_pRSLog = CSTRLogRS(self.m_pDb2, init_srv.m_DbTbStrLog)

        if not self.m_pDb2.open():
            write_log(self.m_szTaskName, 8071, False, 'DB2 open failed')
            return True

        try:
            self.m_pRSLog.open()
        except Exception as exc:
            try:
                self.m_pDb2.rollback()
                time.sleep(30)
                self.m_pRSLog.open()
            except Exception as exc2:
                write_log(self.m_szTaskName, 8071, False, str(exc2))
                return True

        return False

    # ------------------------------------------------------------------
    # Terminate DB and MQ resources
    # ------------------------------------------------------------------
    def run_term_db_mq(self) -> bool:
        """Close MQ queue/connection and DB connections."""
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog
        rt = False

        if self.m_queue is not None:
            try:
                self.m_queue.close()
            except pymqi.MQMIError as exc:
                write_log(self.m_szTaskName, 8021, False,
                          f'MQCLOSE reason={exc.reason}')
            self.m_queue = None

        if self.m_qmgr is not None:
            try:
                self.m_qmgr.disconnect()
            except pymqi.MQMIError as exc:
                write_log(self.m_szTaskName, 8022, False,
                          f'MQDISC reason={exc.reason}')
            self.m_qmgr = None

        try:
            if self.m_pRS is not None:
                self.m_pRS.close()
            if self.m_pRSLog is not None:
                self.m_pRSLog.close()
            if self.m_pDb1 is not None:
                self.m_pDb1.close()
            if self.m_pDb2 is not None:
                self.m_pDb2.close()
        except Exception as exc:
            write_log(self.m_szTaskName, 8071, False, str(exc))
            rt = True

        self.m_pRS = None
        self.m_pRSLog = None
        self.m_pDb1 = None
        self.m_pDb2 = None

        return rt

    # ------------------------------------------------------------------
    # Main processing loop
    # ------------------------------------------------------------------
    def processa_queue(self):
        """Poll DB for pending support records (flag_proc='P'), build MQ
        message and send via MQPUT for each."""
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog
        remote_queue_name = init_srv.m_MqQrCidadeBacenSup

        processa = True
        while processa:
            try:
                self.m_pRS.close()
                self.m_pDb1.begin_trans()
                self.m_pRS.m_index = 2
                self.m_pRS.m_ParamMQ_QN_DESTINO = remote_queue_name
                self.m_pRS.m_ParamFLAG_PROC = 'P'
                self.m_pRS.open()
            except Exception as exc:
                write_log(self.m_szTaskName, 8029, False, str(exc))
                return

            if self.m_pRS.is_eof():
                self.m_pDb1.rollback()
                processa = False
                continue

            self.m_t = datetime.utcnow()

            if self.update_mq_and_db(self.m_pRS):
                processa = False
                self.m_event_stop.set()

    # ------------------------------------------------------------------
    # Build MQ message buffer  (support-specific: raw msg, no SECHDR)
    # ------------------------------------------------------------------
    def monta_buffer_mq(self, rs: CIFAppRS) -> bool:
        """Copy raw message from DB record into m_buffermsg.
        Support messages have no security header or encryption.
        Returns True on error."""
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog

        self.m_messlen = 0

        msg_text = rs.m_MSG or ''
        if not msg_text:
            write_log(self.m_szTaskName, 8065, False, 'Empty message (SPBMSG)')
            return True

        msg_bytes = msg_text.encode('latin-1', errors='replace') if isinstance(msg_text, str) else msg_text
        msg_len = len(msg_bytes)

        self.m_buffermsg[:msg_len] = msg_bytes
        self.m_messlen = msg_len
        self.m_buflen = self.m_messlen

        return False

    # ------------------------------------------------------------------
    # MQPUT + update DB
    # ------------------------------------------------------------------
    def update_mq_and_db(self, rs: CIFAppRS) -> bool:
        """Build buffer, put message on queue, update app record, insert
        log record, commit MQ+DB.  Returns True on error."""
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog
        remote_queue_name = init_srv.m_MqQrCidadeBacenSup
        erro = False

        # Build MQ buffer
        if self.monta_buffer_mq(rs):
            return True

        # Prepare MQ message descriptor
        md = pymqi.MD()
        md['Version'] = pymqi.CMQC.MQMD_VERSION_1
        md['Expiry'] = pymqi.CMQC.MQEI_UNLIMITED
        md['Report'] = (pymqi.CMQC.MQRO_COA
                        + pymqi.CMQC.MQRO_COD
                        + pymqi.CMQC.MQRO_EXCEPTION)
        md['MsgType'] = pymqi.CMQC.MQMT_REQUEST
        md['Format'] = pymqi.CMQC.MQFMT_STRING
        md['Priority'] = pymqi.CMQC.MQPRI_PRIORITY_AS_Q_DEF
        md['Persistence'] = pymqi.CMQC.MQPER_PERSISTENT
        md['ReplyToQMgr'] = init_srv.m_QueueMgr.encode().ljust(48, b'\x00')
        md['ReplyToQ'] = init_srv.m_MqQlBacenCidadeRep.encode().ljust(48, b'\x00')
        md['Encoding'] = pymqi.CMQC.MQENC_NATIVE
        md['CodedCharSetId'] = pymqi.CMQC.MQCCSI_Q_MGR

        # Prepare PMO
        pmo = pymqi.PMO()
        pmo['Options'] = pymqi.CMQC.MQPMO_SYNCPOINT

        # MQPUT
        message = bytes(self.m_buffermsg[:self.m_buflen])
        try:
            self.m_queue.put(message, md, pmo)
        except pymqi.MQMIError as exc:
            erro = True
            write_log(self.m_szTaskName, 8030, False,
                      f'MQPUT failed: rc={exc.reason} cc={exc.comp}')
            if exc.reason == pymqi.CMQC.MQRC_Q_FULL:
                write_log(self.m_szTaskName, 8067, False,
                          f'Queue full: {self.m_szQueueName}')
            elif exc.reason == pymqi.CMQC.MQRC_MSG_TOO_BIG_FOR_Q:
                write_log(self.m_szTaskName, 8068, False,
                          f'Message too big for queue: {self.m_szQueueName}')
            return erro

        self.m_last_md = md

        write_log(self.m_szTaskName, 8061, True,
                  f'MQPUT OK qmgr={init_srv.m_QueueMgr} '
                  f'queue={remote_queue_name} len={self.m_messlen}')

        # Prepare log recordset
        if not erro:
            try:
                self.m_pRSLog.close()
                self.m_pDb2.begin_trans()
                self.m_pRSLog.add_new()
            except Exception as exc:
                write_log(self.m_szTaskName, 8029, False, str(exc))
                erro = True

        # Edit application record
        if not erro:
            try:
                rs.edit()
            except Exception as exc:
                write_log(self.m_szTaskName, 8029, False, str(exc))
                erro = True

        # Update app record fields
        if not erro:
            erro = self.update_db_reg_app()

        # Build log record
        if not erro:
            erro = self.monta_db_reg_log()

        # Insert log record
        if not erro:
            try:
                self.m_pRSLog.update()
            except Exception as exc:
                write_log(self.m_szTaskName, 8029, False, str(exc))
                erro = True

        # Update app record in DB
        if not erro:
            try:
                self._update_app_record_in_db()
            except Exception as exc:
                write_log(self.m_szTaskName, 8029, False, str(exc))
                erro = True

        # Commit or rollback
        if erro:
            try:
                self.m_pDb1.rollback()
            except Exception as exc:
                write_log(self.m_szTaskName, 8029, False, str(exc))
            try:
                self.m_pDb2.rollback()
            except Exception as exc:
                write_log(self.m_szTaskName, 8029, False, str(exc))
            try:
                self.m_qmgr.backout()
                write_log(self.m_szTaskName, 8025, True, 'MQBACK OK')
            except pymqi.MQMIError as exc:
                write_log(self.m_szTaskName, 8027, False,
                          f'MQBACK failed: rc={exc.reason} cc={exc.comp}')
        else:
            try:
                self.m_pDb1.commit_trans()
            except Exception as exc:
                write_log(self.m_szTaskName, 8029, False, str(exc))
            try:
                self.m_pDb2.commit_trans()
            except Exception as exc:
                write_log(self.m_szTaskName, 8029, False, str(exc))
            try:
                self.m_qmgr.commit()
                write_log(self.m_szTaskName, 8026, True, 'MQCMIT OK')
            except pymqi.MQMIError as exc:
                write_log(self.m_szTaskName, 8028, False,
                          f'MQCMIT failed: rc={exc.reason} cc={exc.comp}')

        return erro

    # ------------------------------------------------------------------
    # Update application record after send
    # ------------------------------------------------------------------
    def update_db_reg_app(self) -> bool:
        """Set MQ msg-id, status, flag, timestamps on the app record.
        Support messages set COD_MSG to 'SUPORTE'."""
        md = self.m_last_md
        rs = self.m_pRS

        rs.m_MQ_MSG_ID = md['MsgId']
        rs.m_STATUS_MSG = 'N'
        rs.m_FLAG_PROC = 'E'
        rs.m_MQ_QN_DESTINO = self.pMainSrv.pInitSrv.m_MqQrCidadeBacenSup
        rs.m_MQ_DATETIME_PUT = datetime.utcnow()
        rs.m_MQ_HEADER = b'\x00' * 512
        rs.m_COD_MSG = 'SUPORTE'

        return False

    # ------------------------------------------------------------------
    # Build log record
    # ------------------------------------------------------------------
    def monta_db_reg_log(self) -> bool:
        """Populate log recordset fields from the app record + MQ MD.
        Support messages set COD_MSG to 'SUPORTE'."""
        md = self.m_last_md
        rs = self.m_pRS
        rs_log = self.m_pRSLog
        remote_queue_name = self.pMainSrv.pInitSrv.m_MqQrCidadeBacenSup

        rs_log.m_MQ_MSG_ID = md['MsgId']
        rs_log.m_MQ_CORREL_ID = md['CorrelId']
        rs_log.m_DB_DATETIME = rs.m_DB_DATETIME
        rs_log.m_STATUS_MSG = rs.m_STATUS_MSG
        rs_log.m_MQ_QN_ORIGEM = remote_queue_name
        rs_log.m_MQ_DATETIME = datetime.utcnow()
        rs_log.m_MQ_HEADER = b'\x00' * 512
        rs_log.m_COD_MSG = 'SUPORTE'
        rs_log.m_MSG = rs.m_MSG

        return False

    # ------------------------------------------------------------------
    # Internal: persist the updated app record via SQL UPDATE
    # ------------------------------------------------------------------
    def _update_app_record_in_db(self):
        """Execute SQL UPDATE on the app table for the current record."""
        import psycopg2
        rs = self.m_pRS
        sql = f'''UPDATE {rs.m_sTblName}
                  SET mq_msg_id = %s,
                      status_msg = %s,
                      flag_proc = %s,
                      mq_qn_destino = %s,
                      mq_datetime_put = %s,
                      mq_header = %s,
                      cod_msg = %s
                  WHERE db_datetime = %s
                    AND cod_msg = %s
                    AND mq_qn_destino = %s'''
        cursor = self.m_pDb1.connection.cursor()
        try:
            cursor.execute(sql, (
                psycopg2.Binary(rs.m_MQ_MSG_ID) if rs.m_MQ_MSG_ID else None,
                rs.m_STATUS_MSG,
                rs.m_FLAG_PROC,
                rs.m_MQ_QN_DESTINO,
                rs.m_MQ_DATETIME_PUT,
                psycopg2.Binary(rs.m_MQ_HEADER) if rs.m_MQ_HEADER else None,
                rs.m_COD_MSG,
                rs.m_DB_DATETIME,
                rs.m_COD_MSG,
                self.pMainSrv.pInitSrv.m_MqQrCidadeBacenSup,
            ))
        finally:
            cursor.close()
