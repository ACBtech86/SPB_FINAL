# test_logging_module.py - Unit tests for LoggingModule

import os
import threading
import pytest

from bcsrvsqlmq.logging_module import LoggingModule


class TestLoggingModule:
    """Tests for the LoggingModule class."""

    def test_open_and_close_log(self, tmp_dir):
        logger = LoggingModule()
        assert logger.open_log(str(tmp_dir), 'TestApp')
        assert logger._log_file is not None

        # Check log file exists
        files = os.listdir(str(tmp_dir))
        assert any(f.startswith('TestApp_') and f.endswith('.log') for f in files)

        assert logger.close_log()
        assert logger._log_file is None

    def test_write_log_info(self, tmp_dir):
        logger = LoggingModule()
        logger.open_log(str(tmp_dir), 'TestApp')

        result = logger.write_log('TaskA', 8014, False, 'Service starting')
        assert result is True

        logger.close_log()

        # Read log file and check content
        log_files = [f for f in os.listdir(str(tmp_dir)) if f.endswith('.log')]
        with open(os.path.join(str(tmp_dir), log_files[0]), 'r', encoding='latin-1') as f:
            content = f.read()

        assert '[INFO]' in content
        assert '[MsgID:8014]' in content
        assert '[Task:TaskA]' in content
        assert 'Service starting' in content

    def test_write_log_error(self, tmp_dir):
        logger = LoggingModule()
        logger.open_log(str(tmp_dir), 'TestApp')

        result = logger.write_log('TaskB', 8019, True, 'Something failed')
        assert result is True

        logger.close_log()

        log_files = [f for f in os.listdir(str(tmp_dir)) if f.endswith('.log')]
        with open(os.path.join(str(tmp_dir), log_files[0]), 'r', encoding='latin-1') as f:
            content = f.read()

        assert '[ERROR]' in content
        assert 'Something failed' in content

    def test_write_log_without_open_returns_false(self):
        logger = LoggingModule()
        result = logger.write_log('Task', 1, False, 'test')
        assert result is False

    def test_write_reg(self, tmp_dir):
        logger = LoggingModule()
        logger.open_log(str(tmp_dir), 'TestApp')

        data = b'\x01\x02\x03\x04\x05'
        result = logger.write_reg('TaskC', True, len(data), data)
        assert result is True

        logger.close_log()

        log_files = [f for f in os.listdir(str(tmp_dir)) if f.endswith('.log')]
        with open(os.path.join(str(tmp_dir), log_files[0]), 'r', encoding='latin-1') as f:
            content = f.read()

        assert '[REGISTRY]' in content
        assert '[WRITE]' in content
        assert '01 02 03 04 05' in content

    def test_set_trace(self, tmp_dir):
        logger = LoggingModule()
        logger.open_log(str(tmp_dir), 'TestApp')

        assert logger.set_trace(2)
        assert logger.trace_level == 2

        logger.close_log()

    def test_open_log_creates_directory(self, tmp_dir):
        log_dir = os.path.join(str(tmp_dir), 'subdir', 'logs')
        logger = LoggingModule()
        assert logger.open_log(log_dir, 'TestApp')
        assert os.path.isdir(log_dir)
        logger.close_log()

    def test_thread_safety(self, tmp_dir):
        """Multiple threads writing to log should not crash."""
        logger = LoggingModule()
        logger.open_log(str(tmp_dir), 'ThreadTest')

        errors = []

        def writer(thread_id):
            try:
                for i in range(50):
                    logger.write_log(f'Thread{thread_id}', i, False, f'msg {i}')
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        logger.close_log()
        assert len(errors) == 0

    def test_log_header_written_on_open(self, tmp_dir):
        logger = LoggingModule()
        logger.open_log(str(tmp_dir), 'TestApp', 'TestServer')
        logger.close_log()

        log_files = [f for f in os.listdir(str(tmp_dir)) if f.endswith('.log')]
        with open(os.path.join(str(tmp_dir), log_files[0]), 'r', encoding='latin-1') as f:
            content = f.read()

        assert 'Log opened:' in content
        assert 'Application: TestApp' in content
        assert 'Server: TestServer' in content
        assert 'Log closed:' in content

    def test_reopen_closes_previous(self, tmp_dir):
        logger = LoggingModule()
        logger.open_log(str(tmp_dir), 'First')
        first_file = logger._log_file
        logger.open_log(str(tmp_dir), 'Second')
        assert first_file.closed
        logger.close_log()
