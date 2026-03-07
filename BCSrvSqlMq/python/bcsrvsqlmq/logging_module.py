# logging_module.py - Logging module (port of BCMsgSqlMq.dll)

import os
import threading
from datetime import datetime


class LoggingModule:
    """Thread-safe logging module replacing BCMsgSqlMq.dll."""

    def __init__(self):
        self._lock = threading.Lock()
        self._log_file = None
        self._trace_level = 0
        self._log_file_path = ''

    def _get_timestamp(self) -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def open_log(self, log_dir: str, app_name: str, server_name: str = '') -> bool:
        with self._lock:
            try:
                if self._log_file is not None:
                    self._log_file.close()
                    self._log_file = None

                if not log_dir:
                    log_dir = 'C:\\BCSrvSqlMq\\Logs'
                if not app_name:
                    app_name = 'BCSrvSqlMq'

                date_str = datetime.now().strftime('%Y%m%d')
                self._log_file_path = os.path.join(log_dir, f'{app_name}_{date_str}.log')

                os.makedirs(log_dir, exist_ok=True)

                self._log_file = open(self._log_file_path, 'a', encoding='latin-1')

                self._log_file.write('\n========================================\n')
                self._log_file.write(f'Log opened: {self._get_timestamp()}\n')
                self._log_file.write(f'Application: {app_name}\n')
                if server_name:
                    self._log_file.write(f'Server: {server_name}\n')
                self._log_file.write('========================================\n\n')
                self._log_file.flush()

                return True
            except Exception:
                return False

    def write_log(self, task_name: str, msg_id: int, flag: bool, *params) -> bool:
        with self._lock:
            try:
                if self._log_file is None:
                    return False

                level = 'ERROR' if flag else 'INFO'
                self._log_file.write(
                    f'[{self._get_timestamp()}] [{level}] [MsgID:{msg_id}] '
                )

                if task_name:
                    self._log_file.write(f'[Task:{task_name}] ')

                non_none_params = [p for p in params if p is not None]
                if non_none_params:
                    self._log_file.write('Params: ')
                    for i, p in enumerate(non_none_params, 1):
                        self._log_file.write(f'p{i}={p} ')

                self._log_file.write('\n')
                self._log_file.flush()
                return True
            except Exception:
                return False

    def write_reg(self, task_name: str, flag: bool, size: int, data: bytes) -> bool:
        with self._lock:
            try:
                if self._log_file is None:
                    return False

                mode = 'WRITE' if flag else 'READ'
                self._log_file.write(
                    f'[{self._get_timestamp()}] [REGISTRY] [{mode}] '
                )

                if task_name:
                    self._log_file.write(f'[Task:{task_name}] ')

                self._log_file.write(f'Size:{size} bytes')

                if data and 0 < size <= 1024:
                    self._log_file.write(' Data: ')
                    hex_bytes = data[:min(size, 64)]
                    self._log_file.write(' '.join(f'{b:02X}' for b in hex_bytes))
                    if size > 64:
                        self._log_file.write(f' ... ({size - 64} more bytes)')

                self._log_file.write('\n')
                self._log_file.flush()
                return True
            except Exception:
                return False

    def close_log(self) -> bool:
        with self._lock:
            try:
                if self._log_file is not None:
                    self._log_file.write('\n========================================\n')
                    self._log_file.write(f'Log closed: {self._get_timestamp()}\n')
                    self._log_file.write('========================================\n\n')
                    self._log_file.flush()
                    self._log_file.close()
                    self._log_file = None
                return True
            except Exception:
                return False

    def set_trace(self, level: int) -> bool:
        with self._lock:
            try:
                self._trace_level = level
                if self._log_file is not None:
                    self._log_file.write(
                        f'[{self._get_timestamp()}] [TRACE] Level set to: {level}\n'
                    )
                    self._log_file.flush()
                return True
            except Exception:
                return False

    @property
    def trace_level(self) -> int:
        return self._trace_level
