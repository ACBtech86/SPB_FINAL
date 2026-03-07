# test_smoke.py - End-to-end smoke test
# Verifies that all modules can be imported and basic wiring works.

import pytest


class TestImportSmoke:
    """Verify all package modules import cleanly."""

    def test_import_package(self):
        import bcsrvsqlmq

    def test_import_msg_sgr(self):
        from bcsrvsqlmq.msg_sgr import COMHDR, SECHDR, STAUDITFILE, STTASKSTATUS, MIMSG

    def test_import_nt_servmsg(self):
        from bcsrvsqlmq.nt_servmsg import (
            EVMSG_INSTALLED, EVMSG_REMOVED, EVMSG_STARTED, EVMSG_STOPPED,
        )

    def test_import_logging_module(self):
        from bcsrvsqlmq.logging_module import LoggingModule

    def test_import_openssl_wrapper(self):
        from bcsrvsqlmq.security.openssl_wrapper import (
            CryptoContext, DigitalSignature, SymmetricCrypto,
        )

    def test_import_thread_mq(self):
        from bcsrvsqlmq.thread_mq import CThreadMQ

    def test_import_main_srv(self):
        from bcsrvsqlmq.main_srv import CMainSrv, CQueueList, CClientItem

    def test_import_monitor(self):
        from bcsrvsqlmq.monitor import CMonitor

    def test_import_bacen_tasks(self):
        try:
            from bcsrvsqlmq.bacen_req import CBacenReq
            from bcsrvsqlmq.bacen_rsp import CBacenRsp
            from bcsrvsqlmq.bacen_rep import CBacenRep
            from bcsrvsqlmq.bacen_sup import CBacenSup
        except ImportError as e:
            if 'pymqi' in str(e):
                pytest.skip('pymqi not installed (requires IBM MQ client)')
            raise

    def test_import_if_tasks(self):
        try:
            from bcsrvsqlmq.if_req import CIFReq
            from bcsrvsqlmq.if_rsp import CIFRsp
            from bcsrvsqlmq.if_rep import CIFRep
            from bcsrvsqlmq.if_sup import CIFSup
        except ImportError as e:
            if 'pymqi' in str(e):
                pytest.skip('pymqi not installed (requires IBM MQ client)')
            raise

    def test_import_db_layer(self):
        from bcsrvsqlmq.db.bc_database import CBCDatabase
        from bcsrvsqlmq.db.bacen_app_rs import CBacenAppRS
        from bcsrvsqlmq.db.if_app_rs import CIFAppRS
        from bcsrvsqlmq.db.str_log_rs import CSTRLogRS
        from bcsrvsqlmq.db.controle_rs import CControleRS

    def test_import_init_srv(self):
        try:
            from bcsrvsqlmq.init_srv import CInitSrv
        except ImportError as e:
            if 'win32' in str(e).lower():
                pytest.skip('pywin32 not installed')
            raise


class TestWiringSmoke:
    """Verify basic object creation and wiring."""

    def test_create_comhdr(self):
        from bcsrvsqlmq.msg_sgr import COMHDR, FUNC_POST
        hdr = COMHDR(usMsgLength=11, ucFuncSgr=FUNC_POST)
        packed = hdr.pack()
        assert len(packed) == 11

    def test_create_sechdr(self):
        from bcsrvsqlmq.msg_sgr import SECHDR, SECHDR_SIZE
        sec = SECHDR(Versao=1, AlgHash=2)
        packed = sec.pack()
        assert len(packed) == SECHDR_SIZE

    def test_create_thread_mq(self):
        from bcsrvsqlmq.thread_mq import CThreadMQ
        t = CThreadMQ(name='SmokeTest', automatic_thread=True, handle_mq=1)
        assert t.m_szTaskName == 'SmokeTest'

    def test_create_main_srv(self):
        from bcsrvsqlmq.main_srv import CMainSrv
        srv = CMainSrv()
        assert srv.m_TaskList.get_size() == 0

    def test_create_logging_module(self, tmp_path):
        from bcsrvsqlmq.logging_module import LoggingModule
        logger = LoggingModule()
        assert logger.open_log(str(tmp_path), 'SmokeTest')
        assert logger.write_log('Smoke', 1, False, 'test message')
        assert logger.close_log()

    def test_crypto_context(self, rsa_keypair):
        from bcsrvsqlmq.security.openssl_wrapper import CryptoContext
        key_path, cert_path, _, _ = rsa_keypair
        ctx = CryptoContext()
        assert ctx.load_public_key_from_certificate(cert_path)
        assert ctx.load_private_key(key_path)
        assert ctx.get_key_size() == 2048
        ctx.cleanup()

    def test_xml_roundtrip(self):
        from bcsrvsqlmq.thread_mq import CThreadMQ
        xml = b'<DOC><BCMSG><IdentdEmissor>12345</IdentdEmissor></BCMSG></DOC>'
        doc = CThreadMQ.load_document_sync(xml)
        assert doc is not None
        val = CThreadMQ.find_tag(doc, 'BCMSG', 'IdentdEmissor')
        assert val == '12345'
        assert CThreadMQ.set_tag(doc, 'IdentdEmissor', '99999')
        assert CThreadMQ.find_tag(doc, 'BCMSG', 'IdentdEmissor') == '99999'

    def test_struct_pack_unpack_chain(self):
        """Test the full message pack/unpack chain: COMHDR -> MIMSG."""
        from bcsrvsqlmq.msg_sgr import COMHDR, MIMSG, COMHDR_SIZE, FUNC_POST

        hdr = COMHDR(
            usMsgLength=COMHDR_SIZE + 20,
            ucIdHeader=b'SPB1',
            ucFuncSgr=FUNC_POST,
            usRc=0,
            usDatLength=20,
        )
        msg = MIMSG(hdr=hdr)
        msg.mdata[:20] = b'PayloadData12345678\x00'

        packed = msg.pack()
        restored = MIMSG.unpack(packed)

        assert restored.hdr.ucIdHeader == b'SPB1'
        assert restored.hdr.ucFuncSgr == FUNC_POST
        assert restored.mdata[:19] == bytearray(b'PayloadData12345678')
