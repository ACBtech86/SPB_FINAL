# nt_service.py - Windows NT Service base class (port of ntservice.cpp/h)

import os
import sys
import ctypes

try:
    import win32serviceutil
    import win32service
    import win32event
    import win32evtlogutil
    import servicemanager
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False

from bcsrvsqlmq.nt_servmsg import *


SERVICE_CONTROL_USER = 128


class CNTService:
    """Base class for Windows NT Service (port of CNTService).

    When pywin32 is not available, only debug (-d) mode is supported.
    """

    _instance = None  # Singleton reference (matches C++ m_pThis)

    def __init__(self, service_name: str, dependencies: str = ''):
        CNTService._instance = self

        self.m_szServiceName = service_name[:63]
        self.m_szDependencies = dependencies[:253]
        self.m_iMajorVersion = 1
        self.m_iMinorVersion = 0
        self.m_bIsRunning = False
        self.m_bIsDebuging = False
        self.m_bIsShutDownNow = False

        self._service_status_handle = None
        self._current_state = 0x00000001  # SERVICE_STOPPED
        self._event_source = None

    def parse_standard_args(self, argv: list) -> bool:
        if len(argv) <= 1:
            return False

        arg = argv[1].lower()

        if arg == '-v':
            print(f'{self.m_szServiceName} Versao {self.m_iMajorVersion}.{self.m_iMinorVersion}')
            installed = self.is_installed()
            print(f'O servico{"" if installed else " nao"} esta instalado.')
            return True

        if arg == '-i':
            if self.is_installed():
                print(f'{self.m_szServiceName} ja esta instalado.')
            else:
                if self.install():
                    print(f'{self.m_szServiceName} instalado.')
                else:
                    print(f'{self.m_szServiceName} falhou para instalar.')
            return True

        if arg == '-u':
            if not self.is_installed():
                print(f'{self.m_szServiceName} nao esta instalado.')
            else:
                if self.uninstall():
                    print(f'{self.m_szServiceName} removido.')
                else:
                    print(f'{self.m_szServiceName} nao pode ser removido.')
            return True

        if arg == '-d':
            self.m_bIsDebuging = True
            print(f'{self.m_szServiceName} esta rodando em modo console.')
            return False  # Continue to start_service

        return False

    def is_installed(self) -> bool:
        if not HAS_PYWIN32:
            return False
        try:
            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
            try:
                svc = win32service.OpenService(scm, self.m_szServiceName,
                                               win32service.SERVICE_QUERY_CONFIG)
                win32service.CloseServiceHandle(svc)
                return True
            except Exception:
                return False
            finally:
                win32service.CloseServiceHandle(scm)
        except Exception:
            return False

    def install(self) -> bool:
        if not HAS_PYWIN32:
            print('pywin32 not available - cannot install as service')
            return False
        try:
            exe_path = os.path.abspath(sys.argv[0])
            python_exe = sys.executable
            cmd = f'"{python_exe}" "{exe_path}"'

            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
            try:
                deps = self.m_szDependencies if self.m_szDependencies else None
                svc = win32service.CreateService(
                    scm,
                    self.m_szServiceName,
                    self.m_szServiceName,
                    win32service.SERVICE_ALL_ACCESS,
                    win32service.SERVICE_WIN32_OWN_PROCESS,
                    win32service.SERVICE_AUTO_START,
                    win32service.SERVICE_ERROR_NORMAL,
                    cmd,
                    None, 0, deps, None, None,
                )
                win32service.CloseServiceHandle(svc)
                self.log_event(servicemanager.EVENTLOG_INFORMATION_TYPE,
                               EVMSG_INSTALLED, self.m_szServiceName)
                return True
            finally:
                win32service.CloseServiceHandle(scm)
        except Exception:
            return False

    def uninstall(self) -> bool:
        if not HAS_PYWIN32:
            return False
        try:
            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
            try:
                svc = win32service.OpenService(scm, self.m_szServiceName,
                                               win32service.SERVICE_ALL_ACCESS)
                try:
                    win32service.DeleteService(svc)
                    self.log_event(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                   EVMSG_REMOVED, self.m_szServiceName)
                    return True
                finally:
                    win32service.CloseServiceHandle(svc)
            finally:
                win32service.CloseServiceHandle(scm)
        except Exception:
            return False

    def log_event(self, event_type: int, event_id: int, *strings):
        if HAS_PYWIN32:
            try:
                if not self._event_source:
                    self._event_source = win32evtlogutil.AddSourceToRegistry(
                        self.m_szServiceName, msgDLL=None,
                        eventLogType='Application',
                    )
                servicemanager.LogMsg(
                    event_type, event_id,
                    tuple(s for s in strings if s is not None),
                )
            except Exception:
                pass
        # Also print to console in debug mode
        if self.m_bIsDebuging:
            msg = ' '.join(str(s) for s in strings if s is not None)
            print(f'[Event:{event_id:#x}] {msg}')

    def start_service(self) -> bool:
        if self.m_bIsDebuging:
            # Debug/console mode - run directly
            self.m_bIsRunning = True
            self.run()
            return True

        if not HAS_PYWIN32:
            print('pywin32 not available - use -d for debug/console mode')
            return False

        # Create a dynamic service class for pywin32
        service_instance = self

        class _DynService(win32serviceutil.ServiceFramework):
            _svc_name_ = service_instance.m_szServiceName
            _svc_display_name_ = service_instance.m_szServiceName

            def SvcDoRun(self):
                service_instance.m_bIsRunning = True
                service_instance.log_event(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    EVMSG_STARTED, service_instance.m_szServiceName,
                )
                if service_instance.on_init():
                    service_instance.run()
                    service_instance.log_event(
                        servicemanager.EVENTLOG_INFORMATION_TYPE,
                        EVMSG_STOPPED, service_instance.m_szServiceName,
                    )
                service_instance.m_bIsRunning = False
                self.set_status(win32service.SERVICE_STOPPED)

            def SvcStop(self):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                service_instance.on_stop()

            def SvcPause(self):
                service_instance.on_pause()

            def SvcContinue(self):
                service_instance.on_continue()

            def set_status(self, state):
                self.ReportServiceStatus(state)

        win32serviceutil.HandleCommandLine(_DynService)
        return True

    def set_status(self, state: int):
        self._current_state = state
        # In service mode, this would call SetServiceStatus
        # In debug mode, just track the state

    def run(self):
        """Main service loop - override in subclass."""
        import time
        while self.m_bIsRunning:
            time.sleep(1)

    def on_init(self) -> bool:
        self.msg_to_log(0x0001, EVMSG_MAIN, 'NtService OnInit Rotina dummy executada')
        return True

    def on_stop(self):
        self.msg_to_log(0x0001, EVMSG_MAIN, 'NtService OnStop Rotina dummy executada')

    def on_interrogate(self, status: int):
        pass

    def on_pause(self):
        self.msg_to_log(0x0001, EVMSG_MAIN, 'NtService OnPause Rotina dummy executada')

    def on_continue(self):
        self.msg_to_log(0x0001, EVMSG_MAIN, 'NtService OnContinue Rotina dummy executada')

    def on_shutdown(self):
        self.msg_to_log(0x0001, EVMSG_MAIN, 'NtService OnShutdown Rotina dummy executada')

    def on_user_control(self, opcode: int) -> bool:
        return False

    def msg_to_log(self, event_type: int, event_id: int, text: str):
        self.log_event(event_type, event_id, text)
