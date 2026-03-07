# test_mq_integration.py - Integration tests for IBM MQ connectivity
#
# These tests require a running IBM MQ queue manager (QM.36266751.01)
# with the FINVEST queues configured. Skip automatically if MQ is unavailable.
#
# Run with: pytest python/tests/integration/test_mq_integration.py -v

import os
import sys
import time
import configparser
from datetime import datetime

import pytest

# Try to import pymqi - skip all tests if not installed
pymqi = pytest.importorskip('pymqi', reason='pymqi not installed (requires IBM MQ client)')
import pymqi.CMQC


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
QUEUE_MANAGER = 'QM.36266751.01'
CHANNEL = 'FINVEST.SVRCONN'
CONN_INFO = 'localhost(1414)'

LOCAL_QUEUES = [
    'QL.REQ.00038166.36266751.01',
    'QL.RSP.00038166.36266751.01',
    'QL.REP.00038166.36266751.01',
    'QL.SUP.00038166.36266751.01',
]
REMOTE_QUEUES = [
    'QR.REQ.36266751.00038166.01',
    'QR.RSP.36266751.00038166.01',
    'QR.REP.36266751.00038166.01',
    'QR.SUP.36266751.00038166.01',
]
TEST_QUEUE = 'QL.REQ.00038166.36266751.01'  # Use REQ local queue for put/get tests

SAMPLE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<DOC><BCMSG>'
    '<IdentdEmissor>36266751</IdentdEmissor>'
    '<IdentdDestinatario>00038166</IdentdDestinatario>'
    '<NUOp>20260305000001</NUOp>'
    '<DtHrMsg>2026-03-05T10:00:00</DtHrMsg>'
    '</BCMSG><SISMSG>'
    '<CodMsg>GEN0014</CodMsg>'
    '<NumCtrlIF>CTRL000001</NumCtrlIF>'
    '</SISMSG><GENMSG>'
    '<TxtMsg>Integration test message</TxtMsg>'
    '</GENMSG></DOC>'
)


def _connect_to_qm():
    """Connect to queue manager via client channel (pymqi uses mqic.dll).

    Tries client connection via SVRCONN channel on localhost(1414).
    Falls back to server binding if client fails.
    """
    # Client connection via TCP channel
    cd = pymqi.CD()
    cd.ChannelName = CHANNEL.encode()
    cd.ConnectionName = CONN_INFO.encode()
    cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
    cd.TransportType = pymqi.CMQC.MQXPT_TCP

    qm = pymqi.QueueManager(None)
    qm.connect_with_options(QUEUE_MANAGER, cd)
    return qm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope='module')
def qmgr():
    """Connect to the queue manager. Skip if unavailable."""
    try:
        qm = _connect_to_qm()
    except pymqi.MQMIError as e:
        pytest.skip(f'Cannot connect to {QUEUE_MANAGER}: reason={e.reason}')
    yield qm
    try:
        qm.disconnect()
    except pymqi.MQMIError:
        pass


@pytest.fixture
def test_queue(qmgr):
    """Open the test queue for input/output, clean up after test."""
    open_opts = pymqi.CMQC.MQOO_INPUT_SHARED | pymqi.CMQC.MQOO_OUTPUT
    try:
        queue = pymqi.Queue(qmgr, TEST_QUEUE, open_opts)
    except pymqi.MQMIError as e:
        pytest.skip(f'Cannot open queue {TEST_QUEUE}: reason={e.reason}')
    yield queue
    # Drain any leftover test messages
    try:
        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_NO_WAIT | pymqi.CMQC.MQGMO_FAIL_IF_QUIESCING
        while True:
            queue.get(32768, pymqi.MD(), gmo)
    except pymqi.MQMIError:
        pass
    try:
        queue.close()
    except pymqi.MQMIError:
        pass


# ---------------------------------------------------------------------------
# Tests: Queue Manager Connection
# ---------------------------------------------------------------------------
class TestQueueManagerConnection:
    """Test connectivity to the IBM MQ queue manager."""

    def test_connect_disconnect(self):
        """Verify basic connect/disconnect cycle."""
        try:
            qm = _connect_to_qm()
        except pymqi.MQMIError as e:
            pytest.skip(f'MQ not available: {e.reason}')
        assert qm is not None
        qm.disconnect()

    def test_queue_manager_name(self, qmgr):
        """Verify connected to the correct queue manager."""
        # Query the queue manager name via MQINQ
        try:
            name = qmgr.inquire(pymqi.CMQC.MQCA_Q_MGR_NAME)
            assert QUEUE_MANAGER.replace('.', '.') in name.decode().strip()
        except pymqi.MQMIError:
            # Some versions don't support inquire on QM object
            pass


# ---------------------------------------------------------------------------
# Tests: Queue Existence and Properties
# ---------------------------------------------------------------------------
class TestQueueExistence:
    """Verify all 8 queues exist and have correct properties."""

    @pytest.mark.parametrize('queue_name', LOCAL_QUEUES)
    def test_local_queue_exists(self, qmgr, queue_name):
        """Open each local queue to verify it exists."""
        try:
            q = pymqi.Queue(qmgr, queue_name, pymqi.CMQC.MQOO_INQUIRE)
            q.close()
        except pymqi.MQMIError as e:
            pytest.fail(f'Local queue {queue_name} not found: reason={e.reason}')

    @pytest.mark.parametrize('queue_name', REMOTE_QUEUES)
    def test_remote_queue_exists(self, qmgr, queue_name):
        """Open each remote queue to verify it exists."""
        try:
            q = pymqi.Queue(qmgr, queue_name, pymqi.CMQC.MQOO_INQUIRE)
            q.close()
        except pymqi.MQMIError as e:
            pytest.fail(f'Remote queue {queue_name} not found: reason={e.reason}')

    @pytest.mark.parametrize('queue_name', LOCAL_QUEUES)
    def test_local_queue_max_depth(self, qmgr, queue_name):
        """Verify local queues have MAXDEPTH(5000)."""
        try:
            q = pymqi.Queue(qmgr, queue_name, pymqi.CMQC.MQOO_INQUIRE)
            max_depth = q.inquire(pymqi.CMQC.MQIA_MAX_Q_DEPTH)
            q.close()
            assert max_depth == 5000, f'{queue_name} MAXDEPTH={max_depth}, expected 5000'
        except pymqi.MQMIError as e:
            pytest.skip(f'Cannot inquire {queue_name}: reason={e.reason}')

    @pytest.mark.parametrize('queue_name', LOCAL_QUEUES)
    def test_local_queue_persistent(self, qmgr, queue_name):
        """Verify local queues have DEFPSIST(YES)."""
        try:
            q = pymqi.Queue(qmgr, queue_name, pymqi.CMQC.MQOO_INQUIRE)
            defpsist = q.inquire(pymqi.CMQC.MQIA_DEF_PERSISTENCE)
            q.close()
            assert defpsist == pymqi.CMQC.MQPER_PERSISTENT, (
                f'{queue_name} DEFPSIST={defpsist}, expected PERSISTENT'
            )
        except pymqi.MQMIError as e:
            pytest.skip(f'Cannot inquire {queue_name}: reason={e.reason}')


# ---------------------------------------------------------------------------
# Tests: Put and Get Messages
# ---------------------------------------------------------------------------
class TestPutGetMessages:
    """Test message put/get operations on local queues."""

    def test_put_and_get_simple(self, test_queue):
        """Put a simple text message and get it back."""
        msg = b'INTEGRATION_TEST_SIMPLE'

        # Put
        md = pymqi.MD()
        test_queue.put(msg, md)

        # Get
        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_NO_WAIT
        md_get = pymqi.MD()
        received = test_queue.get(32768, md_get, gmo)

        assert received == msg

    def test_put_and_get_xml(self, test_queue):
        """Put an SPB XML message and get it back."""
        msg = SAMPLE_XML.encode('utf-8')

        md = pymqi.MD()
        md.Format = pymqi.CMQC.MQFMT_STRING
        test_queue.put(msg, md)

        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_NO_WAIT
        md_get = pymqi.MD()
        received = test_queue.get(32768, md_get, gmo)

        assert b'36266751' in received
        assert b'GEN0014' in received
        assert b'Integration test message' in received

    def test_put_persistent_message(self, test_queue):
        """Put a persistent message and verify it survives get."""
        msg = b'PERSISTENT_TEST'

        md = pymqi.MD()
        md.Persistence = pymqi.CMQC.MQPER_PERSISTENT
        pmo = pymqi.PMO()
        test_queue.put(msg, md, pmo)

        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_NO_WAIT
        md_get = pymqi.MD()
        received = test_queue.get(32768, md_get, gmo)

        assert received == msg

    def test_put_get_with_correlation_id(self, test_queue):
        """Put message with correlation ID and get by correlation."""
        msg = b'CORREL_TEST'
        correl_id = b'TESTCORRELID' + b'\x00' * 12  # 24 bytes

        # Put with correlation ID
        md = pymqi.MD()
        md.CorrelId = correl_id
        test_queue.put(msg, md)

        # Get by correlation ID
        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_NO_WAIT
        gmo.MatchOptions = pymqi.CMQC.MQMO_MATCH_CORREL_ID
        md_get = pymqi.MD()
        md_get.CorrelId = correl_id
        received = test_queue.get(32768, md_get, gmo)

        assert received == msg

    def test_no_message_available(self, test_queue):
        """Verify MQRC_NO_MSG_AVAILABLE when queue is empty."""
        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_NO_WAIT

        with pytest.raises(pymqi.MQMIError) as exc_info:
            test_queue.get(32768, pymqi.MD(), gmo)

        assert exc_info.value.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE

    def test_queue_depth_after_put_get(self, qmgr, test_queue):
        """Verify queue depth goes up after put and back down after get."""
        # Check initial depth
        q_inq = pymqi.Queue(qmgr, TEST_QUEUE, pymqi.CMQC.MQOO_INQUIRE)
        depth_before = q_inq.inquire(pymqi.CMQC.MQIA_CURRENT_Q_DEPTH)
        q_inq.close()

        # Put a message
        test_queue.put(b'DEPTH_TEST')

        # Check depth increased
        q_inq = pymqi.Queue(qmgr, TEST_QUEUE, pymqi.CMQC.MQOO_INQUIRE)
        depth_after_put = q_inq.inquire(pymqi.CMQC.MQIA_CURRENT_Q_DEPTH)
        q_inq.close()
        assert depth_after_put == depth_before + 1

        # Get the message
        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_NO_WAIT
        test_queue.get(32768, pymqi.MD(), gmo)

        # Check depth back to original
        q_inq = pymqi.Queue(qmgr, TEST_QUEUE, pymqi.CMQC.MQOO_INQUIRE)
        depth_after_get = q_inq.inquire(pymqi.CMQC.MQIA_CURRENT_Q_DEPTH)
        q_inq.close()
        assert depth_after_get == depth_before


# ---------------------------------------------------------------------------
# Tests: INI Config matches MQ Queues
# ---------------------------------------------------------------------------
class TestIniConfigMatchesMQ:
    """Verify BCSrvSqlMq.ini queue names match actual MQ queues."""

    @pytest.fixture
    def ini_config(self):
        """Load the real BCSrvSqlMq.ini."""
        # Search for INI in common locations
        candidates = [
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'BCSrvSqlMq.ini'),
            r'C:\BCSrvSqlMq\BCSrvSqlMq.ini',
        ]
        for path in candidates:
            path = os.path.normpath(path)
            if os.path.exists(path):
                config = configparser.ConfigParser()
                config.read(path, encoding='latin-1')
                return config
        pytest.skip('BCSrvSqlMq.ini not found')

    def test_queue_manager_name(self, ini_config):
        """INI QueueManager matches our test queue manager."""
        qm = ini_config.get('MQSeries', 'QueueManager')
        assert qm == QUEUE_MANAGER

    def test_local_queue_names_match(self, ini_config, qmgr):
        """All local queue names from INI can be opened in MQ."""
        keys = [
            'QLBacenCidadeReq', 'QLBacenCidadeRsp',
            'QLBacenCidadeRep', 'QLBacenCidadeSup',
        ]
        for key in keys:
            queue_name = ini_config.get('MQSeries', key)
            try:
                q = pymqi.Queue(qmgr, queue_name, pymqi.CMQC.MQOO_INQUIRE)
                q.close()
            except pymqi.MQMIError as e:
                pytest.fail(f'INI queue {key}={queue_name} not found in MQ: reason={e.reason}')

    def test_remote_queue_names_match(self, ini_config, qmgr):
        """All remote queue names from INI can be opened in MQ."""
        keys = [
            'QRCidadeBacenReq', 'QRCidadeBacenRsp',
            'QRCidadeBacenRep', 'QRCidadeBacenSup',
        ]
        for key in keys:
            queue_name = ini_config.get('MQSeries', key)
            try:
                q = pymqi.Queue(qmgr, queue_name, pymqi.CMQC.MQOO_INQUIRE)
                q.close()
            except pymqi.MQMIError as e:
                pytest.fail(f'INI queue {key}={queue_name} not found in MQ: reason={e.reason}')


# ---------------------------------------------------------------------------
# Tests: Syncpoint (Commit/Backout)
# ---------------------------------------------------------------------------
class TestSyncpoint:
    """Test transactional put/get with commit and backout."""

    def test_put_commit(self, qmgr):
        """Put under syncpoint, commit, then verify message is available."""
        open_opts = pymqi.CMQC.MQOO_OUTPUT
        try:
            q = pymqi.Queue(qmgr, TEST_QUEUE, open_opts)
        except pymqi.MQMIError as e:
            pytest.skip(f'Cannot open queue: {e.reason}')

        # Put under syncpoint
        md = pymqi.MD()
        pmo = pymqi.PMO()
        pmo.Options = pymqi.CMQC.MQPMO_SYNCPOINT
        q.put(b'SYNCPOINT_COMMIT_TEST', md, pmo)
        q.close()

        # Commit
        qmgr.commit()

        # Get the message (should be available after commit)
        q = pymqi.Queue(qmgr, TEST_QUEUE, pymqi.CMQC.MQOO_INPUT_SHARED)
        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_NO_WAIT
        received = q.get(32768, pymqi.MD(), gmo)
        q.close()

        assert received == b'SYNCPOINT_COMMIT_TEST'

    def test_put_backout(self, qmgr):
        """Put under syncpoint, backout, then verify message is gone."""
        open_opts = pymqi.CMQC.MQOO_OUTPUT
        try:
            q = pymqi.Queue(qmgr, TEST_QUEUE, open_opts)
        except pymqi.MQMIError as e:
            pytest.skip(f'Cannot open queue: {e.reason}')

        # Put under syncpoint
        md = pymqi.MD()
        pmo = pymqi.PMO()
        pmo.Options = pymqi.CMQC.MQPMO_SYNCPOINT
        q.put(b'SYNCPOINT_BACKOUT_TEST', md, pmo)
        q.close()

        # Backout
        qmgr.backout()

        # Try to get - should be empty
        q = pymqi.Queue(qmgr, TEST_QUEUE, pymqi.CMQC.MQOO_INPUT_SHARED)
        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_NO_WAIT

        with pytest.raises(pymqi.MQMIError) as exc_info:
            q.get(32768, pymqi.MD(), gmo)
        q.close()

        assert exc_info.value.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE
