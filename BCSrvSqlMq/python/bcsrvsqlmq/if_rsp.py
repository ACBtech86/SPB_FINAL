# if_rsp.py - IF Response task (port of IFRsp.cpp/h)
#
# IF (local institution) task that polls the database for pending response
# records and sends them as MQ messages via MQPUT to the remote queue
# QRCidadeBacenRsp.  This is the outbound path: DB -> MQ.

import time
import struct
from datetime import datetime

import pymqi
import pymqi.CMQC

from bcsrvsqlmq.thread_mq import CThreadMQ, connect_qmgr
from bcsrvsqlmq.msg_sgr import (
    COMHDR, SECHDR, SECHDR_SIZE, MAXMSGLENGTH,
    ALG_RSA_2048, ALG_3DES_168, ALG_HASH_SHA256,
    SECHDR_VERSION_V2, CA_SERPRO,
)
from bcsrvsqlmq.db.bc_database import CBCDatabase
from bcsrvsqlmq.db.if_app_rs import CIFAppRS
from bcsrvsqlmq.db.str_log_rs import CSTRLogRS


class CIFRsp(CThreadMQ):
    """IF Response task - reads pending DB records and sends to MQ (port of CIFRsp)."""

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
        """Create DB connections, open recordsets, connect to MQ and load
        crypto keys.  Returns True on error, False on success."""
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog

        self.m_pDb1 = None
        self.m_pDb2 = None
        self.m_pRS = None
        self.m_pRSLog = None
        self.m_open_ok = False

        # Queue names
        local_queue_name = init_srv.m_MqQlIFCidadeRsp
        self.m_szQueueName = local_queue_name.ljust(48)
        remote_queue_name = init_srv.m_MqQrCidadeBacenRsp
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

        # -- Load crypto keys --
        if init_srv.m_SecurityEnable == 'S':
            if self.read_public_key() != 0:
                return True
            if self.read_private_key() != 0:
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
                self.m_pRS.create_table()
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
        """Poll DB for pending response records (flag_proc='P'), build MQ
        message and send via MQPUT for each."""
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog
        remote_queue_name = init_srv.m_MqQrCidadeBacenRsp

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

            # Build buffer then put + update
            if self.update_mq_and_db(self.m_pRS):
                processa = False
                self.m_event_stop.set()

    # ------------------------------------------------------------------
    # Build MQ message buffer
    # ------------------------------------------------------------------
    def monta_buffer_mq(self, rs: CIFAppRS) -> bool:
        """Construct SECHDR + XML payload in m_buffermsg.
        Sign and encrypt when security is enabled.
        Returns True on error."""
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog

        # Build security header V2 (588 bytes)
        sec_hdr = SECHDR()  # defaults to V2 (588 bytes, RSA-2048, SHA-256)

        if init_srv.m_SecurityEnable == 'S':
            sec_hdr.Versao = SECHDR_VERSION_V2
            sec_hdr.CodErro = 0x00
            sec_hdr.AlgAssymKey = ALG_RSA_2048
            sec_hdr.AlgSymKey = ALG_3DES_168
            sec_hdr.AlgAssymKeyLocal = ALG_RSA_2048
            sec_hdr.AlgHash = ALG_HASH_SHA256
            sec_hdr.CADest = CA_SERPRO
            sec_hdr.CALocal = CA_SERPRO

        sec_packed = sec_hdr.pack()
        self.m_buffermsg[:SECHDR_SIZE] = sec_packed
        self.m_messlen = SECHDR_SIZE

        # Prepare XML payload
        msg_text = rs.m_MSG or ''
        msg_text = msg_text.rstrip('\x00\r\n')

        if not msg_text:
            write_log(self.m_szTaskName, 8065, False, 'Empty message (SPBMSG)')
            return True

        # Check total length
        total_len = SECHDR_SIZE + len(msg_text) * 2
        if total_len > init_srv.m_MaxLenMsg:
            write_log(self.m_szTaskName, 8069, False,
                      f'Message too large: {total_len} > {init_srv.m_MaxLenMsg}')
            return True

        # Convert ANSI to UTF-16LE
        unicode_bytes = msg_text.encode('utf-16-le')
        lenwrk = len(unicode_bytes)

        # Validate XML
        if lenwrk > 0:
            if self.checar_xml(lenwrk, unicode_bytes):
                return True

        # Convert to big-endian UTF-16 (byte swap)
        be_bytes = bytearray(lenwrk)
        for i in range(0, lenwrk, 2):
            if i + 1 < lenwrk:
                be_bytes[i] = unicode_bytes[i + 1]
                be_bytes[i + 1] = unicode_bytes[i]
            else:
                be_bytes[i] = unicode_bytes[i]

        payload_data = bytes(be_bytes)

        if sec_hdr.Versao == 0x00:
            # Clear text
            self.func_log(sec_hdr, payload_data)
            self.m_buffermsg[self.m_messlen:self.m_messlen + lenwrk] = payload_data
            self.m_messlen += lenwrk
        else:
            # Encrypted: sign -> log -> encrypt
            rc, payload_data = self.func_assinar(sec_hdr, payload_data)
            if rc != 0:
                return True

            self.func_log(sec_hdr, payload_data)

            rc, payload_data = self.func_cript(sec_hdr, payload_data)
            if rc != 0:
                return True

            self.m_buffermsg[self.m_messlen:self.m_messlen + len(payload_data)] = payload_data
            self.m_messlen += len(payload_data)

            # Re-pack security header
            self.m_buffermsg[:SECHDR_SIZE] = sec_hdr.pack()

        self.m_buflen = self.m_messlen

        # Unicode disable override for testing
        if hasattr(init_srv, 'm_UnicodeEnable') and init_srv.m_UnicodeEnable == 'N':
            raw = msg_text.encode('latin-1', errors='replace')
            if len(raw) > 0:
                self.m_buffermsg[SECHDR_SIZE:SECHDR_SIZE + len(raw)] = raw
                self.m_messlen = SECHDR_SIZE + len(raw)
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
        remote_queue_name = init_srv.m_MqQrCidadeBacenRsp
        erro = False

        # Build MQ buffer first
        if self.monta_buffer_mq(rs):
            return True

        # Prepare MQ message descriptor
        md = pymqi.MD()
        md['Version'] = pymqi.CMQC.MQMD_VERSION_1
        md['Expiry'] = pymqi.CMQC.MQEI_UNLIMITED
        md['Report'] = (pymqi.CMQC.MQRO_COA
                        + pymqi.CMQC.MQRO_COD
                        + pymqi.CMQC.MQRO_EXCEPTION)
        md['MsgType'] = pymqi.CMQC.MQMT_REPLY
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
    # XML validation
    # ------------------------------------------------------------------
    def checar_xml(self, lenmsg: int, data: bytes) -> bool:
        """Parse XML from the message payload.  Returns True on error."""
        if lenmsg <= 0:
            return False

        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog

        try:
            xml_str = data[:lenmsg].decode('utf-16-le')
        except (UnicodeDecodeError, ValueError):
            return True

        doc = self.load_document_sync(xml_str.encode('utf-8'))
        if doc is None:
            return True

        self.m_xmlDoc = doc

        write_log(self.m_szTaskName, 8031, True,
                  '====== | ----------------Inicio Mensagem Xml ---------------------------------')
        self.walk_tree(doc)
        write_log(self.m_szTaskName, 8031, True,
                  '====== | ----------------Fim    Mensagem Xml ---------------------------------')

        return False

    # ------------------------------------------------------------------
    # Update application record after send
    # ------------------------------------------------------------------
    def update_db_reg_app(self) -> bool:
        """Set MQ msg-id, status, flag, timestamps on the app record."""
        md = self.m_last_md
        rs = self.m_pRS

        rs.m_MQ_MSG_ID = md['MsgId']
        rs.m_STATUS_MSG = 'N'
        rs.m_FLAG_PROC = 'E'
        rs.m_MQ_QN_DESTINO = self.pMainSrv.pInitSrv.m_MqQrCidadeBacenRsp
        rs.m_MQ_DATETIME_PUT = datetime.utcnow()
        rs.m_MQ_HEADER = b'\x00' * 512
        rs.m_SECURITY_HEADER = b'\x00' * SECHDR_SIZE

        return False

    # ------------------------------------------------------------------
    # Build log record
    # ------------------------------------------------------------------
    def monta_db_reg_log(self) -> bool:
        """Populate log recordset fields from the app record + MQ MD."""
        md = self.m_last_md
        rs = self.m_pRS
        rs_log = self.m_pRSLog
        remote_queue_name = self.pMainSrv.pInitSrv.m_MqQrCidadeBacenRsp

        rs_log.m_MQ_MSG_ID = md['MsgId']
        rs_log.m_MQ_CORREL_ID = md['CorrelId']
        rs_log.m_DB_DATETIME = rs.m_DB_DATETIME
        rs_log.m_STATUS_MSG = rs.m_STATUS_MSG
        rs_log.m_MQ_QN_ORIGEM = remote_queue_name
        rs_log.m_MQ_DATETIME = datetime.utcnow()
        rs_log.m_MQ_HEADER = b'\x00' * 512
        rs_log.m_SECURITY_HEADER = b'\x00' * SECHDR_SIZE
        rs_log.m_NU_OPE = rs.m_NU_OPE
        rs_log.m_COD_MSG = rs.m_COD_MSG
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
                      security_header = %s
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
                psycopg2.Binary(rs.m_SECURITY_HEADER) if rs.m_SECURITY_HEADER else None,
                rs.m_DB_DATETIME,
                rs.m_COD_MSG,
                self.pMainSrv.pInitSrv.m_MqQrCidadeBacenRsp,
            ))
        finally:
            cursor.close()
