# monitor.py - TCP monitoring server (port of Monitor.cpp/h)

import socket
import select
import struct
import threading
import time

from bcsrvsqlmq.msg_sgr import (
    COMHDR, COMHDR_SIZE, MIMSG, MAXMSGLENGTH, MINMSGLENGTH,
    FUNC_POST, FUNC_NOP, TASKS_COUNT,
)
from bcsrvsqlmq.thread_mq import THREAD_EVENT_STOP

# Monitor event indices
EVENT_TIMER = 0
EVENT_TCP = 1
EVENT_STOP = 2
EVENT_MST = 3
EVENT_QUEUE = 4
EVENT_CLITCP = 5
QTD_MONI_EVENTS = 55
MAX_CLIENTS = QTD_MONI_EVENTS - EVENT_CLITCP  # 50

# Client status
ST_CLI_CONNECT = 1
ST_CLI_DISCONNECT = 3


class CMonitor:
    """TCP monitoring server (port of CMonitor)."""

    def __init__(self):
        self.m_event_stop = threading.Event()
        self.srv_sock = None
        self.cli_socks = {}  # {socket: CClientItem}
        self.is_busy = False
        self.pMainSrv = None

    def run_monitor(self, main_srv):
        """Main monitor loop (replaces RunMonitor)."""
        self.pMainSrv = main_srv
        self.is_busy = True

        write_log = None
        if main_srv.pInitSrv:
            write_log = main_srv.pInitSrv.m_WriteLog

        if write_log:
            write_log('Monitor', 8014, False, 'Monitor starting')

        # Initialize server socket
        self._init_srv_socket()

        # Main event loop
        while not self.m_event_stop.is_set():
            try:
                # Build socket list for select
                read_socks = []
                if self.srv_sock:
                    read_socks.append(self.srv_sock)
                read_socks.extend(self.cli_socks.keys())

                if not read_socks:
                    time.sleep(1.0)
                    self._check_timeout()
                    if not self.srv_sock:
                        self._init_srv_socket()
                    continue

                readable, _, _ = select.select(read_socks, [], [], 1.0)

                for sock in readable:
                    if sock is self.srv_sock:
                        self._aceita_conexao()
                    else:
                        self._recebe_dados_cli(sock)

                self._check_timeout()

            except Exception as e:
                if write_log:
                    write_log('Monitor', 8019, True, f'Monitor error: {e}')
                time.sleep(1.0)

        # Cleanup
        self._cleanup()
        self.is_busy = False

        if write_log:
            write_log('Monitor', 8012, False, 'Monitor stopped')

        main_srv.m_event_monitor_stop.set()

    def _init_srv_socket(self):
        """Initialize server listening socket."""
        if not self.pMainSrv or not self.pMainSrv.pInitSrv:
            return

        port = self.pMainSrv.pInitSrv.m_MonitorPort
        write_log = self.pMainSrv.pInitSrv.m_WriteLog

        try:
            self.srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.srv_sock.setblocking(False)
            self.srv_sock.bind(('0.0.0.0', port))
            self.srv_sock.listen(37)

            if write_log:
                write_log('Monitor', 8070, False, f'Listening on port {port}')
        except Exception as e:
            if write_log:
                write_log('Monitor', 8019, True, f'Socket init error: {e}')
            self.srv_sock = None

    def _aceita_conexao(self):
        """Accept incoming client connection."""
        if not self.srv_sock:
            return

        write_log = self.pMainSrv.pInitSrv.m_WriteLog if self.pMainSrv.pInitSrv else None

        try:
            client_sock, addr = self.srv_sock.accept()
            client_sock.setblocking(False)

            if len(self.cli_socks) >= MAX_CLIENTS:
                if write_log:
                    write_log('Monitor', 8019, True, 'Max clients reached')
                client_sock.close()
                return

            from bcsrvsqlmq.main_srv import CClientItem
            client = CClientItem()
            client.m_Sock = client_sock
            client.m_AddrCli = addr
            client.m_CliHumano = f'{addr[0]}:{addr[1]}'
            client.m_szPorta = str(addr[1])
            client.m_status = ST_CLI_CONNECT
            client.m_timeout = self.pMainSrv.pInitSrv.m_SrvTimeout
            client.m_IsActive = True

            self.cli_socks[client_sock] = client
            self.pMainSrv.m_ClientList.add(client)

            if write_log:
                write_log('Monitor', 8070, False, f'Client connected: {client.m_CliHumano}')

        except Exception as e:
            if write_log:
                write_log('Monitor', 8019, True, f'Accept error: {e}')

    def _recebe_dados_cli(self, sock):
        """Receive data from client socket."""
        client = self.cli_socks.get(sock)
        if not client or not client.m_IsActive:
            return

        write_log = self.pMainSrv.pInitSrv.m_WriteLog if self.pMainSrv.pInitSrv else None

        try:
            # Receive header first
            data = sock.recv(MAXMSGLENGTH)
            if not data:
                self._force_close_cli(sock)
                return

            if len(data) < MINMSGLENGTH:
                self._force_close_cli(sock)
                return

            # Parse message header
            hdr = COMHDR.unpack(data[:COMHDR_SIZE])

            if hdr.usMsgLength < MINMSGLENGTH:
                self._force_close_cli(sock)
                return

            # Store received data
            client.dadosin[:len(data)] = data
            client.tamdadosin = len(data)

            # Process the data
            self._processa_dados_cli(sock, client, data)

        except socket.error as e:
            if e.errno != 10035:  # WSAEWOULDBLOCK
                self._force_close_cli(sock)
        except Exception:
            self._force_close_cli(sock)

    def _processa_dados_cli(self, sock, client, data: bytes):
        """Process received client data (replaces ProcessaDadosCli)."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog if self.pMainSrv.pInitSrv else None

        hdr = COMHDR.unpack(data[:COMHDR_SIZE])

        if hdr.ucFuncSgr == FUNC_NOP:
            # NOP - reset timeout
            client.m_timeout = self.pMainSrv.pInitSrv.m_SrvTimeout
            return

        if hdr.ucFuncSgr == FUNC_POST:
            # POST - find matching task and signal it
            # Extract queue name from message data
            msg_data = data[COMHDR_SIZE:COMHDR_SIZE + hdr.usDatLength]
            queue_name = msg_data[:48].decode('latin-1', errors='replace').strip()

            found = False
            for task in self.pMainSrv.m_TaskList:
                if task.m_ThreadIsRunning and task.m_szQueueName.strip() == queue_name:
                    task.m_event_post.set()
                    found = True
                    break

            # Prepare response
            resp_hdr = COMHDR()
            resp_hdr.usMsgLength = COMHDR_SIZE
            resp_hdr.ucIdHeader = hdr.ucIdHeader
            resp_hdr.ucFuncSgr = hdr.ucFuncSgr
            resp_hdr.usRc = 0 if found else 99
            resp_hdr.usDatLength = 0

            self._send_dados_cli(sock, client, resp_hdr.pack())

    def _send_dados_cli(self, sock, client, data: bytes):
        """Send data to client socket."""
        if not client.m_IsActive:
            return

        client.lock()
        try:
            total_sent = 0
            while total_sent < len(data):
                try:
                    sent = sock.send(data[total_sent:])
                    if sent == 0:
                        break
                    total_sent += sent
                except socket.error as e:
                    if e.errno == 10035:  # WSAEWOULDBLOCK
                        time.sleep(0.02)
                        continue
                    break
        finally:
            client.unlock()

    def _force_close_cli(self, sock):
        """Force close a client connection."""
        write_log = self.pMainSrv.pInitSrv.m_WriteLog if self.pMainSrv.pInitSrv else None

        client = self.cli_socks.pop(sock, None)
        if client:
            client.m_IsActive = False
            self.pMainSrv.m_ClientList.remove_sock(sock)

            if write_log:
                write_log('Monitor', 8070, False,
                          f'Client disconnected: {client.m_CliHumano}')

        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass

    def _check_timeout(self):
        """Check and close timed-out clients."""
        to_close = []
        for sock, client in list(self.cli_socks.items()):
            client.m_timeout -= 1
            if client.m_timeout <= 0 or client.m_ForceCli:
                to_close.append(sock)

        for sock in to_close:
            self._force_close_cli(sock)

    def _cleanup(self):
        """Close all connections on shutdown."""
        for sock in list(self.cli_socks.keys()):
            self._force_close_cli(sock)

        if self.srv_sock:
            try:
                self.srv_sock.close()
            except Exception:
                pass
            self.srv_sock = None
