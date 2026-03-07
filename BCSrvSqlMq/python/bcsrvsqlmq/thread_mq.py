# thread_mq.py - Base worker thread class (port of ThreadMQ.cpp/h)

import threading
import time
import struct
import traceback
from lxml import etree

import pymqi
import pymqi.CMQC

from bcsrvsqlmq.msg_sgr import (
    COMHDR, SECHDR, SECHDR_SIZE, SECHDR_V1_SIZE, MAXMSGLENGTH,
    TASKS_COUNT, FUNC_POST, FUNC_NOP,
    ALG_RSA_1024, ALG_RSA_2048, ALG_3DES_168,
    ALG_HASH_MD5, ALG_HASH_SHA1, ALG_HASH_SHA256,
    SECHDR_VERSION_CLEAR, SECHDR_VERSION_V1, SECHDR_VERSION_V2,
)
from bcsrvsqlmq.security.openssl_wrapper import (
    CryptoContext, DigitalSignature, SymmetricCrypto,
)


def connect_qmgr(queue_manager: str, channel: str, conn_info: str) -> pymqi.QueueManager:
    """Connect to queue manager via TCP client channel (pymqi uses mqic.dll).

    Args:
        queue_manager: Queue manager name, e.g. 'QM.36266751.01'
        channel: SVRCONN channel name, e.g. 'FINVEST.SVRCONN'
        conn_info: Connection info, e.g. 'localhost(1414)'
    """
    cd = pymqi.CD()
    cd.ChannelName = channel.encode()
    cd.ConnectionName = conn_info.encode()
    cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
    cd.TransportType = pymqi.CMQC.MQXPT_TCP
    qm = pymqi.QueueManager(None)
    qm.connect_with_options(queue_manager, cd)
    return qm


# Thread event indices (matches ThreadEvent namespace in C++)
THREAD_EVENT_TIMER = 0
THREAD_EVENT_STOP = 1
THREAD_EVENT_POST = 2
QTD_THREAD_EVENTS = 3


class CThreadMQ:
    """Base class for all 8 worker threads (port of CThreadMQ).

    Subclasses override processa_queue() with their business logic.
    """

    def __init__(self, name: str = '', automatic_thread: bool = True,
                 handle_mq: int = 0, main_srv=None):
        self.m_ServiceName = name
        self.m_HandleMQ = handle_mq
        self.m_AutomaticThread = automatic_thread
        self.pMainSrv = main_srv

        # Thread management
        self.m_thread = None
        self.m_threadId = None
        self.m_mutex = threading.Lock()

        # Thread state (atomic in C++, GIL-protected in Python)
        self.m_ServicoIsRunning = False
        self.m_ThreadIsRunning = False

        # Events (replacing Win32 HANDLE events)
        self.m_event_stop = threading.Event()
        self.m_event_post = threading.Event()
        self.m_event_timer = threading.Event()

        # Task identification
        self.m_szTaskName = name[:40] if name else ''
        self.m_szQueueName = ''
        self.m_lpTaskName = self.m_szTaskName

        # Timer configuration
        self.lPeriod = 1000  # 1 second timer period (ms)

        # OpenSSL Cryptography
        self.m_publicKey = None
        self.m_privateKey = None
        self.m_certificate = None
        self.m_cryptSerialNumberPrv = b'\x00' * 32
        self.m_cryptSerialNumberPub = b'\x00' * 32

        # Crypto context
        self._crypto_ctx = CryptoContext()

        # XML document
        self.m_xmlDoc = None

    # ------------------------------------------------------------------
    # Static thread entry point
    # ------------------------------------------------------------------
    @staticmethod
    def task_thread(main_srv_ref, thread_mq_ref):
        """Static thread entry point (replaces C++ TaskThread callback)."""
        try:
            thread_mq_ref.run_thread(main_srv_ref)
        except Exception as e:
            if main_srv_ref and hasattr(main_srv_ref, 'pInitSrv'):
                try:
                    tb = traceback.format_exc()
                    main_srv_ref.pInitSrv.m_WriteLog(
                        thread_mq_ref.m_szTaskName, 8099, True,
                        f'{e}\n{tb}')
                except Exception:
                    pass
        finally:
            if main_srv_ref and hasattr(main_srv_ref, 'm_StopList'):
                main_srv_ref.m_StopList.add(thread_mq_ref)
                main_srv_ref.m_event_tasksapp_stop.set()

    # ------------------------------------------------------------------
    # Thread lifecycle
    # ------------------------------------------------------------------
    def run_thread(self, main_srv):
        """Template method: init -> wait -> term."""
        self.run_init()
        self.run_wait_post()
        self.run_term()

    def run_init(self):
        """Initialize thread state and queue name buffer."""
        self.m_ServicoIsRunning = True
        self.m_ThreadIsRunning = True

        # Pad queue name to 48 chars (matches C++ memset to 0x20)
        self.m_szQueueName = self.m_szQueueName.ljust(48)

        if self.pMainSrv and self.pMainSrv.MainIsStoping:
            self.m_event_stop.set()
        else:
            self.m_event_post.set()

    def run_wait(self):
        """Wait loop with non-blocking event check (used by some tasks)."""
        while self.m_ServicoIsRunning:
            if self.m_event_stop.is_set():
                self.m_event_stop.clear()
                self.m_ServicoIsRunning = False
                break

            if self.m_event_post.is_set():
                self.m_event_post.clear()
                with self.m_mutex:
                    self.processa_queue()

            time.sleep(self.lPeriod / 1000.0)

    def run_wait_post(self):
        """Wait loop blocking on events (primary event loop)."""
        while self.m_ServicoIsRunning:
            # Check stop first
            if self.m_event_stop.wait(timeout=0.1):
                self.m_event_stop.clear()
                self.m_ServicoIsRunning = False
                break

            # Check post
            if self.m_event_post.is_set():
                self.m_event_post.clear()
                with self.m_mutex:
                    self.processa_queue()
                # Re-post to continue processing
                if self.m_ServicoIsRunning:
                    self.m_event_post.set()

    def run_term(self):
        """Cleanup thread resources."""
        self.m_ThreadIsRunning = False
        self._crypto_ctx.cleanup()

    def processa_queue(self):
        """Process message queue - override in subclass."""
        time.sleep(15)

    # ------------------------------------------------------------------
    # Lock/Unlock
    # ------------------------------------------------------------------
    def lock(self) -> bool:
        self.m_mutex.acquire()
        return True

    def unlock(self) -> bool:
        self.m_mutex.release()
        return True

    # ------------------------------------------------------------------
    # Status update
    # ------------------------------------------------------------------
    def atualiza_status(self):
        """Update task status in main server status array."""
        if self.pMainSrv and hasattr(self.pMainSrv, 'm_StatusTask'):
            idx = self.m_HandleMQ
            if 0 <= idx < TASKS_COUNT:
                status = self.pMainSrv.m_StatusTask[idx]
                status.bTaskNum = self.m_HandleMQ
                status.bTaskName = self.m_szTaskName[:10].encode('latin-1').ljust(10)
                status.iTaskAutomatic = 1 if self.m_AutomaticThread else 0
                status.iTaskIsRunning = 1 if self.m_ThreadIsRunning else 0

    # ------------------------------------------------------------------
    # MQ message header dump
    # ------------------------------------------------------------------
    def dump_header(self, mqmd_dict: dict):
        """Log all MQ message descriptor fields."""
        if not self.pMainSrv or not hasattr(self.pMainSrv, 'pInitSrv'):
            return
        write_log = self.pMainSrv.pInitSrv.m_WriteLog
        task = self.m_szTaskName

        for key, value in mqmd_dict.items():
            if isinstance(value, bytes):
                hex_str = ' '.join(f'{b:02X}' for b in value[:48])
                write_log(task, 8070, False, f'{key}={hex_str}')
            else:
                write_log(task, 8070, False, f'{key}={value}')

    # ------------------------------------------------------------------
    # Character encoding conversion
    # ------------------------------------------------------------------
    @staticmethod
    def ansi_to_unicode(data: bytes) -> bytes:
        """Convert ANSI (Latin-1) to UTF-16LE."""
        return data.decode('latin-1').encode('utf-16-le')

    @staticmethod
    def unicode_to_ansi(data: bytes) -> bytes:
        """Convert UTF-16LE to ANSI (Latin-1)."""
        return data.decode('utf-16-le').encode('latin-1')

    # ------------------------------------------------------------------
    # Cryptography: Key loading
    # ------------------------------------------------------------------
    def read_public_key(self) -> int:
        """Load X.509 certificate and extract public key."""
        if not hasattr(self.pMainSrv, 'pInitSrv'):
            return -1
        init_srv = self.pMainSrv.pInitSrv

        if init_srv.m_SecurityEnable == 'N':
            return 0

        cert_path = init_srv.m_CertificateFile
        if not self._crypto_ctx.load_public_key_from_certificate(cert_path):
            write_log = init_srv.m_WriteLog
            write_log(self.m_szTaskName, 8018, True,
                      f'Error loading certificate: {self._crypto_ctx.get_last_error()}')
            return -1

        self.m_publicKey = self._crypto_ctx.m_publicKey
        self.m_certificate = self._crypto_ctx.m_certificate

        # Extract serial number from certificate
        if self.m_certificate:
            serial = self.m_certificate.serial_number
            serial_bytes = serial.to_bytes(32, byteorder='big')
            self.m_cryptSerialNumberPub = serial_bytes[-32:]

        return 0

    def read_private_key(self) -> int:
        """Load RSA private key from PEM file."""
        if not hasattr(self.pMainSrv, 'pInitSrv'):
            return -1
        init_srv = self.pMainSrv.pInitSrv

        if init_srv.m_SecurityEnable == 'N':
            return 0

        key_path = init_srv.m_PrivateKeyFile
        password = init_srv.m_KeyPassword if init_srv.m_KeyPassword else None

        if not self._crypto_ctx.load_private_key(key_path, password):
            write_log = init_srv.m_WriteLog
            write_log(self.m_szTaskName, 8018, True,
                      f'Error loading private key: {self._crypto_ctx.get_last_error()}')
            return -1

        self.m_privateKey = self._crypto_ctx.m_privateKey

        # Use certificate serial for private key ID
        if self.m_cryptSerialNumberPub != b'\x00' * 32:
            self.m_cryptSerialNumberPrv = self.m_cryptSerialNumberPub

        return 0

    # ------------------------------------------------------------------
    # Cryptography: Digital signature
    # ------------------------------------------------------------------
    def _rsa_size(self) -> int:
        """Return RSA output size based on loaded key (128 for 1024-bit, 256 for 2048-bit)."""
        if self.m_publicKey is not None:
            return self.m_publicKey.key_size // 8
        if self.m_privateKey is not None:
            return self.m_privateKey.key_size // 8
        return 256  # default to RSA-2048

    def func_assinar(self, sec_header: SECHDR, data: bytes) -> tuple:
        """Create digital signature using PKCS#1 v1.5.

        Returns: (status_code, signed_data)
        """
        if self.m_privateKey is None:
            return -1, data

        digest_algo = sec_header.AlgHash

        # Pad data to 8-byte alignment (3DES block size)
        pad_len = (8 - (len(data) % 8)) % 8
        padded_data = data + b'\x00' * pad_len

        signature, sig_len = DigitalSignature.create_signature(
            padded_data, self.m_privateKey, digest_algo)

        if signature is None:
            return -1, data

        # Store signature in C14 HashCifrSign (256 bytes in V2)
        sec_header.HashCifrSign = signature[:256].ljust(256, b'\x00')
        sec_header.NumSerieCertLocal = self.m_cryptSerialNumberPrv[:32]

        return 0, padded_data

    def func_verify_ass(self, sec_header: SECHDR, data: bytes) -> int:
        """Verify digital signature using PKCS#1 v1.5.

        Returns: 0 on success, error code on failure
        """
        if self.m_publicKey is None:
            return -1

        # Verify certificate serial
        if sec_header.NumSerieCertLocal != self.m_cryptSerialNumberPub:
            sec_header.CodErro = 0x10  # Serial mismatch
            return 0x10

        # Extract signature - strip trailing padding zeros
        rsa_size = self._rsa_size()
        signature = sec_header.HashCifrSign[:rsa_size]

        digest_algo = sec_header.AlgHash

        if DigitalSignature.verify_signature(data, signature, self.m_publicKey, digest_algo):
            return 0
        else:
            sec_header.CodErro = 0x05  # Bad signature
            return 0x05

    # ------------------------------------------------------------------
    # Cryptography: Encryption/Decryption
    # ------------------------------------------------------------------
    def func_cript(self, sec_header: SECHDR, data: bytes) -> tuple:
        """Encrypt with 3DES+RSA PKCS#1 v1.5 key wrap.

        Returns: (status_code, encrypted_data)
        """
        if self.m_publicKey is None:
            return -1, data

        # Generate random 3DES key; IV is always zero (matches C++ / SPB spec)
        des3_key = SymmetricCrypto.generate_3des_key()
        iv = b'\x00' * 8

        # Wrap 3DES key with RSA public key
        try:
            encrypted_key = SymmetricCrypto.wrap_key_rsa(des3_key, self.m_publicKey)
        except Exception:
            return -1, data

        # Store encrypted key in C14 SymKeyCifr (256 bytes in V2)
        sec_header.SymKeyCifr = encrypted_key[:256].ljust(256, b'\x00')

        # Pad data to 8-byte alignment (3DES block size)
        pad_len = (8 - (len(data) % 8)) % 8
        padded_data = data + b'\x00' * pad_len

        # Encrypt with 3DES-CBC
        try:
            encrypted_data = SymmetricCrypto.encrypt_3des(padded_data, des3_key, iv)
        except Exception:
            return -1, data

        sec_header.NumSerieCertDest = self.m_cryptSerialNumberPub[:32]

        return 0, encrypted_data

    def func_de_cript(self, sec_header: SECHDR, data: bytes) -> tuple:
        """Decrypt 3DES+RSA PKCS#1 v1.5 key unwrap.

        Returns: (status_code, decrypted_data)
        """
        if self.m_privateKey is None:
            return -1, data

        # Validate algorithm
        if sec_header.AlgSymKey != ALG_3DES_168:
            sec_header.CodErro = 0x04
            return 0x04, data

        # Verify destination serial
        if sec_header.NumSerieCertDest != self.m_cryptSerialNumberPrv:
            sec_header.CodErro = 0x08
            return 0x08, data

        # Extract RSA-wrapped key - use actual RSA size (no rstrip needed)
        rsa_size = self._rsa_size()
        encrypted_key = sec_header.SymKeyCifr[:rsa_size]
        try:
            des3_key = SymmetricCrypto.unwrap_key_rsa(encrypted_key, self.m_privateKey)
        except Exception:
            sec_header.CodErro = 0x03
            return 0x03, data

        # Decrypt with 3DES-CBC (zero IV as in original C++)
        iv = b'\x00' * 8
        try:
            decrypted_data = SymmetricCrypto.decrypt_3des(data, des3_key, iv)
        except Exception:
            sec_header.CodErro = 0x03
            return 0x03, data

        return 0, decrypted_data

    def func_log(self, sec_header: SECHDR, data: bytes) -> int:
        """Logging stub (replaces funcLog)."""
        return 0

    def func_str_log(self, sec_header: SECHDR, data: bytes) -> int:
        """String logging stub (replaces funcStrLog)."""
        return 0

    # ------------------------------------------------------------------
    # XML Processing (lxml replaces pugixml)
    # ------------------------------------------------------------------
    @staticmethod
    def report_error(result, error_msg: str = ''):
        """Report XML parsing error."""
        return False

    @staticmethod
    def check_load(doc) -> bool:
        """Check if XML document loaded successfully."""
        return doc is not None

    @staticmethod
    def load_document_sync(data: bytes) -> etree._Element:
        """Load XML from byte buffer."""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            return etree.fromstring(data)
        except etree.XMLSyntaxError:
            return None

    @staticmethod
    def save_document(doc, filename: str) -> bool:
        """Save XML document to file."""
        try:
            tree = etree.ElementTree(doc)
            tree.write(filename, xml_declaration=True, encoding='UTF-8', pretty_print=True)
            return True
        except Exception:
            return False

    @staticmethod
    def find_tag(doc, parent_name: str, tag_name: str) -> str:
        """Find XML tag value (replaces FindTag with XPath)."""
        if doc is None:
            return None
        try:
            if parent_name:
                nodes = doc.xpath(f'//{parent_name}/{tag_name}')
            else:
                nodes = doc.xpath(f'//{tag_name}')
            if nodes:
                return nodes[0].text
        except Exception:
            pass
        return None

    @staticmethod
    def set_tag(doc, tag_name: str, value: str) -> bool:
        """Set XML tag value (replaces SetTag with XPath)."""
        if doc is None:
            return False
        try:
            nodes = doc.xpath(f'//{tag_name}')
            if len(nodes) == 1:
                nodes[0].text = value
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def walk_tree(node, level: int = 0) -> bool:
        """Recursively walk XML tree for debugging."""
        if node is None:
            return False
        indent = '  ' * level
        print(f'{indent}<{node.tag}>')
        if node.text and node.text.strip():
            print(f'{indent}  {node.text.strip()}')
        for child in node:
            CThreadMQ.walk_tree(child, level + 1)
        return True
