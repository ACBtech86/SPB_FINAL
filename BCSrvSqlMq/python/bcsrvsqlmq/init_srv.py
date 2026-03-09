# init_srv.py - Service initialization (port of InitSrv.cpp/h)

import os
import sys
import configparser
import platform

from bcsrvsqlmq.nt_service import CNTService
from bcsrvsqlmq.nt_servmsg import *
from bcsrvsqlmq.logging_module import LoggingModule
from bcsrvsqlmq.security.openssl_wrapper import init_crypto, cleanup_crypto


SERVICE_RUNNING = 0x00000004
SERVICE_STOPPED = 0x00000001
SERVICE_STOP_PENDING = 0x00000003


class CInitSrv(CNTService):
    """Service initialization and configuration (port of CInitSrv)."""

    def __init__(self, service_name: str, dependencies: str = ''):
        super().__init__(service_name, dependencies)

        # Logging module (replaces DLL)
        self._logger = LoggingModule()
        self.m_WriteLog = self._logger.write_log
        self.m_WriteReg = self._logger.write_reg
        self.m_OpenLog = self._logger.open_log
        self.m_CloseLog = self._logger.close_log
        self.m_Trace = self._logger.set_trace

        # INI file path
        self.m_ARQINI = ''

        # Main server reference
        self.pMainSrv = None

        # Service name
        self.m_szServiceName = service_name

        # ---- Configuration variables ----
        # [Servico]
        self.m_ServiceName = service_name
        self.m_TraceLevel = 'N'
        self.m_MonitorPort = 14499
        self.m_SrvTimeout = 120
        self.m_MaxLenMsg = 1000

        # [Diretorios]
        self.m_DirTraces = 'C:\\BCSRVSQLMQ\\Traces'
        self.m_DirAudFile = 'C:\\BCSRVSQLMQ\\AuditFiles'

        # [DataBase]
        self.m_DBServer = platform.node()
        self.m_DBAliasName = 'banuxSPB'
        self.m_DBName = 'banuxSPB'
        self.m_DBPort = 5432
        self.m_DBUserName = 'postgres'
        self.m_DBPassword = ''
        self.m_DbTbControle = 'CONTROLE'
        self.m_DbTbStrLog = 'BCIDADE_STR_LOG'
        self.m_DbTbBacenCidadeApp = 'BACEN_TO_BCIDADE_APP'
        self.m_DbTbCidadeBacenApp = 'BCIDADE_TO_BACEN_APP'

        # Connection string (built from above)
        self.m_ConnStr = ''

        # [MQSeries]
        self.m_MQServer = 'localhost'
        self.m_QueueManager = 'QM.36266751.01'
        self.m_QueueTimeout = 30

        # Bacen Local Queues
        self.m_MqQlBacenCidadeReq = 'QL.REQ.00038166.36266751.01'
        self.m_MqQlBacenCidadeRsp = 'QL.RSP.00038166.36266751.01'
        self.m_MqQlBacenCidadeRep = 'QL.REP.00038166.36266751.01'
        self.m_MqQlBacenCidadeSup = 'QL.SUP.00038166.36266751.01'

        # Bacen Remote Queues
        self.m_MqQrCidadeBacenReq = 'QR.REQ.36266751.00038166.01'
        self.m_MqQrCidadeBacenRsp = 'QR.RSP.36266751.00038166.01'
        self.m_MqQrCidadeBacenRep = 'QR.REP.36266751.00038166.01'
        self.m_MqQrCidadeBacenSup = 'QR.SUP.36266751.00038166.01'

        # IF Local Queues
        self.m_MqQlIFCidadeReq = 'QL.36266751.01.ENTRADA.IF'
        self.m_MqQlIFCidadeRsp = 'QL.36266751.01.SAIDA.IF'
        self.m_MqQlIFCidadeRep = 'QL.36266751.01.REPORT.IF'
        self.m_MqQlIFCidadeSup = 'QL.36266751.01.SUPORTE.IF'

        # IF Remote Queues
        self.m_MqQrCidadeIFReq = 'QR.36266751.01.ENTRADA.IF'
        self.m_MqQrCidadeIFRsp = 'QR.36266751.01.SAIDA.IF'
        self.m_MqQrCidadeIFRep = 'QR.36266751.01.REPORT.IF'
        self.m_MqQrCidadeIFSup = 'QR.36266751.01.SUPORTE.IF'

        # MQ Channel/Connection for pymqi TCP client mode
        self.m_MQChannel = 'FINVEST.SVRCONN'
        self.m_MQConnInfo = 'localhost(1414)'

        # [E-Mail]
        self.m_ServerEmail = ''
        self.m_SenderEmail = ''
        self.m_SenderName = ''
        self.m_DestEmail = ''
        self.m_DestName = ''

        # [Security]
        self.m_UnicodeEnable = 'S'
        self.m_SecurityEnable = 'N'
        self.m_SecurityDB = 'Public Keys'
        self.m_CertificateFile = ''
        self.m_PrivateKeyFile = ''
        self.m_PublicKeyLabel = ''
        self.m_PrivateKeyLabel = ''
        self.m_KeyPassword = ''

    # Aliases used by thread modules
    @property
    def m_QueueMgr(self):
        return self.m_QueueManager

    @property
    def m_DBUser(self):
        return self.m_DBUserName

    def on_init(self) -> bool:
        return True

    def run(self):
        """Main service entry point (replaces CInitSrv::Run)."""
        # 1. Determine INI path
        if not self.m_ARQINI:
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            self.m_ARQINI = os.path.join(exe_dir, 'BCSrvSqlMq.ini')

        # 2. Load configuration
        needs_write = self.get_key_all()

        # 3. Write defaults back if needed
        if needs_write:
            self.set_key_all()

        # 4. Create directories
        os.makedirs(self.m_DirTraces, exist_ok=True)
        os.makedirs(self.m_DirAudFile, exist_ok=True)

        # 5. Initialize logging
        self.m_OpenLog(self.m_DirTraces, 'TRACE_SPB_', self.m_MQServer)

        # Set trace level
        if self.m_TraceLevel == 'D':
            self.m_Trace(2)
        elif self.m_TraceLevel == 'S':
            self.m_Trace(1)
        else:
            self.m_Trace(0)

        self.m_WriteLog(self.m_szServiceName, 8014, False, 'Service starting')

        # 6. Initialize OpenSSL
        if self.m_SecurityEnable != 'N':
            init_crypto()

        # 7. Create MainSrv and start tasks
        from bcsrvsqlmq.main_srv import CMainSrv
        self.pMainSrv = CMainSrv()
        self.pMainSrv.pInitSrv = self

        if self.pMainSrv.prepara_tasks(self):
            self.set_status(SERVICE_RUNNING)
            self.m_WriteLog(self.m_szServiceName, 8014, False, 'Service running')

            # 8. Block on main event loop
            self.pMainSrv.wait_tasks()

        # 9. Cleanup
        self.m_WriteLog(self.m_szServiceName, 8012, False, 'Service stopping')

        if self.m_SecurityEnable != 'N':
            cleanup_crypto()

        self.m_CloseLog()

    def on_stop(self):
        """Handle service stop request."""
        if self.pMainSrv:
            self.pMainSrv.m_event_stop.set()

    def on_pause(self):
        if self.pMainSrv:
            self.pMainSrv.m_event_pause.set()

    def on_continue(self):
        if self.pMainSrv:
            self.pMainSrv.m_event_continue.set()

    def on_shutdown(self):
        self.m_bIsShutDownNow = True
        self.on_stop()

    def get_key_all(self) -> bool:
        """Load all INI configuration (replaces GetKeyAll).

        Returns True if any keys were missing and defaults were used.
        """
        config = configparser.ConfigParser()
        config.read(self.m_ARQINI, encoding='latin-1')

        missing = False

        def get_str(section, key, default):
            nonlocal missing
            if config.has_option(section, key):
                return config.get(section, key)
            missing = True
            return default

        def get_int(section, key, default):
            nonlocal missing
            if config.has_option(section, key):
                try:
                    return config.getint(section, key)
                except ValueError:
                    return default
            missing = True
            return default

        # [Servico]
        self.m_TraceLevel = get_str('Servico', 'Trace', 'N')
        self.m_MonitorPort = get_int('Servico', 'MonitorPort', 14499)
        self.m_SrvTimeout = get_int('Servico', 'SrvTimeout', 120)
        self.m_MaxLenMsg = get_int('Servico', 'MaxLenMsg', 1000)

        # [Diretorios]
        self.m_DirTraces = get_str('Diretorios', 'DirTraces', 'C:\\BCSRVSQLMQ\\Traces')
        self.m_DirAudFile = get_str('Diretorios', 'DirAudFile', 'C:\\BCSRVSQLMQ\\AuditFiles')

        # [DataBase]
        self.m_DBServer = get_str('DataBase', 'DBServer', platform.node())
        self.m_DBAliasName = get_str('DataBase', 'DBAliasName', 'banuxSPB')
        self.m_DBName = get_str('DataBase', 'DBName', 'banuxSPB')
        self.m_DBPort = get_int('DataBase', 'DBPort', 5432)
        self.m_DBUserName = get_str('DataBase', 'DBUserName', 'postgres')
        self.m_DBPassword = get_str('DataBase', 'DBPassword', '')
        self.m_DbTbControle = get_str('DataBase', 'DbTbControle', 'CONTROLE')
        self.m_DbTbStrLog = get_str('DataBase', 'DbTbStrLog', 'BCIDADE_STR_LOG')
        self.m_DbTbBacenCidadeApp = get_str('DataBase', 'DbTbBacenCidadeApp',
                                             'BACEN_TO_BCIDADE_APP')
        self.m_DbTbCidadeBacenApp = get_str('DataBase', 'DbTbCidadeBacenApp',
                                             'BCIDADE_TO_BACEN_APP')

        # Build PostgreSQL connection string
        self.m_ConnStr = (
            f'DRIVER={{PostgreSQL Unicode}};'
            f'SERVER={self.m_DBServer};'
            f'PORT={self.m_DBPort};'
            f'DATABASE={self.m_DBAliasName};'
            f'UID={self.m_DBUserName};'
            f'PWD={self.m_DBPassword};'
        )

        # [MQSeries]
        self.m_MQServer = get_str('MQSeries', 'MQServer', 'localhost')
        self.m_QueueManager = get_str('MQSeries', 'QueueManager', 'QM.36266751.01')
        self.m_QueueTimeout = get_int('MQSeries', 'QueueTimeout', 30)
        self.m_MQChannel = get_str('MQSeries', 'Channel', 'FINVEST.SVRCONN')
        self.m_MQConnInfo = get_str('MQSeries', 'ConnInfo', 'localhost(1414)')

        # Bacen Local Queues
        self.m_MqQlBacenCidadeReq = get_str('MQSeries', 'QLBacenCidadeReq',
                                              'QL.REQ.00038166.36266751.01')
        self.m_MqQlBacenCidadeRsp = get_str('MQSeries', 'QLBacenCidadeRsp',
                                              'QL.RSP.00038166.36266751.01')
        self.m_MqQlBacenCidadeRep = get_str('MQSeries', 'QLBacenCidadeRep',
                                              'QL.REP.00038166.36266751.01')
        self.m_MqQlBacenCidadeSup = get_str('MQSeries', 'QLBacenCidadeSup',
                                              'QL.SUP.00038166.36266751.01')

        # Bacen Remote Queues
        self.m_MqQrCidadeBacenReq = get_str('MQSeries', 'QRCidadeBacenReq',
                                              'QR.REQ.36266751.00038166.01')
        self.m_MqQrCidadeBacenRsp = get_str('MQSeries', 'QRCidadeBacenRsp',
                                              'QR.RSP.36266751.00038166.01')
        self.m_MqQrCidadeBacenRep = get_str('MQSeries', 'QRCidadeBacenRep',
                                              'QR.REP.36266751.00038166.01')
        self.m_MqQrCidadeBacenSup = get_str('MQSeries', 'QRCidadeBacenSup',
                                              'QR.SUP.36266751.00038166.01')

        # IF Local Queues
        self.m_MqQlIFCidadeReq = get_str('MQSeries', 'QLIFCidadeReq',
                                           'QL.36266751.01.ENTRADA.IF')
        self.m_MqQlIFCidadeRsp = get_str('MQSeries', 'QLIFCidadeRsp',
                                           'QL.36266751.01.SAIDA.IF')
        self.m_MqQlIFCidadeRep = get_str('MQSeries', 'QLIFCidadeRep',
                                           'QL.36266751.01.REPORT.IF')
        self.m_MqQlIFCidadeSup = get_str('MQSeries', 'QLIFCidadeSup',
                                           'QL.36266751.01.SUPORTE.IF')

        # IF Remote Queues
        self.m_MqQrCidadeIFReq = get_str('MQSeries', 'QRCidadeIFReq',
                                           'QR.36266751.01.ENTRADA.IF')
        self.m_MqQrCidadeIFRsp = get_str('MQSeries', 'QRCidadeIFRsp',
                                           'QR.36266751.01.SAIDA.IF')
        self.m_MqQrCidadeIFRep = get_str('MQSeries', 'QRCidadeIFRep',
                                           'QR.36266751.01.REPORT.IF')
        self.m_MqQrCidadeIFSup = get_str('MQSeries', 'QRCidadeIFSup',
                                           'QR.36266751.01.SUPORTE.IF')

        # [E-Mail]
        self.m_ServerEmail = get_str('E-Mail', 'ServerEmail', '')
        self.m_SenderEmail = get_str('E-Mail', 'SenderEmail', '')
        self.m_SenderName = get_str('E-Mail', 'SenderName', '')
        self.m_DestEmail = get_str('E-Mail', 'DestEmail', '')
        self.m_DestName = get_str('E-Mail', 'DestName', '')

        # [Security]
        self.m_UnicodeEnable = get_str('Security', 'UnicodeEnable', 'S')
        self.m_SecurityEnable = get_str('Security', 'SecurityEnable', 'N')
        self.m_SecurityDB = get_str('Security', 'SecurityDB', 'Public Keys')
        self.m_CertificateFile = get_str('Security', 'CertificateFile', '')
        self.m_PrivateKeyFile = get_str('Security', 'PrivateKeyFile', '')
        self.m_PublicKeyLabel = get_str('Security', 'PublicKeyLabel', '')
        self.m_PrivateKeyLabel = get_str('Security', 'PrivateKeyLabel', '')
        self.m_KeyPassword = get_str('Security', 'KeyPassword', '')

        return missing

    def set_key_all(self):
        """Write configuration back to INI file (replaces SetKeyAll)."""
        config = configparser.ConfigParser()

        # Preserve existing entries
        config.read(self.m_ARQINI, encoding='latin-1')

        def set_val(section, key, val):
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, key, str(val))

        # [Servico]
        set_val('Servico', 'ServiceName', self.m_ServiceName)
        set_val('Servico', 'Trace', self.m_TraceLevel)
        set_val('Servico', 'MonitorPort', self.m_MonitorPort)
        set_val('Servico', 'SrvTimeout', self.m_SrvTimeout)
        set_val('Servico', 'MaxLenMsg', self.m_MaxLenMsg)

        # [Diretorios]
        set_val('Diretorios', 'DirTraces', self.m_DirTraces)
        set_val('Diretorios', 'DirAudFile', self.m_DirAudFile)

        # [DataBase]
        set_val('DataBase', 'DBServer', self.m_DBServer)
        set_val('DataBase', 'DBAliasName', self.m_DBAliasName)
        set_val('DataBase', 'DBName', self.m_DBName)
        set_val('DataBase', 'DBPort', self.m_DBPort)
        set_val('DataBase', 'DBUserName', self.m_DBUserName)
        set_val('DataBase', 'DBPassword', self.m_DBPassword)
        set_val('DataBase', 'DbTbControle', self.m_DbTbControle)
        set_val('DataBase', 'DbTbStrLog', self.m_DbTbStrLog)
        set_val('DataBase', 'DbTbBacenCidadeApp', self.m_DbTbBacenCidadeApp)
        set_val('DataBase', 'DbTbCidadeBacenApp', self.m_DbTbCidadeBacenApp)

        # [MQSeries]
        set_val('MQSeries', 'MQServer', self.m_MQServer)
        set_val('MQSeries', 'QueueManager', self.m_QueueManager)
        set_val('MQSeries', 'QueueTimeout', self.m_QueueTimeout)
        set_val('MQSeries', 'QLBacenCidadeReq', self.m_MqQlBacenCidadeReq)
        set_val('MQSeries', 'QLBacenCidadeRsp', self.m_MqQlBacenCidadeRsp)
        set_val('MQSeries', 'QLBacenCidadeRep', self.m_MqQlBacenCidadeRep)
        set_val('MQSeries', 'QLBacenCidadeSup', self.m_MqQlBacenCidadeSup)
        set_val('MQSeries', 'QRCidadeBacenReq', self.m_MqQrCidadeBacenReq)
        set_val('MQSeries', 'QRCidadeBacenRsp', self.m_MqQrCidadeBacenRsp)
        set_val('MQSeries', 'QRCidadeBacenRep', self.m_MqQrCidadeBacenRep)
        set_val('MQSeries', 'QRCidadeBacenSup', self.m_MqQrCidadeBacenSup)
        set_val('MQSeries', 'QLIFCidadeReq', self.m_MqQlIFCidadeReq)
        set_val('MQSeries', 'QLIFCidadeRsp', self.m_MqQlIFCidadeRsp)
        set_val('MQSeries', 'QLIFCidadeRep', self.m_MqQlIFCidadeRep)
        set_val('MQSeries', 'QLIFCidadeSup', self.m_MqQlIFCidadeSup)
        set_val('MQSeries', 'QRCidadeIFReq', self.m_MqQrCidadeIFReq)
        set_val('MQSeries', 'QRCidadeIFRsp', self.m_MqQrCidadeIFRsp)
        set_val('MQSeries', 'QRCidadeIFRep', self.m_MqQrCidadeIFRep)
        set_val('MQSeries', 'QRCidadeIFSup', self.m_MqQrCidadeIFSup)

        # [Security]
        set_val('Security', 'UnicodeEnable', self.m_UnicodeEnable)
        set_val('Security', 'SecurityEnable', self.m_SecurityEnable)
        set_val('Security', 'CertificateFile', self.m_CertificateFile)
        set_val('Security', 'PrivateKeyFile', self.m_PrivateKeyFile)
        set_val('Security', 'PublicKeyLabel', self.m_PublicKeyLabel)
        set_val('Security', 'PrivateKeyLabel', self.m_PrivateKeyLabel)

        try:
            with open(self.m_ARQINI, 'w', encoding='latin-1') as f:
                config.write(f)
        except Exception:
            pass
