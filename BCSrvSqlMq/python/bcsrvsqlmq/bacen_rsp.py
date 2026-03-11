# bacen_rsp.py - Bacen Response task (port of BacenRsp.cpp/h)
#
# CBacenRsp: Reads from QLBacenCidadeRsp queue, processes response
# messages from Bacen (R1 responses to our requests), verifies crypto,
# parses XML, updates BacenApp + STRLog tables, handles response-specific
# functions (GEN0001R1, GEN0002R1, GEN0003R1, GEN0004).

import time
from datetime import datetime

import pymqi
import pymqi.CMQC

from bcsrvsqlmq.thread_mq import CThreadMQ, THREAD_EVENT_STOP, connect_qmgr
from bcsrvsqlmq.msg_sgr import SECHDR, SECHDR_SIZE, SECHDR_V1_SIZE
from bcsrvsqlmq.db.bc_database import CBCDatabase
from bcsrvsqlmq.db.bacen_app_rs import CBacenAppRS
from bcsrvsqlmq.db.str_log_rs import CSTRLogRS
from bcsrvsqlmq.db.controle_rs import CControleRS
from bcsrvsqlmq.db.if_app_rs import CIFAppRS


class CBacenRsp(CThreadMQ):
    """Bacen Response task - reads response messages from Bacen.

    MQ Queue: QLBacenCidadeRsp (local input, exclusive)
    DB Tables: BacenCidadeApp, STRLog, Controle, CidadeBacenApp
    """

    def __init__(self, name: str = '', automatic_thread: bool = True,
                 handle_mq: int = 0, main_srv=None):
        super().__init__(name, automatic_thread, handle_mq, main_srv)

        # Database connections and recordsets
        self.m_pDb1 = None
        self.m_pDb2 = None
        self.m_pDb3 = None
        self.m_pDb4 = None
        self.m_pRS = None
        self.m_pRSLog = None
        self.m_pRSCtr = None
        self.m_pRSApp = None

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

        # XML extracted fields
        self.m_NuOpe = ''
        self.m_CodMsg = ''
        self.m_TipoIdEmissor = ''
        self.m_IdEmissor = ''
        self.m_TipoIdDestinatario = ''
        self.m_IdDestinatario = ''
        self.m_CodMsgOr = ''       # Original message code (Rsp-specific)
        self.m_StatusMsg = 'N'

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
        """Initialize 4 DB connections, 4 recordsets, and open MQ queue.

        Returns True on error, False on success.
        """
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog

        self.m_pDb1 = None
        self.m_pDb2 = None
        self.m_pDb3 = None
        self.m_pDb4 = None
        self.m_pRS = None
        self.m_pRSLog = None
        self.m_pRSCtr = None
        self.m_pRSApp = None

        self.m_buffermsg = bytearray(init_srv.m_MaxLenMsg)
        self.m_szQueueName = init_srv.m_MqQlBacenCidadeRsp
        self.m_QMName = init_srv.m_QueueMgr

        # ---- Connect to queue manager ----
        try:
            self.m_qmgr = connect_qmgr(self.m_QMName, init_srv.m_MQChannel, init_srv.m_MQConnInfo)
            self.m_CReason = pymqi.CMQC.MQRC_NONE
        except pymqi.MQMIError as e:
            write_log(self.m_szTaskName, 8018, False, str(e.reason))
            self.m_CReason = e.reason
            return True

        # ---- Open queue for exclusive input ----
        open_options = pymqi.CMQC.MQOO_INPUT_EXCLUSIVE | pymqi.CMQC.MQOO_FAIL_IF_QUIESCING
        try:
            self.m_queue = pymqi.Queue(self.m_qmgr, self.m_szQueueName, open_options)
            self.m_OpenCode = pymqi.CMQC.MQCC_OK
        except pymqi.MQMIError as e:
            if e.reason != pymqi.CMQC.MQRC_NONE:
                write_log(self.m_szTaskName, 8019, False, str(e.reason))
            self.m_OpenCode = pymqi.CMQC.MQCC_FAILED
            return True

        # ---- Load crypto keys ----
        if init_srv.m_SecurityEnable != 'N':
            if self.read_public_key() != 0:
                return True
            if self.read_private_key() != 0:
                return True

        # ---- Create DB connections ----
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
        self.m_pDb4 = CBCDatabase(**db_params)
        self.m_pDb4.set_transactions()

        self.m_pRS = CBacenAppRS(self.m_pDb1, init_srv.m_DbTbBacenCidadeApp)
        self.m_pRSLog = CSTRLogRS(self.m_pDb2, init_srv.m_DbTbStrLog)
        self.m_pRSCtr = CControleRS(self.m_pDb3, init_srv.m_DbTbControle)
        self.m_pRSApp = CIFAppRS(self.m_pDb4, init_srv.m_DbTbCidadeBacenApp)

        # ---- Open DB connections and recordsets ----
        for db, rs, kw in [
            (self.m_pDb1, self.m_pRS, dict(index=2)),
            (self.m_pDb2, self.m_pRSLog, {}),
            (self.m_pDb3, self.m_pRSCtr, {}),
            (self.m_pDb4, self.m_pRSApp, dict(index=1)),
        ]:
            if not self._open_db_and_rs(db, rs, **kw):
                return True

        return False

    def _open_db_and_rs(self, db, rs, index=None) -> bool:
        """Open a database and its recordset. Returns True on success."""
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
            for obj in [self.m_pRS, self.m_pRSLog, self.m_pRSCtr, self.m_pRSApp]:
                if obj is not None:
                    obj.close()
            for obj in [self.m_pDb1, self.m_pDb2, self.m_pDb3, self.m_pDb4]:
                if obj is not None:
                    obj.close()
        except Exception as ex:
            write_log(self.m_szTaskName, 8071, False, str(ex))
            rt = True

        self.m_buffermsg = None
        self.m_pRS = None
        self.m_pRSLog = None
        self.m_pRSCtr = None
        self.m_pRSApp = None
        self.m_pDb1 = None
        self.m_pDb2 = None
        self.m_pDb3 = None
        self.m_pDb4 = None
        self.m_queue = None
        self.m_qmgr = None

        return rt

    # ------------------------------------------------------------------
    # ProcessaQueue - Main MQGET loop
    # ------------------------------------------------------------------
    def processa_queue(self):
        """MQGET loop for response messages."""
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog
        erro = False

        while not erro:
            erro = False
            self.m_StatusMsg = 'N'
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
                      init_srv.m_MqQlBacenCidadeRsp,
                      str(self.m_messlen))

            self.m_t = datetime.utcnow()

            # ---- Decrypt and verify signature ----
            if not erro:
                erro = self.check_ass_decrypt_buffer_mq()

            # ---- Parse XML ----
            if not erro:
                erro = self.checar_xml()

            # ---- Audit log ----
            if not erro:
                if hasattr(self.pMainSrv, 'monta_audit'):
                    self.pMainSrv.monta_audit(self.m_t, self.m_md,
                                              self.m_buflen, self.m_buffermsg)

            # ---- Update DB ----
            if not erro:
                erro = self.update_db()

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
                            ('Controle', self.m_pDb3), ('IFApp', self.m_pDb4)]:
            try:
                if db is not None:
                    db.rollback()
            except Exception as ex:
                write_log(self.m_szTaskName, 8029, False, f'{db_name}: {ex}')
        if self.m_pRSCtr is not None and self.m_pRSCtr.is_locked():
            try:
                self.m_pRSCtr.unlock()
            except Exception:
                pass

    def _commit_all(self):
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        for db_name, db in [('BacenApp', self.m_pDb1), ('STRLog', self.m_pDb2),
                            ('Controle', self.m_pDb3), ('IFApp', self.m_pDb4)]:
            try:
                if db is not None:
                    db.commit_trans()
            except Exception as ex:
                write_log(self.m_szTaskName, 8029, False, f'{db_name}: {ex}')
        if self.m_pRSCtr is not None and self.m_pRSCtr.is_locked():
            try:
                self.m_pRSCtr.unlock()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # CheckAssDeCryptBufferMQ
    # ------------------------------------------------------------------
    def check_ass_decrypt_buffer_mq(self) -> bool:
        """Extract SECHDR, verify signature, decrypt. Returns True on error."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        rc = False

        # Detect header version from first 2 bytes (V1=332=0x014C, V2=588=0x024C)
        if len(self.m_buffermsg) < 2:
            write_log(self.m_szTaskName, 8075, False)
            return True

        hdr_size_val = int.from_bytes(bytes(self.m_buffermsg[0:2]), 'big')
        if hdr_size_val == SECHDR_V1_SIZE:
            actual_hdr_size = SECHDR_V1_SIZE
        else:
            actual_hdr_size = SECHDR_SIZE  # V2 (588)

        if len(self.m_buffermsg) < actual_hdr_size:
            write_log(self.m_szTaskName, 8075, False)
            return True

        sec_header = SECHDR.unpack(bytes(self.m_buffermsg[:actual_hdr_size]))
        self.m_messlen = actual_hdr_size

        if hdr_size_val not in (SECHDR_V1_SIZE, SECHDR_SIZE):
            write_log(self.m_szTaskName, 8073, False)
            sec_header.CodErro = 0x04
        if sec_header.CodErro != 0x00:
            write_log(self.m_szTaskName, 8074, False, str(sec_header.CodErro))
            rc = True

        lenmsg = self.m_buflen - actual_hdr_size
        data = bytes(self.m_buffermsg[actual_hdr_size:actual_hdr_size + lenmsg])

        if lenmsg > 0:
            if sec_header.Versao in (0x01, 0x02):
                if not rc:
                    status, data = self.func_de_cript(sec_header, data)
                    if status != 0:
                        self.gera_report()
                        rc = True
                if not rc:
                    self.func_str_log(sec_header, data)
                if not rc:
                    status = self.func_verify_ass(sec_header, data)
                    if status != 0:
                        self.gera_report()
                        rc = True
            else:
                self.func_str_log(sec_header, data)
        else:
            write_log(self.m_szTaskName, 8075, False)
            self.func_str_log(sec_header, data)

        if not rc and lenmsg > 0:
            self.m_buffermsg[SECHDR_SIZE:SECHDR_SIZE + len(data)] = data
            self.m_buflen = SECHDR_SIZE + len(data)

        packed_hdr = sec_header.pack()
        self.m_buffermsg[:SECHDR_SIZE] = packed_hdr

        return rc

    # ------------------------------------------------------------------
    # ChecarXml - Parse XML for response messages
    # ------------------------------------------------------------------
    def checar_xml(self) -> bool:
        """Parse XML, extract fields, handle R1 response functions.

        Returns True on error.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        lenmsg = self.m_buflen - SECHDR_SIZE
        if lenmsg <= 0:
            return False

        xml_data = bytes(self.m_buffermsg[SECHDR_SIZE:SECHDR_SIZE + lenmsg])
        doc = self.load_document_sync(xml_data)
        if doc is None:
            return False
        self.m_xmlDoc = doc

        write_log(self.m_szTaskName, 8031, True,
                  '====== | ----------------Inicio Mensagem Xml ---------------------------------')
        self.walk_tree(doc)
        write_log(self.m_szTaskName, 8031, True,
                  '====== | ----------------Fim    Mensagem Xml ---------------------------------')

        # Extract fields
        val = self.find_tag(doc, 'BCMSG', 'NUOp')
        if val is not None:
            self.m_NuOpe = val

        self.m_TipoIdEmissor = self.find_tag(doc, 'Grupo_EmissorMsg', 'TipoId_Emissor') or ''
        self.m_IdEmissor = self.find_tag(doc, 'Grupo_EmissorMsg', 'Id_Emissor') or ''
        self.m_TipoIdDestinatario = self.find_tag(doc, 'Grupo_DestinatarioMsg', 'TipoId_Destinatario') or ''
        self.m_IdDestinatario = self.find_tag(doc, 'Grupo_DestinatarioMsg', 'Id_Destinatario') or ''

        val = self.find_tag(doc, None, 'CodMsg')
        if val is not None:
            self.m_CodMsg = val

        # Handle response-specific functions
        if self.m_CodMsg == 'GEN0001R1':
            return self.func_eco_r1()
        if self.m_CodMsg == 'GEN0002R1':
            return self.func_log_r1()
        if self.m_CodMsg == 'GEN0003R1':
            return self.func_ult_msg_r1()
        if self.m_CodMsg == 'GEN0004':
            return self.func_erro()

        return False

    # ------------------------------------------------------------------
    # UpdateDB - Insert into BacenApp + STRLog
    # ------------------------------------------------------------------
    def update_db(self) -> bool:
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
    # MontaDbRegApp - Populate BacenAppRS fields
    # ------------------------------------------------------------------
    def monta_db_reg_app(self) -> bool:
        md = self.m_md

        self.m_pRS.m_MQ_MSG_ID = md.MsgId if hasattr(md, 'MsgId') else md['MsgId']
        self.m_pRS.m_MQ_CORREL_ID = md.CorrelId if hasattr(md, 'CorrelId') else md['CorrelId']
        self.m_pRS.m_DB_DATETIME = self.m_t
        self.m_pRS.m_STATUS_MSG = self.m_StatusMsg
        self.m_pRS.m_FLAG_PROC = 'N'
        self.m_pRS.m_MQ_QN_ORIGEM = self.pMainSrv.pInitSrv.m_MqQlBacenCidadeRsp
        self.m_pRS.m_MQ_DATETIME = self._parse_mq_datetime(md)
        self.m_pRS.m_MQ_HEADER = self._serialize_md(md)
        self.m_pRS.m_SECURITY_HEADER = bytes(self.m_buffermsg[:SECHDR_SIZE])
        self.m_pRS.m_NU_OPE = self.m_NuOpe
        self.m_pRS.m_COD_MSG = self.m_CodMsg

        msg_body = bytes(self.m_buffermsg[SECHDR_SIZE:self.m_buflen])
        try:
            self.m_pRS.m_MSG = msg_body.decode('latin-1')
        except Exception:
            self.m_pRS.m_MSG = msg_body.decode('utf-8', errors='replace')

        return False

    # ------------------------------------------------------------------
    # MontaDbRegLog - Populate STRLogRS fields
    # ------------------------------------------------------------------
    def monta_db_reg_log(self) -> bool:
        md = self.m_md

        self.m_pRSLog.m_MQ_MSG_ID = md.MsgId if hasattr(md, 'MsgId') else md['MsgId']
        self.m_pRSLog.m_MQ_CORREL_ID = md.CorrelId if hasattr(md, 'CorrelId') else md['CorrelId']
        self.m_pRSLog.m_DB_DATETIME = self.m_t
        self.m_pRSLog.m_STATUS_MSG = self.m_StatusMsg
        self.m_pRSLog.m_MQ_QN_ORIGEM = self.pMainSrv.pInitSrv.m_MqQlBacenCidadeRsp
        self.m_pRSLog.m_MQ_DATETIME = self._parse_mq_datetime(md)
        self.m_pRSLog.m_MQ_HEADER = self._serialize_md(md)
        self.m_pRSLog.m_SECURITY_HEADER = b'\x00' * SECHDR_SIZE
        self.m_pRSLog.m_NU_OPE = self.m_NuOpe
        self.m_pRSLog.m_COD_MSG = self.m_CodMsg

        msg_body = bytes(self.m_buffermsg[SECHDR_SIZE:self.m_buflen])
        try:
            self.m_pRSLog.m_MSG = msg_body.decode('latin-1')
        except Exception:
            self.m_pRSLog.m_MSG = msg_body.decode('utf-8', errors='replace')

        return False

    # ------------------------------------------------------------------
    # FuncEcoR1 - Handle GEN0001R1 echo response
    # ------------------------------------------------------------------
    def func_eco_r1(self) -> bool:
        """Verify GENReqECORespReq tag exists in echo response."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        val = self.find_tag(self.m_xmlDoc, 'SISMSG', 'GENReqECORespReq')
        if val is None:
            write_log(self.m_szTaskName, 8078, False)
            return True

        return False

    # ------------------------------------------------------------------
    # FuncLogR1 - Handle GEN0002R1 log response
    # ------------------------------------------------------------------
    def func_log_r1(self) -> bool:
        """Verify GENReqLOGRespReq tag exists in log response."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        val = self.find_tag(self.m_xmlDoc, 'SISMSG', 'GENReqLOGRespReq')
        if val is None:
            write_log(self.m_szTaskName, 8078, False)
            return True

        return False

    # ------------------------------------------------------------------
    # FuncUltMsgR1 - Handle GEN0003R1 last-message response
    # ------------------------------------------------------------------
    def func_ult_msg_r1(self) -> bool:
        """Verify GENReqUltMsgRespReq tag exists in last-message response."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        val = self.find_tag(self.m_xmlDoc, 'SISMSG', 'GENReqUltMsgRespReq')
        if val is None:
            write_log(self.m_szTaskName, 8078, False)
            return True

        return False

    # ------------------------------------------------------------------
    # FuncErro - Handle GEN0004 error notification
    # ------------------------------------------------------------------
    def func_erro(self) -> bool:
        """Handle GEN0004 error notification. Sets status to Error."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        val = self.find_tag(self.m_xmlDoc, 'SISMSG', 'GENInfErro')
        if val is None:
            write_log(self.m_szTaskName, 8078, False)
            return True

        self.m_StatusMsg = 'E'
        return False

    # ------------------------------------------------------------------
    # GeraReport - Generate report message into IFApp table
    # ------------------------------------------------------------------
    def gera_report(self) -> bool:
        """Generate a report message in the IFApp table. Returns True on error."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        md = self.m_md
        lenmsg = self.m_buflen - SECHDR_SIZE

        try:
            self.m_pDb4.begin_trans()
            self.m_pRSApp.add_new()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSApp.m_sTblName}: {ex}')
            return True

        self.m_pRSApp.m_DB_DATETIME = self.m_t
        self.m_pRSApp.m_STATUS_MSG = 'P'
        self.m_pRSApp.m_FLAG_PROC = 'N'
        self.m_pRSApp.m_MQ_QN_DESTINO = self.pMainSrv.pInitSrv.m_MqQrCidadeBacenRep
        self.m_pRSApp.m_NU_OPE = ''
        self.m_pRSApp.m_COD_MSG = 'REPORT'

        self.m_pRSApp.m_MQ_CORREL_ID = md.MsgId if hasattr(md, 'MsgId') else md['MsgId']
        self.m_pRSApp.m_SECURITY_HEADER = bytes(self.m_buffermsg[:SECHDR_SIZE])

        self.m_pRSApp.m_MSG_LEN = lenmsg
        if lenmsg > 0:
            msg_body = bytes(self.m_buffermsg[SECHDR_SIZE:SECHDR_SIZE + lenmsg])
            try:
                self.m_pRSApp.m_MSG = msg_body.decode('latin-1')
            except Exception:
                self.m_pRSApp.m_MSG = msg_body.decode('utf-8', errors='replace')
        else:
            self.m_pRSApp.m_MSG = ''

        try:
            self.m_pRSApp.update()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSApp.m_sTblName}: {ex}')
            return True

        return False

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------
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
