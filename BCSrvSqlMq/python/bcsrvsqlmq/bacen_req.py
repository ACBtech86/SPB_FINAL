# bacen_req.py - Bacen Request task (port of BacenReq.cpp/h)
#
# CBacenReq: Reads from QLBacenCidadeReq queue, processes incoming
# messages from Bacen (Central Bank), verifies crypto, parses XML,
# updates BacenApp + STRLog tables, handles GEN0001/GEN0002/GEN0003
# special functions, and generates reports.

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


class CBacenReq(CThreadMQ):
    """Bacen Request task - reads incoming messages from Bacen.

    MQ Queue: QLBacenCidadeReq (local input, exclusive)
    DB Tables: BacenCidadeApp, STRLog, Controle, CidadeBacenApp
    """

    def __init__(self, name: str = '', automatic_thread: bool = True,
                 handle_mq: int = 0, main_srv=None):
        super().__init__(name, automatic_thread, handle_mq, main_srv)

        # Database connections and recordsets
        self.m_pDb1 = None   # BacenApp DB
        self.m_pDb2 = None   # STRLog DB
        self.m_pDb3 = None   # Controle DB
        self.m_pDb4 = None   # IFApp DB
        self.m_pRS = None    # CBacenAppRS
        self.m_pRSLog = None  # CSTRLogRS
        self.m_pRSCtr = None  # CControleRS
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

        # MQ message descriptor (reset each iteration)
        self.m_md = None

        # Timestamp for current message
        self.m_t = None

        # XML extracted fields
        self.m_NuOpe = ''
        self.m_CodMsg = ''
        self.m_TipoIdEmissor = ''
        self.m_IdEmissor = ''
        self.m_TipoIdDestinatario = ''
        self.m_IdDestinatario = ''
        self.m_StatusMsg = 'N'

    # ------------------------------------------------------------------
    # Thread lifecycle
    # ------------------------------------------------------------------
    def run_thread(self, main_srv=None):
        """RunThread: init -> init DB+MQ -> wait loop -> term DB+MQ -> term."""
        if main_srv is not None:
            self.pMainSrv = main_srv

        self.run_init()

        if not self.run_init_db_mq():
            self.run_wait_post()

        self.run_term_db_mq()
        self.run_term()

    # ------------------------------------------------------------------
    # RunInitDBeMQ - Create DB connections + open MQ queue
    # ------------------------------------------------------------------
    def run_init_db_mq(self) -> bool:
        """Initialize 4 DB connections, 4 recordsets, and open MQ queue.

        Returns True on error, False on success (matches C++ convention).
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

        # ---- Allocate message buffer ----
        self.m_buffermsg = bytearray(init_srv.m_MaxLenMsg)

        # ---- Set queue name ----
        self.m_szQueueName = init_srv.m_MqQlBacenCidadeReq
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

        # ---- Create DB connections (4 separate connections) ----
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

        # ---- Create recordsets ----
        self.m_pRS = CBacenAppRS(self.m_pDb1, init_srv.m_DbTbBacenCidadeApp)
        self.m_pRSLog = CSTRLogRS(self.m_pDb2, init_srv.m_DbTbStrLog)
        self.m_pRSCtr = CControleRS(self.m_pDb3, init_srv.m_DbTbControle)
        self.m_pRSApp = CIFAppRS(self.m_pDb4, init_srv.m_DbTbCidadeBacenApp)

        # ---- Open DB1 + BacenAppRS ----
        if not self._open_db_and_rs(
                self.m_pDb1, self.m_pRS, 'open',
                index=2, n_params=1, create_table=True):
            return True

        # ---- Open DB2 + STRLogRS ----
        if not self._open_db_and_rs(
                self.m_pDb2, self.m_pRSLog, 'open',
                create_table=True):
            return True

        # ---- Open DB3 + ControleRS ----
        if not self._open_db_and_rs(
                self.m_pDb3, self.m_pRSCtr, 'open',
                create_table=True):
            return True

        # ---- Open DB4 + IFAppRS ----
        if not self._open_db_and_rs(
                self.m_pDb4, self.m_pRSApp, 'open',
                index=1, n_params=1, create_table=True):
            return True

        return False

    def _open_db_and_rs(self, db, rs, method, index=None, n_params=None,
                        create_table=False) -> bool:
        """Open a database and its recordset. Returns True on success."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        try:
            if not db.open():
                return False
            if index is not None:
                rs.m_index = index
            if n_params is not None:
                pass  # params set via recordset attributes
            rs.open()
            return True
        except Exception as ex:
            err_str = str(ex)
            # Table does not exist - try to create
            if create_table and ('does not exist' in err_str or '42P01' in err_str):
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
    # RunTermDBeMQ - Close recordsets, DB connections, MQ queue
    # ------------------------------------------------------------------
    def run_term_db_mq(self) -> bool:
        """Cleanup all DB and MQ resources. Returns True on error."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        rt = False

        # Close MQ queue
        if self.m_queue is not None:
            try:
                self.m_queue.close()
            except pymqi.MQMIError as e:
                if e.reason != pymqi.CMQC.MQRC_NONE:
                    write_log(self.m_szTaskName, 8021, False, str(e.reason))

        # Disconnect from queue manager
        if self.m_qmgr is not None and self.m_CReason != pymqi.CMQC.MQRC_ALREADY_CONNECTED:
            try:
                self.m_qmgr.disconnect()
            except pymqi.MQMIError as e:
                if e.reason != pymqi.CMQC.MQRC_NONE:
                    write_log(self.m_szTaskName, 8022, False, str(e.reason))

        # Close recordsets and DB connections
        try:
            if self.m_pRS is not None:
                self.m_pRS.close()
            if self.m_pRSLog is not None:
                self.m_pRSLog.close()
            if self.m_pRSCtr is not None:
                self.m_pRSCtr.close()
            if self.m_pRSApp is not None:
                self.m_pRSApp.close()
            if self.m_pDb1 is not None:
                self.m_pDb1.close()
            if self.m_pDb2 is not None:
                self.m_pDb2.close()
            if self.m_pDb3 is not None:
                self.m_pDb3.close()
            if self.m_pDb4 is not None:
                self.m_pDb4.close()
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
        """MQGET loop: get message, decrypt, parse XML, update DB, commit/backout."""
        init_srv = self.pMainSrv.pInitSrv
        write_log = init_srv.m_WriteLog
        erro = False

        while not erro:
            erro = False
            self.m_StatusMsg = 'N'
            self.m_buflen = init_srv.m_MaxLenMsg - 1

            # ---- Prepare message descriptor and get options ----
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
                    return  # No more messages, exit loop
                write_log(self.m_szTaskName, 8023, False,
                          str(e.reason), str(e.comp))
                if e.reason == pymqi.CMQC.MQRC_TRUNCATED_MSG_FAILED:
                    erro = True
                continue

            write_log(self.m_szTaskName, 8024, True,
                      init_srv.m_QueueMgr,
                      init_srv.m_MqQlBacenCidadeReq,
                      str(self.m_messlen))

            self.m_t = datetime.utcnow()

            # ---- Decrypt and verify signature ----
            if not erro:
                erro = self.check_ass_decrypt_buffer_mq()

            # ---- Unicode conversion (ANSI -> Unicode -> ANSI round-trip) ----
            if not erro:
                if getattr(init_srv, 'm_UnicodeEnable', 'N') == 'N':
                    # ANSI mode: data after SECHDR is already Latin-1
                    pass
                # else: Unicode mode handled transparently with lxml

            # ---- Parse XML ----
            if not erro:
                erro = self.checar_xml()

            # ---- Audit log ----
            if not erro:
                if hasattr(self.pMainSrv, 'monta_audit'):
                    self.pMainSrv.monta_audit(self.m_t, self.m_md,
                                              self.m_buflen, self.m_buffermsg)

            # ---- Update DB (BacenApp + STRLog) ----
            if not erro:
                erro = self.update_db()

            # ---- Update Controle table ----
            if not erro:
                if self.m_StatusMsg == 'N':
                    erro = self.atualiza_ctr()

            # ---- Commit or Backout ----
            if erro:
                self.m_event_stop.set()
                # Rollback all DB transactions
                self._rollback_all()
                # Backout MQ message
                try:
                    self.m_qmgr.backout()
                    write_log(self.m_szTaskName, 8025, True)
                except pymqi.MQMIError as e:
                    write_log(self.m_szTaskName, 8027, False,
                              str(e.reason), str(e.comp))
            else:
                # Commit all DB transactions
                self._commit_all()
                # Commit MQ
                try:
                    self.m_qmgr.commit()
                    write_log(self.m_szTaskName, 8026, True)
                except pymqi.MQMIError as e:
                    write_log(self.m_szTaskName, 8028, False,
                              str(e.reason), str(e.comp))

    def _rollback_all(self):
        """Rollback all DB transactions, logging errors."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        for db_name, db in [('BacenApp', self.m_pDb1), ('STRLog', self.m_pDb2),
                            ('Controle', self.m_pDb3), ('IFApp', self.m_pDb4)]:
            try:
                if db is not None:
                    db.rollback()
            except Exception as ex:
                write_log(self.m_szTaskName, 8029, False, f'{db_name}: {ex}')
        # Unlock controle RS if locked
        if self.m_pRSCtr is not None and self.m_pRSCtr.is_locked():
            try:
                self.m_pRSCtr.unlock()
            except Exception:
                pass

    def _commit_all(self):
        """Commit all DB transactions, logging errors."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        for db_name, db in [('BacenApp', self.m_pDb1), ('STRLog', self.m_pDb2),
                            ('Controle', self.m_pDb3), ('IFApp', self.m_pDb4)]:
            try:
                if db is not None:
                    db.commit_trans()
            except Exception as ex:
                write_log(self.m_szTaskName, 8029, False, f'{db_name}: {ex}')
        # Unlock controle RS if locked
        if self.m_pRSCtr is not None and self.m_pRSCtr.is_locked():
            try:
                self.m_pRSCtr.unlock()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # CheckAssDeCryptBufferMQ - Verify/decrypt security header
    # ------------------------------------------------------------------
    def check_ass_decrypt_buffer_mq(self) -> bool:
        """Extract SECHDR, verify signature, decrypt message.

        Returns True on error.
        """
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

        # Parse security header (auto-detects V1 vs V2)
        sec_header = SECHDR.unpack(bytes(self.m_buffermsg[:actual_hdr_size]))
        self.m_messlen = actual_hdr_size

        # Validate header size marker (V1: 0x014C=332, V2: 0x024C=588)
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
                # Encrypted message (V1 or V2): decrypt -> log -> verify signature
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
                # Clear message: just log
                self.func_str_log(sec_header, data)
        else:
            write_log(self.m_szTaskName, 8075, False)
            self.func_str_log(sec_header, data)

        # Write decrypted data back to buffer (always use V2 size for internal buffer)
        if not rc and lenmsg > 0:
            self.m_buffermsg[SECHDR_SIZE:SECHDR_SIZE + len(data)] = data
            self.m_buflen = SECHDR_SIZE + len(data)

        # Write updated security header back
        packed_hdr = sec_header.pack()
        self.m_buffermsg[:SECHDR_SIZE] = packed_hdr

        return rc

    # ------------------------------------------------------------------
    # ChecarXml - Parse XML to extract key fields + handle special msgs
    # ------------------------------------------------------------------
    def checar_xml(self) -> bool:
        """Parse XML from message body, extract NuOpe/CodMsg/Emissor/Destinatario.

        Handles special functions: GEN0001 (Eco), GEN0002 (Log), GEN0003 (UltMsg).
        Returns True on error.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        lenmsg = self.m_buflen - SECHDR_SIZE
        if lenmsg <= 0:
            return False

        # Parse XML document
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

        # Extract BCMSG/NUOp
        val = self.find_tag(doc, 'BCMSG', 'NUOp')
        if val is not None:
            self.m_NuOpe = val

        # Extract Grupo_EmissorMsg fields
        self.m_TipoIdEmissor = self.find_tag(doc, 'Grupo_EmissorMsg', 'TipoId_Emissor') or ''
        self.m_IdEmissor = self.find_tag(doc, 'Grupo_EmissorMsg', 'Id_Emissor') or ''

        # Extract Grupo_DestinatarioMsg fields
        self.m_TipoIdDestinatario = self.find_tag(doc, 'Grupo_DestinatarioMsg', 'TipoId_Destinatario') or ''
        self.m_IdDestinatario = self.find_tag(doc, 'Grupo_DestinatarioMsg', 'Id_Destinatario') or ''

        # Extract CodMsg (no parent)
        val = self.find_tag(doc, None, 'CodMsg')
        if val is not None:
            self.m_CodMsg = val

        # Handle special functions
        if self.m_CodMsg == 'GEN0001':
            return self.func_eco()
        if self.m_CodMsg == 'GEN0002':
            return self.func_log()
        if self.m_CodMsg == 'GEN0003':
            return self.func_ult_msg()

        return False

    # ------------------------------------------------------------------
    # UpdateDB - Insert into BacenApp + STRLog tables
    # ------------------------------------------------------------------
    def update_db(self) -> bool:
        """Insert message into BacenApp and STRLog tables.

        Returns True on error.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        # ---- Insert into BacenApp ----
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

        # ---- Insert into STRLog ----
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
    # MontaDbRegApp - Populate BacenAppRS fields from MQ message
    # ------------------------------------------------------------------
    def monta_db_reg_app(self) -> bool:
        """Fill BacenAppRS recordset fields from current MQ message."""
        md = self.m_md

        # MQ Message ID and Correlation ID
        self.m_pRS.m_MQ_MSG_ID = md.MsgId if hasattr(md, 'MsgId') else md['MsgId']
        self.m_pRS.m_MQ_CORREL_ID = md.CorrelId if hasattr(md, 'CorrelId') else md['CorrelId']

        # DB timestamp (current UTC time)
        self.m_pRS.m_DB_DATETIME = self.m_t

        # Message status (N=Normal, E=Error, R=Report)
        self.m_pRS.m_STATUS_MSG = self.m_StatusMsg

        # Processing flag (N=new insert, S=after app reads)
        self.m_pRS.m_FLAG_PROC = 'N'

        # Source MQ queue name
        self.m_pRS.m_MQ_QN_ORIGEM = self.pMainSrv.pInitSrv.m_MqQlBacenCidadeReq

        # MQ Put date/time
        self.m_pRS.m_MQ_DATETIME = self._parse_mq_datetime(md)

        # MQ header (raw bytes of message descriptor)
        self.m_pRS.m_MQ_HEADER = self._serialize_md(md)

        # Security header (first SECHDR_SIZE bytes of buffer)
        self.m_pRS.m_SECURITY_HEADER = bytes(self.m_buffermsg[:SECHDR_SIZE])

        # Extracted XML fields
        self.m_pRS.m_NU_OPE = self.m_NuOpe
        self.m_pRS.m_COD_MSG = self.m_CodMsg

        # Message body (after security header)
        msg_body = bytes(self.m_buffermsg[SECHDR_SIZE:self.m_buflen])
        try:
            self.m_pRS.m_MSG = msg_body.decode('latin-1')
        except Exception:
            self.m_pRS.m_MSG = msg_body.decode('utf-8', errors='replace')

        return False

    # ------------------------------------------------------------------
    # MontaDbRegLog - Populate STRLogRS fields from MQ message
    # ------------------------------------------------------------------
    def monta_db_reg_log(self) -> bool:
        """Fill STRLogRS recordset fields from current MQ message."""
        md = self.m_md

        self.m_pRSLog.m_MQ_MSG_ID = md.MsgId if hasattr(md, 'MsgId') else md['MsgId']
        self.m_pRSLog.m_MQ_CORREL_ID = md.CorrelId if hasattr(md, 'CorrelId') else md['CorrelId']
        self.m_pRSLog.m_DB_DATETIME = self.m_t
        self.m_pRSLog.m_STATUS_MSG = self.m_StatusMsg
        self.m_pRSLog.m_MQ_QN_ORIGEM = self.pMainSrv.pInitSrv.m_MqQlBacenCidadeReq
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
    # AtualizaCtr - Update Controle table with last message info
    # ------------------------------------------------------------------
    def atualiza_ctr(self) -> bool:
        """Update Controle table with NuOpe and timestamp of last message.

        Returns True on error.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        ispb = '00038166' if self.m_IdEmissor == 'SISBACEN' else self.m_IdEmissor

        try:
            self.m_pDb3.begin_trans()
            self.m_pRSCtr.m_ParamISPB = ispb
            self.m_pRSCtr.lock()
            self.m_pRSCtr.open()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSCtr.m_sTblName}: {ex}')
            try:
                self.m_pRSCtr.unlock()
            except Exception:
                pass
            return True

        if self.m_pRSCtr.is_eof():
            write_log(self.m_szTaskName, 8077, False, ispb)
            return True

        # Update ULTMSG and DTHR_ULTMSG
        if self.m_NuOpe:
            self.m_pRSCtr.m_ULTMSG = self.m_NuOpe
            self.m_pRSCtr.m_DTHR_ULTMSG = self.m_t

        try:
            self.m_pRSCtr.update_existing(
                'ispb = %s', [ispb])
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSCtr.m_sTblName}: {ex}')
            try:
                self.m_pRSCtr.unlock()
            except Exception:
                pass
            return True

        return False

    # ------------------------------------------------------------------
    # ReadCtr - Read Controle table for a given ISPB
    # ------------------------------------------------------------------
    def read_ctr(self) -> bool:
        """Read Controle record for current IdEmissor. Returns True on error."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        ispb = '00038166' if self.m_IdEmissor == 'SISBACEN' else self.m_IdEmissor

        try:
            self.m_pRSCtr.m_ParamISPB = ispb
            self.m_pRSCtr.open()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSCtr.m_sTblName}: {ex}')
            return True

        if self.m_pRSCtr.is_eof():
            write_log(self.m_szTaskName, 8077, False, ispb)
            return True

        return False

    # ------------------------------------------------------------------
    # FuncEco - Handle GEN0001 (Echo request)
    # ------------------------------------------------------------------
    def func_eco(self) -> bool:
        """Handle GEN0001 Echo request. Generates R1 response and updates Controle.

        Returns True on error.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        # Verify GENReqECO tag exists
        val = self.find_tag(self.m_xmlDoc, 'SISMSG', 'GENReqECO')
        if val is None:
            write_log(self.m_szTaskName, 8078, False)
            return True

        # Generate response XML
        xml = self.gera_eco_r1()

        # Update Controle table with echo timestamp
        ispb = '00038166' if self.m_IdEmissor == 'SISBACEN' else self.m_IdEmissor

        try:
            self.m_pDb3.begin_trans()
            self.m_pRSCtr.m_ParamISPB = ispb
            self.m_pRSCtr.lock()
            self.m_pRSCtr.open()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSCtr.m_sTblName}: {ex}')
            try:
                self.m_pRSCtr.unlock()
            except Exception:
                pass
            return True

        if self.m_pRSCtr.is_eof():
            write_log(self.m_szTaskName, 8077, False, ispb)
            try:
                self.m_pRSCtr.unlock()
            except Exception:
                pass
            return True

        self.m_pRSCtr.m_DTHR_ECO = self.m_t

        try:
            self.m_pRSCtr.update_existing('ispb = %s', [ispb])
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSCtr.m_sTblName}: {ex}')
            try:
                self.m_pRSCtr.unlock()
            except Exception:
                pass
            return True

        # Insert response into IFApp table
        return self._insert_response_to_if_app('GEN0001R1', xml)

    # ------------------------------------------------------------------
    # FuncLog - Handle GEN0002 (Log request)
    # ------------------------------------------------------------------
    def func_log(self) -> bool:
        """Handle GEN0002 Log request. Queries STRLog and generates R1 response.

        Returns True on error.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        val = self.find_tag(self.m_xmlDoc, 'SISMSG', 'GENReqLOG')
        if val is None:
            write_log(self.m_szTaskName, 8078, False)
            return True

        # Get NUOp from GENReqLOG
        nu_op_log = self.find_tag(self.m_xmlDoc, 'GENReqLOG', 'NUOp') or ''

        # Generate response XML
        xml = self.gera_log_r1(nu_op_log)

        # Insert response into IFApp table
        return self._insert_response_to_if_app('GEN0002R1', xml)

    # ------------------------------------------------------------------
    # FuncUltMsg - Handle GEN0003 (Last message request)
    # ------------------------------------------------------------------
    def func_ult_msg(self) -> bool:
        """Handle GEN0003 UltMsg request. Reads Controle and generates R1 response.

        Returns True on error.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        val = self.find_tag(self.m_xmlDoc, 'SISMSG', 'GENReqUltMsg')
        if val is None:
            write_log(self.m_szTaskName, 8078, False)
            return True

        # Read Controle to get last message info
        if self.read_ctr():
            return True

        # Generate response XML
        xml = self.gera_ult_msg_r1()

        # Insert response into IFApp table
        return self._insert_response_to_if_app('GEN0003R1', xml)

    # ------------------------------------------------------------------
    # Helper: Insert response message into IFApp table
    # ------------------------------------------------------------------
    def _insert_response_to_if_app(self, cod_msg: str, xml: str) -> bool:
        """Insert a generated response message into the IFApp (CidadeBacenApp) table.

        Returns True on error.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

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
        self.m_pRSApp.m_MQ_QN_DESTINO = self.pMainSrv.pInitSrv.m_MqQrCidadeBacenRsp
        self.m_pRSApp.m_NU_OPE = self.m_NuOpe
        self.m_pRSApp.m_COD_MSG = cod_msg
        self.m_pRSApp.m_MSG = xml

        try:
            self.m_pRSApp.update()
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSApp.m_sTblName}: {ex}')
            return True

        return False

    # ------------------------------------------------------------------
    # GeraEcoR1 - Generate GEN0001R1 echo response XML
    # ------------------------------------------------------------------
    def gera_eco_r1(self) -> str:
        """Generate XML for GEN0001R1 echo response."""
        msg_eco = self.find_tag(self.m_xmlDoc, 'GENReqECO', 'MsgECO') or ''

        xml = '<?xml version="1.0"?>'
        xml += '<!DOCTYPE SPBDOC SYSTEM "SPBDOC.DTD">'
        xml += '<SPBDOC>'
        xml += '<BCMSG>'
        xml += '<Grupo_EmissorMsg>'
        xml += f'<TipoId_Emissor>{self.m_TipoIdDestinatario}</TipoId_Emissor>'
        xml += f'<Id_Emissor>{self.m_IdDestinatario}</Id_Emissor>'
        xml += '</Grupo_EmissorMsg>'
        xml += '<Grupo_DestinatarioMsg>'
        xml += f'<TipoId_Destinatario>{self.m_TipoIdEmissor}</TipoId_Destinatario>'
        xml += f'<Id_Destinatario>{self.m_IdEmissor}</Id_Destinatario>'
        xml += '</Grupo_DestinatarioMsg>'
        xml += f'<NUOp>{self.m_NuOpe}</NUOp>'
        xml += '</BCMSG>'
        xml += '<SISMSG>'
        xml += '<GENReqECORespReq>'
        xml += '<CodMsg>GEN0001R1</CodMsg>'
        xml += f'<MsgECO>{msg_eco}</MsgECO>'
        xml += '</GENReqECORespReq>'
        xml += '</SISMSG>'
        xml += '<USERMSG/>'
        xml += '</SPBDOC>'
        return xml

    # ------------------------------------------------------------------
    # GeraLogR1 - Generate GEN0002R1 log response XML
    # ------------------------------------------------------------------
    def gera_log_r1(self, nu_op_log: str) -> str:
        """Generate XML for GEN0002R1 log response.

        Queries STRLog for messages matching nu_op_log.
        """
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        # Query STRLog for the requested NUOp
        try:
            self.m_pRSLog.m_ParamNU_OPE = nu_op_log
            self.m_pRSLog.close()
            self.m_pRSLog.open()
            self.m_pRSLog.m_ParamNU_OPE = ''
        except Exception as ex:
            write_log(self.m_szTaskName, 8029, False,
                      f'{self.m_pRSLog.m_sTblName}: {ex}')

        xml = '<?xml version="1.0"?>'
        xml += '<!DOCTYPE SPBDOC SYSTEM "SPBDOC.DTD">'
        xml += '<SPBDOC>'
        xml += '<BCMSG>'
        xml += '<Grupo_EmissorMsg>'
        xml += f'<TipoId_Emissor>{self.m_TipoIdDestinatario}</TipoId_Emissor>'
        xml += f'<Id_Emissor>{self.m_IdDestinatario}</Id_Emissor>'
        xml += '</Grupo_EmissorMsg>'
        xml += '<Grupo_DestinatarioMsg>'
        xml += f'<TipoId_Destinatario>{self.m_TipoIdEmissor}</TipoId_Destinatario>'
        xml += f'<Id_Destinatario>{self.m_IdEmissor}</Id_Destinatario>'
        xml += '</Grupo_DestinatarioMsg>'
        xml += f'<NUOp>{self.m_NuOpe}</NUOp>'
        xml += '</BCMSG>'

        if self.m_pRSLog.is_eof():
            # NUOp not found - error response
            xml += '<SISMSG>'
            xml += '<GENReqLOG>'
            xml += f'<CodMsg>{self.m_CodMsg}E</CodMsg>'
            xml += f'<NUOp CodErro="EGEN0013">{self.m_NuOpe}</NUOp>'
            xml += '</GENReqLOG>'
            xml += '</SISMSG>'
            xml += '</SPBDOC>'
            return xml

        xml += '<SISMSG>'
        xml += '<GENReqLOGRespReq>'
        xml += '<CodMsg>GEN0002R1</CodMsg>'
        xml += '<Repet_GEN0002R1_Msg>'

        while not self.m_pRSLog.is_eof():
            xml += f'<Msg><![CDATA[{self.m_pRSLog.m_MSG}]]></Msg>'
            self.m_pRSLog.move_next()

        xml += '</Repet_GEN0002R1_Msg>'
        xml += '</GENReqLOGRespReq>'
        xml += '</SISMSG>'
        xml += '</SPBDOC>'
        return xml

    # ------------------------------------------------------------------
    # GeraUltMsgR1 - Generate GEN0003R1 last-message response XML
    # ------------------------------------------------------------------
    def gera_ult_msg_r1(self) -> str:
        """Generate XML for GEN0003R1 last-message response."""
        # Format DTHR_ULTMSG
        dthr = self.m_pRSCtr.m_DTHR_ULTMSG
        if dthr is not None:
            dthr_str = dthr.strftime('%Y%m%d%H%M%S')
        else:
            dthr_str = '00000000000000'

        # Format current time
        now_str = self.m_t.strftime('%Y%m%d%H%M%S')

        xml = '<?xml version="1.0"?>'
        xml += '<!DOCTYPE SPBDOC SYSTEM "SPBDOC.DTD">'
        xml += '<SPBDOC>'
        xml += '<BCMSG>'
        xml += '<Grupo_EmissorMsg>'
        xml += f'<TipoId_Emissor>{self.m_TipoIdDestinatario}</TipoId_Emissor>'
        xml += f'<Id_Emissor>{self.m_IdDestinatario}</Id_Emissor>'
        xml += '</Grupo_EmissorMsg>'
        xml += '<Grupo_DestinatarioMsg>'
        xml += f'<TipoId_Destinatario>{self.m_TipoIdEmissor}</TipoId_Destinatario>'
        xml += f'<Id_Destinatario>{self.m_IdEmissor}</Id_Destinatario>'
        xml += '</Grupo_DestinatarioMsg>'
        xml += f'<NUOp>{self.m_NuOpe}</NUOp>'
        xml += '</BCMSG>'
        xml += '<SISMSG>'
        xml += '<GENReqUltMsgRespReq>'
        xml += '<CodMsg>GEN0003R1</CodMsg>'
        xml += f'<NumUltOp>{self.m_pRSCtr.m_ULTMSG}</NumUltOp>'
        xml += f'<DtHUltMsg>{dthr_str}</DtHUltMsg>'
        xml += f'<DtHBC>{now_str}</DtHBC>'
        xml += '</GENReqUltMsgRespReq>'
        xml += '</SISMSG>'
        xml += '</SPBDOC>'
        return xml

    # ------------------------------------------------------------------
    # GeraReport - Generate MQ report message into IFApp table
    # ------------------------------------------------------------------
    def gera_report(self) -> bool:
        """Generate a report message in the IFApp table for crypto/XML errors.

        Returns True on error.
        """
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

        # Set correlation ID from MsgId
        self.m_pRSApp.m_MQ_CORREL_ID = md.MsgId if hasattr(md, 'MsgId') else md['MsgId']

        # Security header from buffer
        self.m_pRSApp.m_SECURITY_HEADER = bytes(self.m_buffermsg[:SECHDR_SIZE])

        # Message length and body
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
    # Utility: Parse MQ PutDate/PutTime into datetime
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_mq_datetime(md) -> datetime:
        """Parse MQ message descriptor PutDate/PutTime into a datetime."""
        try:
            put_date = md.PutDate if hasattr(md, 'PutDate') else md['PutDate']
            put_time = md.PutTime if hasattr(md, 'PutTime') else md['PutTime']

            if isinstance(put_date, bytes):
                put_date = put_date.decode('ascii').strip()
            if isinstance(put_time, bytes):
                put_time = put_time.decode('ascii').strip()

            date_str = str(put_date) + str(put_time)
            # Format: YYYYMMDDHHMMSSCC
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
        """Serialize pymqi.MD to bytes for storage."""
        try:
            return md.pack()
        except Exception:
            # Fallback: concatenate known fields
            parts = []
            for attr in ('MsgId', 'CorrelId', 'PutDate', 'PutTime'):
                val = getattr(md, attr, None)
                if val is None:
                    val = md.get(attr, b'')
                if isinstance(val, str):
                    val = val.encode('ascii')
                parts.append(val)
            return b''.join(parts).ljust(512, b'\x00')[:512]
