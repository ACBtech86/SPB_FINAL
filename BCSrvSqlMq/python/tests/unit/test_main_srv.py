# test_main_srv.py - Unit tests for CQueueList, CClientItem, CMainSrv

import threading
import pytest

from bcsrvsqlmq.main_srv import CQueueList, CClientItem, CMainSrv
from bcsrvsqlmq.msg_sgr import MAXMSGLENGTH, TASKS_COUNT


class TestCQueueList:
    """Tests for the thread-safe queue list."""

    def test_add_and_get_size(self):
        q = CQueueList('test')
        assert q.get_size() == 0
        q.add('item1')
        q.add('item2')
        assert q.get_size() == 2

    def test_get_at(self):
        q = CQueueList('test')
        q.add('a')
        q.add('b')
        q.add('c')
        assert q.get_at(0) == 'a'
        assert q.get_at(1) == 'b'
        assert q.get_at(2) == 'c'
        assert q.get_at(99) is None
        assert q.get_at(-1) is None

    def test_get_first_removes(self):
        q = CQueueList('test')
        q.add('first')
        q.add('second')
        assert q.get_first() == 'first'
        assert q.get_size() == 1
        assert q.get_first() == 'second'
        assert q.get_size() == 0
        assert q.get_first() is None

    def test_remove_at(self):
        q = CQueueList('test')
        q.add('a')
        q.add('b')
        q.add('c')
        q.remove_at(1)
        assert q.get_size() == 2
        assert q.get_at(0) == 'a'
        assert q.get_at(1) == 'c'

    def test_remove_all(self):
        q = CQueueList('test')
        q.add('a')
        q.add('b')
        q.remove_all()
        assert q.get_size() == 0

    def test_max_size_tracking(self):
        q = CQueueList('test')
        q.add('a')
        q.add('b')
        q.add('c')
        assert q.get_max_size() == 3
        q.remove_at(0)
        assert q.get_max_size() == 3  # Max doesn't decrease

    def test_locate_sock(self):
        q = CQueueList('test')
        client = CClientItem()
        client.m_Sock = 'fake_socket'
        q.add(client)

        found = q.locate_sock('fake_socket')
        assert found is client

        not_found = q.locate_sock('other_socket')
        assert not_found is None

    def test_remove_sock(self):
        q = CQueueList('test')
        client = CClientItem()
        client.m_Sock = 'fake_socket'
        q.add(client)

        removed = q.remove_sock('fake_socket')
        assert removed is client
        assert q.get_size() == 0

    def test_remove_sock_not_found(self):
        q = CQueueList('test')
        result = q.remove_sock('nonexistent')
        assert result is None

    def test_iter(self):
        q = CQueueList('test')
        q.add(1)
        q.add(2)
        q.add(3)
        assert list(q) == [1, 2, 3]

    def test_len(self):
        q = CQueueList('test')
        assert len(q) == 0
        q.add('x')
        assert len(q) == 1

    def test_thread_safety(self):
        """Multiple threads adding to queue should not corrupt it."""
        q = CQueueList('test')
        errors = []

        def adder(start):
            try:
                for i in range(100):
                    q.add(start + i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=adder, args=(i * 100,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert q.get_size() == 500


class TestCClientItem:
    """Tests for the client item class."""

    def test_default_values(self):
        c = CClientItem()
        assert c.m_CliHumano == ''
        assert c.m_Sock is None
        assert c.m_IsActive is False
        assert c.m_ForceCli is False
        assert c.m_timeout == 120
        assert len(c.dadosin) == MAXMSGLENGTH
        assert len(c.dadosout) == MAXMSGLENGTH

    def test_lock_unlock(self):
        c = CClientItem()
        c.lock()
        c.unlock()  # Should not raise

    def test_custom_values(self):
        c = CClientItem()
        c.m_CliHumano = '192.168.1.1:5000'
        c.m_szPorta = '5000'
        c.m_IsActive = True
        c.m_timeout = 60

        assert c.m_CliHumano == '192.168.1.1:5000'
        assert c.m_szPorta == '5000'
        assert c.m_IsActive is True
        assert c.m_timeout == 60


class TestCMainSrv:
    """Tests for the main server coordinator."""

    def test_initial_state(self):
        srv = CMainSrv()
        assert srv.MainIsRunning is False
        assert srv.MainIsStoping is False
        assert srv.MoniIsRunning is False
        assert srv.pInitSrv is None
        assert srv.pMonitor is None

    def test_events_exist(self):
        srv = CMainSrv()
        assert srv.m_event_timer is not None
        assert srv.m_event_acabou is not None
        assert srv.m_event_stop is not None
        assert srv.m_event_pause is not None
        assert srv.m_event_continue is not None
        assert srv.m_event_monitor_stop is not None
        assert srv.m_event_tasksapp_stop is not None

    def test_status_task_array(self):
        srv = CMainSrv()
        assert len(srv.m_StatusTask) == TASKS_COUNT

    def test_queue_lists_initialized(self):
        srv = CMainSrv()
        assert srv.m_TaskList.get_size() == 0
        assert srv.m_StopList.get_size() == 0
        assert srv.m_ClientList.get_size() == 0
        assert srv.m_MonitorList.get_size() == 0

    def test_audit_operations(self, tmp_path):
        srv = CMainSrv()
        srv.init_audit()

        srv.m_pathAudit = str(tmp_path)
        srv.m_nameAudit = 'TestAudit'
        srv.open_audit(str(tmp_path), 'TestAudit')
        assert srv.m_hAudit is not None

        srv.write_audit(b'test audit data')

        srv.close_audit()
        assert srv.m_hAudit is None

    def test_close_audit_twice(self, tmp_path):
        srv = CMainSrv()
        srv.open_audit(str(tmp_path), 'Test')
        srv.close_audit()
        srv.close_audit()  # Should not raise

    def test_check_finaliza_no_running(self):
        srv = CMainSrv()
        srv.MoniIsRunning = False
        srv.check_finaliza()
        assert srv.m_event_acabou.is_set()

    def test_check_finaliza_mon(self):
        srv = CMainSrv()
        srv.check_finaliza_mon()
        assert srv.m_event_acabou.is_set()
