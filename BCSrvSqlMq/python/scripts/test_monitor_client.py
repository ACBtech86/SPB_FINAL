#!/usr/bin/env python3
"""
Test client for BCSrvSqlMq TCP Monitor.

Connects to the Monitor port (default 14499) and sends test messages
using the COMHDR binary protocol.

Usage:
    python test_monitor_client.py [host] [port]

Examples:
    python test_monitor_client.py                    # localhost:14499
    python test_monitor_client.py localhost 15000    # custom port
"""

import socket
import struct
import sys
import time

# COMHDR format: usMsgLength(2) + ucIdHeader(4) + ucFuncSgr(1) + usRc(2) + usDatLength(2)
COMHDR_FORMAT = '<H4sBHH'
COMHDR_SIZE = struct.calcsize(COMHDR_FORMAT)  # 11 bytes

FUNC_POST = 0x01
FUNC_NOP = 0xFF


def pack_comhdr(msg_length, id_header=b'\x00\x00\x00\x00', func=FUNC_NOP,
                rc=0, dat_length=0):
    """Pack a COMHDR message."""
    return struct.pack(COMHDR_FORMAT, msg_length, id_header[:4], func, rc, dat_length)


def unpack_comhdr(data):
    """Unpack a COMHDR response."""
    if len(data) < COMHDR_SIZE:
        return None
    values = struct.unpack(COMHDR_FORMAT, data[:COMHDR_SIZE])
    return {
        'usMsgLength': values[0],
        'ucIdHeader': values[1],
        'ucFuncSgr': values[2],
        'usRc': values[3],
        'usDatLength': values[4],
    }


def send_nop(sock):
    """Send a NOP (keepalive) message."""
    print('[>] Sending NOP message...')
    msg = pack_comhdr(COMHDR_SIZE, func=FUNC_NOP)
    sock.sendall(msg)
    print('[<] NOP sent (no response expected)')


def send_post(sock, queue_name):
    """Send a POST message to trigger a task by queue name.

    The POST message includes the queue name (48 bytes) as payload.
    The monitor responds with usRc=0 if the task was found, or usRc=99 if not.
    """
    # Pad queue name to 48 bytes
    qn_bytes = queue_name.encode('latin-1').ljust(48, b' ')
    dat_length = len(qn_bytes)
    msg_length = COMHDR_SIZE + dat_length

    print(f'[>] Sending POST for queue: "{queue_name}"')
    hdr = pack_comhdr(msg_length, id_header=b'POST', func=FUNC_POST,
                      dat_length=dat_length)
    sock.sendall(hdr + qn_bytes)

    # Wait for response
    try:
        resp = sock.recv(1024)
        if resp:
            parsed = unpack_comhdr(resp)
            if parsed:
                rc = parsed['usRc']
                status = 'FOUND' if rc == 0 else f'NOT FOUND (rc={rc})'
                print(f'[<] POST response: {status}')
            else:
                print(f'[<] Raw response: {resp.hex()}')
        else:
            print('[<] No response (connection closed)')
    except socket.timeout:
        print('[<] Response timeout')


def interactive_session(host, port):
    """Run an interactive test session."""
    print(f'Connecting to BCSrvSqlMq Monitor at {host}:{port}...')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)

    try:
        sock.connect((host, port))
        print(f'Connected!\n')
    except ConnectionRefusedError:
        print(f'ERROR: Connection refused. Is the service running?')
        print(f'  Start with: python -m bcsrvsqlmq -d')
        return
    except socket.timeout:
        print(f'ERROR: Connection timed out.')
        return

    print('Available commands:')
    print('  nop              - Send NOP (keepalive)')
    print('  post <queue>     - Send POST to trigger task by queue name')
    print('  post-bacen-req   - POST to BacenReq task')
    print('  post-bacen-rsp   - POST to BacenRsp task')
    print('  post-if-req      - POST to IFReq task')
    print('  post-if-rsp      - POST to IFRsp task')
    print('  raw <hex>        - Send raw hex bytes')
    print('  quit             - Disconnect')
    print()

    # Default queue names from INI
    queues = {
        'post-bacen-req': 'QL.61377677.01.ENTRADA.BACEN',
        'post-bacen-rsp': 'QL.61377677.01.SAIDA.BACEN',
        'post-bacen-rep': 'QL.61377677.01.REPORT.BACEN',
        'post-bacen-sup': 'QL.61377677.01.SUPORTE.BACEN',
        'post-if-req':    'QL.61377677.01.ENTRADA.IF',
        'post-if-rsp':    'QL.61377677.01.SAIDA.IF',
        'post-if-rep':    'QL.61377677.01.REPORT.IF',
        'post-if-sup':    'QL.61377677.01.SUPORTE.IF',
    }

    try:
        while True:
            try:
                cmd = input('monitor> ').strip()
            except EOFError:
                break

            if not cmd:
                continue

            if cmd == 'quit' or cmd == 'exit':
                break

            if cmd == 'nop':
                send_nop(sock)

            elif cmd.startswith('post '):
                queue_name = cmd[5:].strip()
                send_post(sock, queue_name)

            elif cmd in queues:
                send_post(sock, queues[cmd])

            elif cmd.startswith('raw '):
                hex_str = cmd[4:].strip().replace(' ', '')
                try:
                    raw_bytes = bytes.fromhex(hex_str)
                    print(f'[>] Sending {len(raw_bytes)} raw bytes')
                    sock.sendall(raw_bytes)
                    time.sleep(0.5)
                    try:
                        resp = sock.recv(1024)
                        print(f'[<] Response: {resp.hex()}')
                    except socket.timeout:
                        print('[<] No response')
                except ValueError:
                    print('Invalid hex string')

            else:
                print(f'Unknown command: {cmd}')

    except (BrokenPipeError, ConnectionResetError):
        print('\nConnection lost.')
    finally:
        sock.close()
        print('Disconnected.')


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 14499

    interactive_session(host, port)


if __name__ == '__main__':
    main()
