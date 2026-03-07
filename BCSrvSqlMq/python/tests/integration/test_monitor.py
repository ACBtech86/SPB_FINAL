# test_monitor.py - Integration tests for TCP monitor

import socket
import struct
import threading
import time
import pytest

from bcsrvsqlmq.msg_sgr import COMHDR, COMHDR_SIZE, FUNC_NOP, FUNC_POST


class MockInitSrv:
    """Minimal mock of CInitSrv for monitor tests."""
    def __init__(self, port):
        self.m_MonitorPort = port
        self.m_SrvTimeout = 120
        self.m_WriteLog = self._noop_log

    def _noop_log(self, *args, **kwargs):
        pass


class MockMainSrv:
    """Minimal mock of CMainSrv for monitor tests."""
    def __init__(self, port):
        self.pInitSrv = MockInitSrv(port)
        self.m_event_monitor_stop = threading.Event()
        self.m_ClientList = MockQueueList()
        self.m_TaskList = []


class MockQueueList:
    """Minimal mock of CQueueList."""
    def __init__(self):
        self._items = []

    def add(self, item):
        self._items.append(item)

    def remove_sock(self, sock):
        pass

    def get_size(self):
        return len(self._items)


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


@pytest.mark.integration
class TestMonitor:
    """Integration tests for CMonitor TCP server."""

    def test_import(self):
        from bcsrvsqlmq.monitor import CMonitor

    def test_start_and_stop(self):
        from bcsrvsqlmq.monitor import CMonitor

        port = find_free_port()
        main_srv = MockMainSrv(port)
        monitor = CMonitor()

        thread = threading.Thread(target=monitor.run_monitor, args=(main_srv,), daemon=True)
        thread.start()

        # Wait for monitor to start listening
        time.sleep(0.5)

        # Signal stop
        monitor.m_event_stop.set()
        thread.join(timeout=5)
        assert not thread.is_alive()

    def test_accept_connection(self):
        from bcsrvsqlmq.monitor import CMonitor

        port = find_free_port()
        main_srv = MockMainSrv(port)
        monitor = CMonitor()

        thread = threading.Thread(target=monitor.run_monitor, args=(main_srv,), daemon=True)
        thread.start()
        time.sleep(0.5)

        # Connect a client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect(('127.0.0.1', port))
            time.sleep(0.5)

            # Should have one client
            assert main_srv.m_ClientList.get_size() >= 1
        finally:
            client.close()
            monitor.m_event_stop.set()
            thread.join(timeout=5)

    def test_send_nop_message(self):
        from bcsrvsqlmq.monitor import CMonitor

        port = find_free_port()
        main_srv = MockMainSrv(port)
        monitor = CMonitor()

        thread = threading.Thread(target=monitor.run_monitor, args=(main_srv,), daemon=True)
        thread.start()
        time.sleep(0.5)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect(('127.0.0.1', port))
            time.sleep(0.3)

            # Send a NOP message
            hdr = COMHDR(
                usMsgLength=COMHDR_SIZE,
                ucIdHeader=b'\x00' * 4,
                ucFuncSgr=FUNC_NOP,
                usRc=0,
                usDatLength=0,
            )
            client.sendall(hdr.pack())
            time.sleep(0.5)

            # Connection should still be alive (NOP just resets timeout)
            assert main_srv.m_ClientList.get_size() >= 1
        finally:
            client.close()
            monitor.m_event_stop.set()
            thread.join(timeout=5)

    def test_client_disconnect(self):
        from bcsrvsqlmq.monitor import CMonitor

        port = find_free_port()
        main_srv = MockMainSrv(port)
        monitor = CMonitor()

        thread = threading.Thread(target=monitor.run_monitor, args=(main_srv,), daemon=True)
        thread.start()
        time.sleep(0.5)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', port))
        time.sleep(0.3)
        client.close()
        time.sleep(1.5)  # Wait for monitor to detect disconnection

        monitor.m_event_stop.set()
        thread.join(timeout=5)
