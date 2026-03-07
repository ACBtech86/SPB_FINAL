# main_srv.py - Main server coordinator (port of MainSrv.cpp/h)

import os
import threading
import time
import struct
from datetime import datetime

from bcsrvsqlmq.msg_sgr import (
    STTASKSTATUS, STAUDITFILE, MAXMSGLENGTH, COMHDR, COMHDR_SIZE,
    TASKS_COUNT, TASKS_MONITOR, TASKS_BACENREQ, TASKS_BACENRSP,
    TASKS_BACENREP, TASKS_BACENSUP, TASKS_IFREQ, TASKS_IFRSP,
    TASKS_IFREP, TASKS_IFSUP, FUNC_POST, FUNC_NOP,
)
from bcsrvsqlmq.thread_mq import CThreadMQ, THREAD_EVENT_STOP

# Task mode constants
TASK_AUTOMATIC = True
TASK_MANUAL = False

# Main event indices
MAIN_EVENT_TIMER = 0
MAIN_EVENT_ACABOU = 1
MAIN_EVENT_STOP = 2
MAIN_EVENT_PAUSE = 3
MAIN_EVENT_CONTINUE = 4
MAIN_EVENT_MONITOR_STOP = 5
MAIN_EVENT_TASKSAPP_STOP = 6
QTD_EVENTS_FIXED = 7

# Client status constants
ST_CLI_CONNECT = 1
ST_CLI_CONSULTA = 2
ST_CLI_DISCONNECT = 3
ST_CLI_QUEUE = 4
ST_CLI_WAITRESP = 5


class CClientItem:
    """Represents a connected monitoring client (port of CClientItem)."""

    def __init__(self):
        self.m_mutex = threading.Lock()
        self.m_CliHumano = ''
        self.m_szPorta = ''
        self.m_Sock = None
        self.m_AddrCli = None
        self.dadosin = bytearray(MAXMSGLENGTH)
        self.dadosout = bytearray(MAXMSGLENGTH)
        self.tamdadosin = 0
        self.tamdadosout = 0
        self.m_status = 0
        self.m_timeout = 120
        self.m_index = 0
        self.m_IsActive = False
        self.m_ForceCli = False

    def lock(self):
        self.m_mutex.acquire()

    def unlock(self):
        self.m_mutex.release()


class CQueueList:
    """Thread-safe list container (port of CQueueList)."""

    def __init__(self, name: str = '', is_true_list: bool = True):
        self.m_mutex = threading.Lock()
        self.m_QueueList = []
        self.m_iMaxList = 0
        self.m_name = name

    def add(self, obj):
        with self.m_mutex:
            self.m_QueueList.append(obj)
            if len(self.m_QueueList) > self.m_iMaxList:
                self.m_iMaxList = len(self.m_QueueList)

    def remove_at(self, index: int):
        with self.m_mutex:
            if 0 <= index < len(self.m_QueueList):
                del self.m_QueueList[index]

    def remove_all(self):
        with self.m_mutex:
            self.m_QueueList.clear()

    def get_size(self) -> int:
        with self.m_mutex:
            return len(self.m_QueueList)

    def get_max_size(self) -> int:
        return self.m_iMaxList

    def get_at(self, index: int):
        with self.m_mutex:
            if 0 <= index < len(self.m_QueueList):
                return self.m_QueueList[index]
            return None

    def get_first(self):
        with self.m_mutex:
            if self.m_QueueList:
                return self.m_QueueList.pop(0)
            return None

    def locate_sock(self, sock):
        with self.m_mutex:
            for item in self.m_QueueList:
                if hasattr(item, 'm_Sock') and item.m_Sock == sock:
                    return item
            return None

    def remove_sock(self, sock):
        with self.m_mutex:
            for i, item in enumerate(self.m_QueueList):
                if hasattr(item, 'm_Sock') and item.m_Sock == sock:
                    return self.m_QueueList.pop(i)
            return None

    def __iter__(self):
        with self.m_mutex:
            return iter(list(self.m_QueueList))

    def __len__(self):
        return self.get_size()


class CMainSrv:
    """Main server coordinator (port of CMainSrv)."""

    def __init__(self):
        # Events
        self.m_event_timer = threading.Event()
        self.m_event_acabou = threading.Event()
        self.m_event_stop = threading.Event()
        self.m_event_pause = threading.Event()
        self.m_event_continue = threading.Event()
        self.m_event_monitor_stop = threading.Event()
        self.m_event_tasksapp_stop = threading.Event()

        # State flags
        self.MainIsRunning = False
        self.MainIsStoping = False
        self.MoniIsRunning = False

        # Queue lists
        self.m_TaskList = CQueueList('Task List', True)
        self.m_StopList = CQueueList('Stop List', False)
        self.m_ClientList = CQueueList('Client List', True)
        self.m_MonitorList = CQueueList('Monitor List', False)

        # Task indices
        self.m_TaskBacenReq = None
        self.m_TaskBacenRsp = None
        self.m_TaskBacenRep = None
        self.m_TaskBacenSup = None
        self.m_TaskIFReq = None
        self.m_TaskIFRsp = None
        self.m_TaskIFRep = None
        self.m_TaskIFSup = None

        # Audit
        self.m_hAudit = None
        self.m_hAuditmutex = threading.Lock()
        self.m_pathAudit = ''
        self.m_nameAudit = ''
        self.m_auditDate = ''

        # Pointers
        self.pMonitor = None
        self.pInitSrv = None

        # Task status
        self.m_StatusTask = [STTASKSTATUS() for _ in range(TASKS_COUNT)]

        # Timer
        self._timer_thread = None
        self._timer_counter = 0

    def prepara_tasks(self, init_srv) -> bool:
        """Create and start all 8 worker threads + monitor (replaces PreparaTasks)."""
        from bcsrvsqlmq.bacen_req import CBacenReq
        from bcsrvsqlmq.bacen_rsp import CBacenRsp
        from bcsrvsqlmq.bacen_rep import CBacenRep
        from bcsrvsqlmq.bacen_sup import CBacenSup
        from bcsrvsqlmq.if_req import CIFReq
        from bcsrvsqlmq.if_rsp import CIFRsp
        from bcsrvsqlmq.if_rep import CIFRep
        from bcsrvsqlmq.if_sup import CIFSup
        from bcsrvsqlmq.monitor import CMonitor

        self.pInitSrv = init_srv
        self.MainIsRunning = True
        self.MainIsStoping = False

        # Log startup
        write_log = init_srv.m_WriteLog
        write_log(init_srv.m_szServiceName, 8014, False, 'PreparaTasks started')

        # Initialize audit
        self.init_audit()
        self.m_pathAudit = init_srv.m_DirAudFile
        self.m_nameAudit = init_srv.m_szServiceName
        self.open_audit(self.m_pathAudit, self.m_nameAudit)

        # Create 8 worker tasks
        svc = init_srv.m_szServiceName
        self.m_TaskBacenReq = CBacenReq(f'RmtReq..{svc}', TASK_AUTOMATIC, TASKS_BACENREQ, self)
        self.m_TaskBacenRsp = CBacenRsp(f'RmtRsp..{svc}', TASK_AUTOMATIC, TASKS_BACENRSP, self)
        self.m_TaskBacenRep = CBacenRep(f'RmtRep..{svc}', TASK_AUTOMATIC, TASKS_BACENREP, self)
        self.m_TaskBacenSup = CBacenSup(f'RmtSup..{svc}', TASK_AUTOMATIC, TASKS_BACENSUP, self)
        self.m_TaskIFReq = CIFReq(f'LocReq..{svc}', TASK_AUTOMATIC, TASKS_IFREQ, self)
        self.m_TaskIFRsp = CIFRsp(f'LocRsp..{svc}', TASK_AUTOMATIC, TASKS_IFRSP, self)
        self.m_TaskIFRep = CIFRep(f'LocRep..{svc}', TASK_AUTOMATIC, TASKS_IFREP, self)
        self.m_TaskIFSup = CIFSup(f'LocSup..{svc}', TASK_AUTOMATIC, TASKS_IFSUP, self)

        # Add to task list
        for task in [self.m_TaskBacenReq, self.m_TaskBacenRsp,
                     self.m_TaskBacenRep, self.m_TaskBacenSup,
                     self.m_TaskIFReq, self.m_TaskIFRsp,
                     self.m_TaskIFRep, self.m_TaskIFSup]:
            self.m_TaskList.add(task)

        # Start worker threads
        for task in self.m_TaskList:
            self._start_task_thread(task)

        # Start timer thread
        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True,
                                              name='MainSrv-Timer')
        self._timer_thread.start()

        # Start Monitor
        self.pMonitor = CMonitor()
        monitor_thread = threading.Thread(target=self.pMonitor.run_monitor, args=(self,),
                                          daemon=True, name='Monitor')
        monitor_thread.start()
        self.MoniIsRunning = True

        write_log(init_srv.m_szServiceName, 8014, False, 'PreparaTasks completed')
        return True

    def _start_task_thread(self, task):
        """Start a single task thread."""
        task.m_thread = threading.Thread(
            target=CThreadMQ.task_thread, args=(self, task),
            daemon=True, name=task.m_szTaskName,
        )
        task.m_thread.start()

    def wait_tasks(self):
        """Main event loop - blocks until service stops (replaces WaitTasks)."""
        while self.MainIsRunning:
            # Check events in priority order
            if self.m_event_stop.is_set():
                self.m_event_stop.clear()
                self.end_tasks()
                self.check_finaliza()
                continue

            if self.m_event_acabou.is_set():
                self.m_event_acabou.clear()
                self.MainIsRunning = False
                break

            if self.m_event_tasksapp_stop.is_set():
                self.m_event_tasksapp_stop.clear()
                self.processa_stop_list()
                continue

            if self.m_event_monitor_stop.is_set():
                self.m_event_monitor_stop.clear()
                self.MoniIsRunning = False
                self.check_finaliza_mon()
                continue

            if self.m_event_timer.is_set():
                self.m_event_timer.clear()
                self.processa_timer()
                continue

            # Sleep briefly to avoid busy wait
            time.sleep(0.1)

        # Cleanup
        self.close_audit()

    def _timer_loop(self):
        """Timer thread - fires every 1s (replaces WaitableTimer)."""
        while self.MainIsRunning:
            time.sleep(1.0)
            self._timer_counter += 1
            if self._timer_counter >= 20:
                self._timer_counter = 0
                self.m_event_timer.set()

    def processa_timer(self):
        """Restart dead automatic threads (called every ~20 seconds)."""
        for task in self.m_TaskList:
            if task.m_AutomaticThread and not task.m_ThreadIsRunning:
                if self.pInitSrv:
                    self.pInitSrv.m_WriteLog(
                        task.m_szTaskName, 8014, False, 'Restarting task')
                self._start_task_thread(task)

    def processa_stop_list(self):
        """Process tasks that have stopped."""
        while self.m_StopList.get_size() > 0:
            task = self.m_StopList.get_first()
            if task:
                task.m_ThreadIsRunning = False
                if self.pInitSrv:
                    self.pInitSrv.m_WriteLog(
                        task.m_szTaskName, 8012, False, 'Task stopped')

        if self.MainIsStoping:
            self.check_finaliza()

    def end_tasks(self):
        """Signal all tasks to stop (replaces EndTasks)."""
        self.MainIsStoping = True
        for task in self.m_TaskList:
            task.m_AutomaticThread = TASK_MANUAL
            if task.m_ThreadIsRunning:
                task.m_event_stop.set()

    def check_finaliza(self):
        """Check if all tasks are stopped (replaces CheckFinaliza)."""
        any_running = False
        for task in self.m_TaskList:
            if task.m_ThreadIsRunning:
                any_running = True
                break

        if not any_running:
            if self.MoniIsRunning and self.pMonitor:
                self.pMonitor.m_event_stop.set()
            else:
                self.m_event_acabou.set()

    def check_finaliza_mon(self):
        """Called when monitor stops (replaces CheckFinalizaMon)."""
        self.m_event_acabou.set()

    # ------------------------------------------------------------------
    # Audit file management
    # ------------------------------------------------------------------
    def init_audit(self):
        """Initialize audit mutex."""
        pass  # m_hAuditmutex already created in __init__

    def open_audit(self, path: str, name: str):
        """Open/create audit file with date stamp."""
        try:
            os.makedirs(path, exist_ok=True)
            date_str = datetime.now().strftime('%Y%m%d')
            self.m_auditDate = date_str
            filename = os.path.join(path, f'{name}_{date_str}.aud')
            self.m_hAudit = open(filename, 'ab')
        except Exception:
            self.m_hAudit = None

    def check_data_audit(self):
        """Check if date changed, reopen audit file if needed."""
        current_date = datetime.now().strftime('%Y%m%d')
        if current_date != self.m_auditDate:
            self.close_audit()
            self.open_audit(self.m_pathAudit, self.m_nameAudit)

    def close_audit(self):
        """Close audit file."""
        with self.m_hAuditmutex:
            if self.m_hAudit:
                try:
                    self.m_hAudit.close()
                except Exception:
                    pass
                self.m_hAudit = None

    def write_audit(self, data: bytes):
        """Write data to audit file (thread-safe)."""
        with self.m_hAuditmutex:
            if self.m_hAudit:
                try:
                    self.check_data_audit()
                    self.m_hAudit.write(data)
                    self.m_hAudit.flush()
                except Exception:
                    pass

    def monta_audit(self, mq_header: bytes, sec_header: bytes, msg_xml: bytes) -> bytes:
        """Assemble audit record from components."""
        now = datetime.now()
        audit = STAUDITFILE()
        audit.AUD_AAAAMMDD = now.strftime('%Y%m%d').encode('ascii')
        audit.AUD_HHMMDDSS = now.strftime('%H%M%S00').encode('ascii')[:8]

        # Pad MQ header to 512 bytes
        audit.AUD_MQ_HEADER = mq_header[:512].ljust(512, b'\x00')

        # Security header
        from bcsrvsqlmq.msg_sgr import SECHDR_SIZE
        audit.AUD_SEC_HEADER = sec_header[:SECHDR_SIZE].ljust(SECHDR_SIZE, b'\x00')

        # SPB document
        audit.AUD_SPBDOC = msg_xml[:32767]

        # Calculate record size
        total = (2 + 8 + 8 + 512 + SECHDR_SIZE + len(audit.AUD_SPBDOC) + 2)
        audit.AUD_TAMREG = total
        audit.AUD_TAMREG_PREV = total

        return audit.pack()
