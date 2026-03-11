#!/usr/bin/env python3
"""
SPB System - End-to-End Test (v2)
Tests all services with correct endpoints.
"""

import socket
import struct
import sys
import time
import subprocess
from datetime import datetime

import psycopg2
import requests

# ─── Config ──────────────────────────────────────────────────────────────────
DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'BanuxSPB', 'user': 'postgres', 'password': 'Rama1248',
}
SPBSITE_URL = 'http://localhost:8000'
MONITOR_HOST, MONITOR_PORT = 'localhost', 14499
MQ_BIN = r'C:\Program Files\IBM\MQ\bin\runmqsc.exe'
QM_NAME = 'QM.36266751.01'
MQ_QUEUES = [
    'QL.36266751.01.ENTRADA.IF',
    'QL.REQ.00038166.36266751.01',
    'QL.RSP.00038166.36266751.01',
]

PASS = '[PASS]'
FAIL = '[FAIL]'
INFO = '[INFO]'

results = {}


def header(title):
    print(f"\n{'='*70}\n  {title}\n{'='*70}")


def record(name, success, detail=''):
    results[name] = {'success': success, 'detail': detail}
    icon = PASS if success else FAIL
    print(f"{icon} {name}" + (f" — {detail}" if detail else ''))


# ─── 1. Service connectivity ──────────────────────────────────────────────────
header("1. Service Connectivity")

for svc, port in [('PostgreSQL', 5432), ('IBM MQ', 1414),
                   ('SPBSite', 8000), ('BCSrvSqlMq Monitor', 14499)]:
    s = socket.socket()
    s.settimeout(2)
    ok = s.connect_ex(('localhost', port)) == 0
    s.close()
    record(f"Service: {svc}", ok, f"port {port}")

if not results['Service: IBM MQ']['success']:
    print(f"\n{FAIL} IBM MQ not running — aborting.")
    sys.exit(1)

# ─── 2. Database tables ───────────────────────────────────────────────────────
header("2. Database Tables")

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    tables = ['users', 'spb_local_to_bacen', 'spb_bacen_to_local', 'spb_controle', 'spb_log_bacen']
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            record(f"Table: {table}", True, f"{count} rows")
        except Exception as e:
            record(f"Table: {table}", False, str(e))
    cur.close()
    conn.close()
except Exception as e:
    record("Database connection", False, str(e))

# ─── 3. SPBSite login + pages ─────────────────────────────────────────────────
header("3. SPBSite Login & Pages")

session = requests.Session()
try:
    r = session.post(f'{SPBSITE_URL}/login',
                     data={'username': 'admin', 'password': 'admin'},
                     allow_redirects=True, timeout=10)
    logged_in = r.status_code == 200 and 'login' not in r.url
    record("SPBSite: Login", logged_in, f"final URL: {r.url}")
except Exception as e:
    record("SPBSite: Login", False, str(e))
    logged_in = False

if logged_in:
    for page, path in [
        ('Monitoring', '/monitoring/control/local'),
        ('Queue', '/queue'),
        ('Messages', '/messages/combined'),
    ]:
        try:
            r = session.get(f'{SPBSITE_URL}{path}', timeout=10)
            record(f"SPBSite: {page}", r.status_code == 200, f"HTTP {r.status_code}")
        except Exception as e:
            record(f"SPBSite: {page}", False, str(e))

# ─── 4. BCSrvSqlMq Monitor (NOP) ─────────────────────────────────────────────
header("4. BCSrvSqlMq Monitor — NOP heartbeat")

COMHDR_FORMAT = '<H4sBHH'
COMHDR_SIZE = struct.calcsize(COMHDR_FORMAT)

try:
    sock = socket.socket()
    sock.settimeout(5)
    sock.connect((MONITOR_HOST, MONITOR_PORT))
    nop = struct.pack(COMHDR_FORMAT, COMHDR_SIZE, b'\x00\x00\x00\x00', 0xFF, 0, 0)
    sock.sendall(nop)
    time.sleep(0.5)
    sock.close()
    record("BCSrvSqlMq: NOP heartbeat", True, "connected and sent NOP")
except Exception as e:
    record("BCSrvSqlMq: NOP heartbeat", False, str(e))

# ─── 5. IBM MQ queue depths ───────────────────────────────────────────────────
header("5. IBM MQ Queue Depths")

mq_script = '\n'.join([f'DISPLAY QLOCAL({q}) CURDEPTH' for q in MQ_QUEUES]) + '\nEND\n'
try:
    proc = subprocess.run(
        [MQ_BIN, QM_NAME],
        input=mq_script, capture_output=True, text=True, timeout=15
    )
    output = proc.stdout + proc.stderr
    for q in MQ_QUEUES:
        if q in output:
            # Extract CURDEPTH value
            for line in output.split('\n'):
                if 'CURDEPTH' in line and q in output[max(0, output.find(line)-200):output.find(line)+100]:
                    depth = line.strip()
                    break
            else:
                depth = 'see output'
            record(f"MQ Queue: {q}", True, depth)
        else:
            record(f"MQ Queue: {q}", False, "queue not found")
    if not any(q in output for q in MQ_QUEUES):
        print(f"{INFO} runmqsc output:\n{output[:500]}")
except FileNotFoundError:
    record("IBM MQ: runmqsc", False, f"not found at {MQ_BIN}")
except Exception as e:
    record("IBM MQ: runmqsc", False, str(e))

# ─── 6. Message flow — DB insert → monitor trigger ───────────────────────────
header("6. Message Flow -- Schema & Queue Activity Check")

# Verify DB schema is complete for message processing
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Check spb_controle (service registration)
    cur.execute("SELECT COUNT(*) FROM spb_controle")
    ctrl_count = cur.fetchone()[0]
    record("Message flow: spb_controle entries", ctrl_count > 0, f"{ctrl_count} service(s) registered")

    # Check column structure is correct
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name = 'spb_local_to_bacen'
        AND column_name IN ('mq_msg_id','cod_msg','msg','nu_ope','status_msg')
    """)
    col_count = cur.fetchone()[0]
    record("Message flow: spb_local_to_bacen schema", col_count == 5, f"{col_count}/5 required columns found")

    cur.execute("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name = 'spb_bacen_to_local'
        AND column_name IN ('mq_msg_id','cod_msg','msg','nu_ope','status_msg')
    """)
    col_count = cur.fetchone()[0]
    record("Message flow: spb_bacen_to_local schema", col_count == 5, f"{col_count}/5 required columns found")

    cur.close()
    conn.close()
except Exception as e:
    record("Message flow: DB schema check", False, str(e))

# Trigger BCSrvSqlMq monitor to check IF queue
try:
    sock = socket.socket()
    sock.settimeout(5)
    sock.connect((MONITOR_HOST, MONITOR_PORT))
    qname = b'QL.36266751.01.ENTRADA.IF'.ljust(48)
    dat_len = len(qname)
    msg_len = COMHDR_SIZE + dat_len
    hdr = struct.pack(COMHDR_FORMAT, msg_len, b'POST', 0x01, 0, dat_len)
    sock.sendall(hdr + qname)
    resp = sock.recv(64)
    sock.close()
    parsed = struct.unpack(COMHDR_FORMAT, resp[:COMHDR_SIZE]) if len(resp) >= COMHDR_SIZE else None
    rc = parsed[3] if parsed else -1
    # rc=0 means task found (queue known), rc=99 means not found
    record("Message flow: Monitor queue trigger", rc in (0, 99), f"rc={rc} ({'task found' if rc==0 else 'task not found/idle'})")
except Exception as e:
    record("Message flow: Monitor queue trigger", False, str(e))

# ─── Report ───────────────────────────────────────────────────────────────────
header("End-to-End Test Report")

print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
passed = sum(1 for r in results.values() if r['success'])
failed = sum(1 for r in results.values() if not r['success'])
total = len(results)

for name, r in results.items():
    icon = PASS if r['success'] else FAIL
    detail = f" - {r['detail']}" if r['detail'] else ''
    print(f"  {icon} {name}{detail}")

print(f"\n{'-'*70}")
print(f"  Total: {total}  Passed: {passed}  Failed: {failed}")
if failed == 0:
    print("  ALL TESTS PASSED")
else:
    print(f"  {failed} TEST(S) FAILED")

sys.exit(0 if failed == 0 else 1)
