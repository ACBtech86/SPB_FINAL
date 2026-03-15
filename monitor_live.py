#!/usr/bin/env python3
"""
SPB Live Flow Monitor — Event-based visual monitor

Prints a static header with the flow diagram, then only prints
timestamped events when something actually changes in the system.

Usage:
    python monitor_live.py                # monitor only
    python monitor_live.py --inject       # inject a test GEN0001 and monitor
    python monitor_live.py --inject --auto-respond  # inject + start auto-responder
"""

import os
import sys
import time
import signal
import argparse
import subprocess
import threading
from datetime import datetime

import psycopg2
import pymqi
import pymqi.CMQC

# ── Config ─────────────────────────────────────────────────────
DB = dict(dbname="BanuxSPB", user="postgres", password="Rama1248", host="localhost", port=5432)
MQ = dict(qm="QM.36266751.01", channel="FINVEST.SVRCONN", conn="localhost(1414)")
ISPB_LOCAL = "36266751"
ISPB_BACEN = "00038166"

# ── Colors ─────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    GREEN   = "\033[38;5;46m"
    RED     = "\033[38;5;196m"
    YELLOW  = "\033[38;5;220m"
    CYAN    = "\033[38;5;51m"
    BLUE    = "\033[38;5;33m"
    MAGENTA = "\033[38;5;207m"
    ORANGE  = "\033[38;5;208m"
    WHITE   = "\033[38;5;255m"
    GRAY    = "\033[38;5;240m"

def col(text, color):
    return f"{color}{text}{C.RESET}"

def ts():
    return col(datetime.now().strftime("%H:%M:%S"), C.DIM)

# ── Data Collection ────────────────────────────────────────────
def get_db_snapshot():
    try:
        conn = psycopg2.connect(**DB)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM spb_local_to_bacen")
        out_total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM spb_local_to_bacen WHERE flag_proc = 'P'")
        out_pending = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM spb_local_to_bacen WHERE flag_proc = 'E'")
        out_sent = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM spb_bacen_to_local")
        in_total = cur.fetchone()[0]
        cur.execute("SELECT nu_ope, cod_msg, flag_proc, db_datetime FROM spb_local_to_bacen ORDER BY db_datetime DESC LIMIT 1")
        last_out = cur.fetchone()
        cur.execute("SELECT nu_ope, cod_msg, flag_proc, db_datetime FROM spb_bacen_to_local ORDER BY db_datetime DESC LIMIT 1")
        last_in = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM spb_log_bacen")
        log_count = cur.fetchone()[0]
        conn.close()
        return {
            "ok": True, "out_total": out_total, "out_pending": out_pending,
            "out_sent": out_sent, "in_total": in_total, "last_out": last_out,
            "last_in": last_in, "log_count": log_count,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_mq_depths():
    queues = [
        ("ENTRADA.IF", f"QL.{ISPB_LOCAL}.01.ENTRADA.IF"),
        ("SAIDA.IF",   f"QL.{ISPB_LOCAL}.01.SAIDA.IF"),
        ("REPORT.IF",  f"QL.{ISPB_LOCAL}.01.REPORT.IF"),
        ("SUPORTE.IF", f"QL.{ISPB_LOCAL}.01.SUPORTE.IF"),
        ("BACEN REQ",  f"QL.REQ.{ISPB_BACEN}.{ISPB_LOCAL}.01"),
        ("BACEN RSP",  f"QL.RSP.{ISPB_BACEN}.{ISPB_LOCAL}.01"),
        ("BACEN REP",  f"QL.REP.{ISPB_BACEN}.{ISPB_LOCAL}.01"),
        ("BACEN SUP",  f"QL.SUP.{ISPB_BACEN}.{ISPB_LOCAL}.01"),
    ]
    try:
        cd = pymqi.CD()
        cd.ChannelName = MQ["channel"].encode()
        cd.ConnectionName = MQ["conn"].encode()
        cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
        cd.TransportType = pymqi.CMQC.MQXPT_TCP
        qm = pymqi.QueueManager(None)
        qm.connect_with_options(MQ["qm"], cd)
        depths = {}
        for label, qname in queues:
            try:
                q = pymqi.Queue(qm, qname, pymqi.CMQC.MQOO_INQUIRE)
                depths[label] = q.inquire(pymqi.CMQC.MQIA_CURRENT_Q_DEPTH)
                q.close()
            except Exception:
                depths[label] = -1
        qm.disconnect()
        return depths
    except Exception:
        return {}


def check_service(name):
    try:
        return subprocess.run(["pgrep", "-f", name], capture_output=True).returncode == 0
    except Exception:
        return False


def get_last_log_line():
    log_dir = "/home/ubuntu/SPBFinal/SPB_FINAL/BCSrvSqlMq/Traces"
    log_file = os.path.join(log_dir, f"TRACE_SPB__{datetime.now().strftime('%Y%m%d')}.log")
    try:
        with open(log_file, "r", encoding="latin-1") as f:
            lines = f.readlines()
            # Find last meaningful line
            for line in reversed(lines):
                stripped = line.rstrip()
                if stripped and not stripped.startswith("==="):
                    return stripped
            return ""
    except Exception:
        return ""


# ── Inject ─────────────────────────────────────────────────────
def inject_message():
    now = datetime.now()
    nu_ope = now.strftime("LIVE%Y%m%d%H%M%S")
    xml = (
        f'<?xml version="1.0"?><!DOCTYPE SPBDOC SYSTEM "SPBDOC.DTD">'
        f'<SPBDOC><BCMSG>'
        f'<Grupo_EmissorMsg><TipoId_Emissor>P</TipoId_Emissor>'
        f'<Id_Emissor>{ISPB_LOCAL}</Id_Emissor></Grupo_EmissorMsg>'
        f'<DestinatarioMsg><TipoId_Destinatario>P</TipoId_Destinatario>'
        f'<Id_Destinatario>{ISPB_BACEN}</Id_Destinatario></DestinatarioMsg>'
        f'<NUOp>{nu_ope}</NUOp></BCMSG>'
        f'<SISMSG><GEN0001><SitRetReq>1</SitRetReq>'
        f'<DtHrMsg>{now.strftime("%Y%m%d%H%M%S")}</DtHrMsg>'
        f'</GEN0001></SISMSG></SPBDOC>'
    )
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO spb_local_to_bacen "
        "(db_datetime, status_msg, flag_proc, mq_qn_destino, nu_ope, cod_msg, msg) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (now, "P", "P", f"QL.{ISPB_LOCAL}.01.ENTRADA.IF", nu_ope, "GEN0001", xml),
    )
    conn.commit()
    conn.close()
    return nu_ope


# ── Auto-responder in background ──────────────────────────────
def start_auto_responder():
    responder_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "BCSrvSqlMq", "bacen_auto_responder.py",
    )
    # Run a small wrapper that calls run_continuous with a long duration
    # so it stays alive as long as the monitor is running
    wrapper = (
        f"import sys; sys.path.insert(0, '{os.path.dirname(responder_path)}'); "
        f"from bacen_auto_responder import BacenAutoResponder; "
        f"r = BacenAutoResponder(); r.run_continuous(duration_seconds=3600, poll_interval=1.0)"
    )
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/opt/mqm/lib64:/opt/mqm/lib:" + env.get("LD_LIBRARY_PATH", "")
    proc = subprocess.Popen(
        [sys.executable, "-c", wrapper],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    return proc


# ── Print Header ───────────────────────────────────────────────
def print_header():
    print()
    print(col("  ╔══════════════════════════════════════════════════════════════════╗", C.BLUE))
    print(col("  ║", C.BLUE) + col("           SPB LIVE FLOW MONITOR", C.BOLD + C.WHITE) + "                          " + col("║", C.BLUE))
    print(col("  ╚══════════════════════════════════════════════════════════════════╝", C.BLUE))
    print()
    print(col("  MESSAGE FLOW:", C.BOLD + C.WHITE))
    print()
    print(f"   {col('SPBSite', C.CYAN)}  ━━▶  {col('PostgreSQL', C.MAGENTA)}  ━━▶  {col('BCSrvSqlMq', C.ORANGE)}  ━━▶  {col('MQ Queues', C.YELLOW)}  ━━▶  {col('BACEN', C.GREEN)}")
    print(f"   {col(':8000', C.DIM)}         {col('BanuxSPB', C.DIM)}       {col('8 threads', C.DIM)}        {col('port 1414', C.DIM)}       {col('simulator', C.DIM)}")
    print(f"                                                         {col('◀━━━━━━━━━━━━', C.CYAN)}  {col('response', C.DIM)}")
    print()

    # Service check
    services = [
        ("PostgreSQL", check_service("postgres")),
        ("IBM MQ", check_service("amqzxma0")),
        ("BCSrvSqlMq", check_service("bcsrvsqlmq")),
        ("SPBSite", check_service("uvicorn")),
    ]
    svc_line = "  SERVICES: "
    for name, up in services:
        icon = col("●", C.GREEN) if up else col("●", C.RED)
        svc_line += f" {icon} {name}  "
    print(svc_line)
    print()
    print(col("  ─────────────────────────────────────────────────────────────────", C.DIM))
    print(f"  {col('TIME', C.DIM):>18}  {col('EVENT', C.BOLD + C.WHITE)}")
    print(col("  ─────────────────────────────────────────────────────────────────", C.DIM))


def event(icon, color, msg):
    """Print a single event line."""
    print(f"  {ts()}  {col(icon, color)}  {msg}")


# ── Main Loop ─────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="SPB Live Flow Monitor")
    parser.add_argument("--inject", action="store_true", help="Inject a test GEN0001 message")
    parser.add_argument("--no-responder", action="store_true", help="Do NOT start BACEN auto-responder")
    args = parser.parse_args()

    def cleanup(sig=None, frame=None):
        if responder_proc and responder_proc.poll() is None:
            responder_proc.terminate()
        print(f"\n\n  {col('Monitor stopped.', C.DIM)}\n")
        sys.exit(0)
    signal.signal(signal.SIGINT, cleanup)

    print_header()

    # Always start auto-responder unless --no-responder
    responder_proc = None
    if not args.no_responder:
        responder_proc = start_auto_responder()
        event("▶", C.GREEN, f"BACEN Auto-Responder {col('started', C.GREEN)} (PID {responder_proc.pid})")
    else:
        event("▷", C.DIM, f"BACEN Auto-Responder {col('disabled', C.DIM)} (use without --no-responder to enable)")

    # Inject test message if requested
    if args.inject:
        nu_ope = inject_message()
        event("✉", C.CYAN, f"Test message {col('injected', C.BOLD + C.CYAN)}: GEN0001  nu_ope={col(nu_ope, C.WHITE)}")

    # State tracking — only print when something changes
    prev = {
        "out_pending": -1,
        "out_sent": -1,
        "out_total": -1,
        "in_total": -1,
        "log_count": -1,
        "depths": {},
        "last_log": "",
        "bcsrv_up": None,
        "spbsite_up": None,
    }

    event("◉", C.BLUE, f"Monitoring started. {col('Waiting for events...', C.DIM)}")

    while True:
        # ── Collect state ──
        db = get_db_snapshot()
        depths = get_mq_depths()
        last_log = get_last_log_line()
        bcsrv_up = check_service("bcsrvsqlmq")
        spbsite_up = check_service("uvicorn")

        if not db.get("ok"):
            if prev.get("db_ok", True):
                event("✗", C.RED, f"PostgreSQL {col('connection lost', C.RED)}: {db.get('error', '?')}")
            prev["db_ok"] = False
            time.sleep(2)
            continue
        prev["db_ok"] = True

        # ── Service status changes ──
        if bcsrv_up != prev["bcsrv_up"] and prev["bcsrv_up"] is not None:
            if bcsrv_up:
                event("●", C.GREEN, f"BCSrvSqlMq {col('started', C.GREEN)}")
            else:
                event("●", C.RED, f"BCSrvSqlMq {col('stopped', C.RED)}")
        prev["bcsrv_up"] = bcsrv_up

        if spbsite_up != prev["spbsite_up"] and prev["spbsite_up"] is not None:
            if spbsite_up:
                event("●", C.GREEN, f"SPBSite {col('started', C.GREEN)}")
            else:
                event("●", C.RED, f"SPBSite {col('stopped', C.RED)}")
        prev["spbsite_up"] = spbsite_up

        # ── DB changes ──
        out_t = db["out_total"]
        out_p = db["out_pending"]
        out_s = db["out_sent"]
        in_t = db["in_total"]
        log_c = db["log_count"]

        last = db.get("last_out")
        nu = last[0] if last else "?"
        cod = last[1] if last else "?"

        # Detect new outbound message (total increased)
        # This catches even fast P→E transitions that we'd miss checking pending alone
        if out_t > prev["out_total"] and prev["out_total"] >= 0:
            if out_p > prev["out_pending"]:
                # Still pending — BCSrvSqlMq hasn't picked it up yet
                event("①", C.YELLOW,
                      f"DB INSERT  {col(cod, C.BOLD + C.WHITE)}  "
                      f"nu_ope={col(nu, C.WHITE)}  flag={col('P', C.YELLOW)}  "
                      f"{col('→ waiting for BCSrvSqlMq', C.DIM)}")
            else:
                # Already processed (fast P→E) — show both steps
                event("①", C.YELLOW,
                      f"DB INSERT  {col(cod, C.BOLD + C.WHITE)}  "
                      f"nu_ope={col(nu, C.WHITE)}  flag={col('P', C.YELLOW)}")
                event("②", C.GREEN,
                      f"BCSrvSqlMq {col('PROCESSED', C.BOLD + C.GREEN)}  "
                      f"flag={col('P', C.YELLOW)}→{col('E', C.GREEN)}  "
                      f"{col('→ signed, encrypted, sent to MQ', C.DIM)}")

        # Message processed by BCSrvSqlMq (sent increased, but total didn't — was pending before)
        elif out_s > prev["out_sent"] and prev["out_sent"] >= 0 and out_t == prev["out_total"]:
            event("②", C.GREEN,
                  f"BCSrvSqlMq {col('PROCESSED', C.BOLD + C.GREEN)}  {col(cod, C.WHITE)}  "
                  f"flag={col('P', C.YELLOW)}→{col('E', C.GREEN)}  "
                  f"{col('→ signed, encrypted, sent to MQ', C.DIM)}")

        # Inbound message received
        if in_t > prev["in_total"] and prev["in_total"] >= 0:
            last_in = db.get("last_in")
            in_nu = last_in[0] if last_in else "?"
            in_cod = last_in[1] if last_in else "?"
            diff = in_t - prev["in_total"]
            event("④", C.CYAN,
                  f"RESPONSE   {col(in_cod or '?', C.BOLD + C.WHITE)}  "
                  f"nu_ope={col(in_nu or '?', C.WHITE)}  "
                  f"{col('→ BACEN response stored in DB', C.DIM)}")
            if diff > 0:
                event("✓", C.GREEN,
                      f"{col('FLOW COMPLETE', C.BOLD + C.GREEN)}  "
                      f"outbound={out_s} sent, inbound={in_t} received")

        # Audit log entries
        if log_c > prev["log_count"] and prev["log_count"] >= 0:
            diff = log_c - prev["log_count"]
            event("📋", C.DIM, f"Audit log: {col(f'+{diff}', C.WHITE)} new entries (total: {log_c})")

        prev["out_total"] = out_t
        prev["out_pending"] = out_p
        prev["out_sent"] = out_s
        prev["in_total"] = in_t
        prev["log_count"] = log_c

        # ── MQ depth changes ──
        for label, depth in depths.items():
            old = prev["depths"].get(label, 0)
            if depth != old:
                if depth > old:
                    arrow = col(f"↑ {old}→{depth}", C.YELLOW)
                    # Detect auto-responder putting response on RSP queue
                    if "RSP" in label:
                        event("③", C.CYAN, f"MQ PUT     {col(label, C.WHITE)}  depth {arrow}  {col('→ BACEN response queued', C.CYAN)}")
                    else:
                        event("③", C.YELLOW, f"MQ PUT     {col(label, C.WHITE)}  depth {arrow}  {col('→ message waiting in queue', C.DIM)}")
                else:
                    arrow = col(f"↓ {old}→{depth}", C.GREEN)
                    if "RSP" in label:
                        event("③", C.GREEN, f"MQ GET     {col(label, C.WHITE)}  depth {arrow}  {col('→ BCSrvSqlMq picked up response', C.GREEN)}")
                    else:
                        event("③", C.GREEN, f"MQ GET     {col(label, C.WHITE)}  depth {arrow}  {col('→ message consumed from queue', C.DIM)}")
        prev["depths"] = dict(depths)

        # ── BCSrvSqlMq log changes ──
        if last_log and last_log != prev["last_log"]:
            # Extract the interesting part
            short = last_log
            if "] " in short:
                short = short.split("] ", 1)[-1]
            if len(short) > 80:
                short = short[:80] + "..."
            if "MQPUT" in last_log:
                event("⚡", C.GREEN, f"Log: {col(short, C.GREEN)}")
            elif "MQCMIT" in last_log:
                event("✓", C.GREEN, f"Log: {col(short, C.GREEN)}")
            elif "FAIL" in last_log or "Exception" in last_log:
                event("✗", C.RED, f"Log: {col(short, C.RED)}")
        prev["last_log"] = last_log

        # ── Auto-responder check — restart if it dies ──
        if responder_proc and responder_proc.poll() is not None:
            event("■", C.YELLOW, f"BACEN Auto-Responder stopped — {col('restarting...', C.YELLOW)}")
            responder_proc = start_auto_responder()
            event("▶", C.GREEN, f"BACEN Auto-Responder {col('restarted', C.GREEN)} (PID {responder_proc.pid})")

        time.sleep(0.5)


if __name__ == "__main__":
    main()
