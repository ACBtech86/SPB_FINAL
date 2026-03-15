#!/usr/bin/env python3
"""
End-to-End Full System Test for SPB

Tests the complete message flow through all servers:
  1. PostgreSQL    - Database storage
  2. IBM MQ        - Message queuing
  3. BCSrvSqlMq    - Message processing service (8 worker threads)
  4. SPBSite       - Web interface (FastAPI)
  5. BACEN Auto-Responder - Simulated BACEN responses

Flow tested:
  SPBSite/DB INSERT → BCSrvSqlMq picks up (flag P→E) → MQ PUT →
  Auto-Responder reads → generates response → MQ PUT →
  BCSrvSqlMq picks up → DB INSERT (spb_bacen_to_local)

Usage:
  python test_scripts/e2e_full_system_test.py
"""

import os
import sys
import time
import subprocess
import signal
from datetime import datetime

import psycopg2
import pymqi
import pymqi.CMQC

# ── Configuration ──────────────────────────────────────────────
DB_CONFIG = {
    "dbname": "BanuxSPB",
    "user": "postgres",
    "password": "Rama1248",
    "host": "localhost",
    "port": 5432,
}

MQ_CONFIG = {
    "qm_name": "QM.36266751.01",
    "channel": "FINVEST.SVRCONN",
    "conn_info": "localhost(1414)",
}

SPBSITE_URL = "http://localhost:8000"
ISPB_LOCAL = "36266751"
ISPB_BACEN = "00038166"

# ── Helpers ────────────────────────────────────────────────────
class Colors:
    OK = "\033[0;32m"
    FAIL = "\033[0;31m"
    WARN = "\033[1;33m"
    INFO = "\033[0;36m"
    NC = "\033[0m"

def ok(msg):
    print(f"  {Colors.OK}[PASS]{Colors.NC} {msg}")

def fail(msg):
    print(f"  {Colors.FAIL}[FAIL]{Colors.NC} {msg}")

def info(msg):
    print(f"  {Colors.INFO}[INFO]{Colors.NC} {msg}")

def section(title):
    print(f"\n{Colors.WARN}{'='*60}")
    print(f" {title}")
    print(f"{'='*60}{Colors.NC}")


# ── Test Steps ─────────────────────────────────────────────────
results = []

def check(name, condition, detail=""):
    if condition:
        ok(f"{name} {detail}")
        results.append((name, True))
    else:
        fail(f"{name} {detail}")
        results.append((name, False))
    return condition


def test_1_services_running():
    """Verify all required services are up."""
    section("1. Service Health Checks")

    # PostgreSQL
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        check("PostgreSQL", True, "connected OK")
    except Exception as e:
        check("PostgreSQL", False, str(e))
        return False

    # IBM MQ
    try:
        cd = pymqi.CD()
        cd.ChannelName = MQ_CONFIG["channel"].encode()
        cd.ConnectionName = MQ_CONFIG["conn_info"].encode()
        cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
        cd.TransportType = pymqi.CMQC.MQXPT_TCP
        qm = pymqi.QueueManager(None)
        qm.connect_with_options(MQ_CONFIG["qm_name"], cd)
        qm.disconnect()
        check("IBM MQ", True, f"QM {MQ_CONFIG['qm_name']} connected")
    except Exception as e:
        check("IBM MQ", False, str(e))
        return False

    # BCSrvSqlMq
    try:
        r = subprocess.run(["pgrep", "-f", "bcsrvsqlmq"], capture_output=True)
        running = r.returncode == 0
        check("BCSrvSqlMq", running, "process running" if running else "NOT running")
    except Exception as e:
        check("BCSrvSqlMq", False, str(e))

    # SPBSite
    try:
        import httpx
        r = httpx.get(f"{SPBSITE_URL}/login", timeout=5)
        check("SPBSite", r.status_code == 200, f"HTTP {r.status_code}")
    except Exception as e:
        check("SPBSite", False, str(e))

    return True


def test_2_spbsite_login():
    """Test SPBSite authentication."""
    section("2. SPBSite Login")
    try:
        import httpx
        client = httpx.Client(follow_redirects=False, base_url=SPBSITE_URL)
        r = client.post("/login", data={"username": "admin", "password": "admin"})
        logged_in = r.status_code == 303
        check("Login", logged_in, f"→ {r.headers.get('location', '')}")

        # Verify session by accessing protected page
        r2 = client.get("/monitoring/control/local")
        check("Session", r2.status_code == 200, "monitoring page accessible")
        client.close()
        return True
    except Exception as e:
        check("Login", False, str(e))
        return False


def test_3_insert_outbound_message():
    """Insert a test message into spb_local_to_bacen (simulates form submission)."""
    section("3. Insert Outbound Message (DB)")

    now = datetime.now()
    nu_ope = now.strftime("E2E%Y%m%d%H%M%S")
    msg_id = "GEN0001"
    queue_name = f"QL.{ISPB_LOCAL}.01.ENTRADA.IF"

    xml_msg = f"""<?xml version="1.0"?><!DOCTYPE SPBDOC SYSTEM "SPBDOC.DTD"><SPBDOC><BCMSG><Grupo_EmissorMsg><TipoId_Emissor>P</TipoId_Emissor><Id_Emissor>{ISPB_LOCAL}</Id_Emissor></Grupo_EmissorMsg><DestinatarioMsg><TipoId_Destinatario>P</TipoId_Destinatario><Id_Destinatario>{ISPB_BACEN}</Id_Destinatario></DestinatarioMsg><NUOp>{nu_ope}</NUOp></BCMSG><SISMSG><GEN0001><SitRetReq>1</SitRetReq><DtHrMsg>{now.strftime('%Y%m%d%H%M%S')}</DtHrMsg></GEN0001></SISMSG></SPBDOC>"""

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO spb_local_to_bacen
               (db_datetime, status_msg, flag_proc, mq_qn_destino, nu_ope, cod_msg, msg)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (now, "P", "P", queue_name, nu_ope, msg_id, xml_msg),
        )
        conn.commit()

        # Verify insertion
        cur.execute(
            "SELECT flag_proc FROM spb_local_to_bacen WHERE nu_ope = %s", (nu_ope,)
        )
        row = cur.fetchone()
        check("Insert outbound", row is not None, f"nu_ope={nu_ope}, flag='{row[0]}'")
        conn.close()
        return nu_ope
    except Exception as e:
        check("Insert outbound", False, str(e))
        return None


def test_4_bcsrvsqlmq_picks_up(nu_ope, timeout=15):
    """Wait for BCSrvSqlMq to pick up the message (flag P → E)."""
    section("4. BCSrvSqlMq Outbound Processing (flag P → E)")

    info(f"Waiting up to {timeout}s for BCSrvSqlMq to process nu_ope={nu_ope}...")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for i in range(timeout):
        cur.execute(
            "SELECT flag_proc, mq_msg_id FROM spb_local_to_bacen WHERE nu_ope = %s",
            (nu_ope,),
        )
        row = cur.fetchone()
        if row and row[0] == "E":
            check("Outbound processed", True, f"flag='E', mq_msg_id={row[1]}")
            conn.close()
            return True
        time.sleep(1)

    cur.execute(
        "SELECT flag_proc FROM spb_local_to_bacen WHERE nu_ope = %s", (nu_ope,)
    )
    row = cur.fetchone()
    flag = row[0] if row else "?"
    check("Outbound processed", False, f"flag still '{flag}' after {timeout}s")
    conn.close()
    return False


def test_5_mq_message_routed():
    """Verify MQ queues are operational."""
    section("5. IBM MQ Queue Status")

    try:
        cd = pymqi.CD()
        cd.ChannelName = MQ_CONFIG["channel"].encode()
        cd.ConnectionName = MQ_CONFIG["conn_info"].encode()
        cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
        cd.TransportType = pymqi.CMQC.MQXPT_TCP
        qm = pymqi.QueueManager(None)
        qm.connect_with_options(MQ_CONFIG["qm_name"], cd)

        # Check key queues
        for qname in [
            f"QL.{ISPB_LOCAL}.01.ENTRADA.IF",
            f"QL.RSP.{ISPB_BACEN}.{ISPB_LOCAL}.01",
        ]:
            try:
                q = pymqi.Queue(qm, qname, pymqi.CMQC.MQOO_INQUIRE)
                depth = q.inquire(pymqi.CMQC.MQIA_CURRENT_Q_DEPTH)
                q.close()
                check(f"Queue {qname}", True, f"depth={depth}")
            except pymqi.MQMIError as e:
                if e.reason == pymqi.CMQC.MQRC_UNKNOWN_OBJECT_NAME:
                    check(f"Queue {qname}", False, "does not exist")
                else:
                    check(f"Queue {qname}", False, str(e))

        qm.disconnect()
        return True
    except Exception as e:
        check("MQ queues", False, str(e))
        return False


def test_6_bacen_auto_responder(nu_ope, timeout=20):
    """Start BACEN auto-responder and wait for response in DB."""
    section("6. BACEN Auto-Responder → Inbound Response")

    # Start auto-responder as subprocess
    responder_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "BCSrvSqlMq",
        "bacen_auto_responder.py",
    )

    info(f"Starting BACEN auto-responder for {timeout}s...")
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/opt/mqm/lib64:/opt/mqm/lib:" + env.get("LD_LIBRARY_PATH", "")
    proc = subprocess.Popen(
        [sys.executable, responder_path],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        # Wait for response to appear in spb_bacen_to_local
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        for i in range(timeout):
            cur.execute(
                "SELECT cod_msg, flag_proc, nu_ope FROM spb_bacen_to_local ORDER BY db_datetime DESC LIMIT 5"
            )
            rows = cur.fetchall()
            if rows:
                info(f"Found {len(rows)} inbound message(s)")
                for row in rows:
                    info(f"  cod_msg={row[0]}, flag={row[1]}, nu_ope={row[2]}")
                check("Inbound response received", True, f"{len(rows)} message(s) in spb_bacen_to_local")
                conn.close()
                return True
            time.sleep(1)

        check("Inbound response received", False, f"no messages after {timeout}s")
        conn.close()
        return False
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            out, _ = proc.communicate(timeout=5)
            if out:
                info("Auto-responder output:")
                for line in out.decode(errors="replace").strip().split("\n")[-10:]:
                    print(f"    {line}")
        except subprocess.TimeoutExpired:
            proc.kill()


def test_7_spbsite_monitoring():
    """Verify messages are visible via SPBSite monitoring pages."""
    section("7. SPBSite Monitoring Verification")

    try:
        import httpx
        client = httpx.Client(follow_redirects=True, base_url=SPBSITE_URL)
        # Login
        client.post("/login", data={"username": "admin", "password": "admin"})

        # Check outbound messages
        r = client.get("/monitoring/messages/outbound/bacen")
        has_outbound = r.status_code == 200
        check("Outbound monitoring page", has_outbound, f"HTTP {r.status_code}")

        # Check inbound messages
        r = client.get("/monitoring/messages/inbound/bacen")
        has_inbound = r.status_code == 200
        check("Inbound monitoring page", has_inbound, f"HTTP {r.status_code}")

        client.close()
        return True
    except Exception as e:
        check("SPBSite monitoring", False, str(e))
        return False


def test_8_database_audit():
    """Verify audit log entries were created."""
    section("8. Database Audit Trail")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Check outbound messages
        cur.execute("SELECT COUNT(*) FROM spb_local_to_bacen")
        outbound = cur.fetchone()[0]
        check("Outbound records", outbound > 0, f"{outbound} record(s)")

        # Check flag status
        cur.execute("SELECT flag_proc, COUNT(*) FROM spb_local_to_bacen GROUP BY flag_proc")
        flags = dict(cur.fetchall())
        info(f"Flag distribution: {flags}")

        # Check inbound messages
        cur.execute("SELECT COUNT(*) FROM spb_bacen_to_local")
        inbound = cur.fetchone()[0]
        check("Inbound records", inbound > 0, f"{inbound} record(s)")

        # Check log
        cur.execute("SELECT COUNT(*) FROM spb_log_bacen")
        logs = cur.fetchone()[0]
        info(f"Audit log entries: {logs}")

        conn.close()
        return True
    except Exception as e:
        check("Audit trail", False, str(e))
        return False


# ── Main ───────────────────────────────────────────────────────
def main():
    print(f"\n{'#'*60}")
    print(f"#  SPB End-to-End Full System Test")
    print(f"#  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    # 1. Check services
    if not test_1_services_running():
        print("\n[ABORT] Required services are not running.")
        return 1

    # 2. SPBSite login
    test_2_spbsite_login()

    # 3. Insert outbound message
    nu_ope = test_3_insert_outbound_message()
    if not nu_ope:
        print("\n[ABORT] Failed to insert test message.")
        return 1

    # 4. Wait for BCSrvSqlMq to process
    picked_up = test_4_bcsrvsqlmq_picks_up(nu_ope)

    # 5. Check MQ queues
    test_5_mq_message_routed()

    # 6. BACEN auto-responder (only if message was picked up)
    if picked_up:
        test_6_bacen_auto_responder(nu_ope)
    else:
        section("6. BACEN Auto-Responder (SKIPPED)")
        info("Skipped — outbound message was not processed by BCSrvSqlMq")

    # 7. SPBSite monitoring
    test_7_spbsite_monitoring()

    # 8. Audit trail
    test_8_database_audit()

    # ── Summary ────────────────────────────────────────────────
    section("SUMMARY")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    failed = total - passed

    for name, ok in results:
        status = f"{Colors.OK}PASS{Colors.NC}" if ok else f"{Colors.FAIL}FAIL{Colors.NC}"
        print(f"  [{status}] {name}")

    print(f"\n  {Colors.OK}{passed} passed{Colors.NC}, ", end="")
    if failed:
        print(f"{Colors.FAIL}{failed} failed{Colors.NC}", end="")
    else:
        print(f"0 failed", end="")
    print(f" out of {total} checks")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
