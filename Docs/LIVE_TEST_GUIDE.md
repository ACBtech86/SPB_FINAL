# SPB Live Test Guide

Step-by-step guide for running end-to-end live tests on the SPB system deployed on Ubuntu.

---

## Prerequisites

Before running the live test, ensure all services are up:

| Service | Check Command | Expected |
|---------|---------------|----------|
| PostgreSQL | `sudo systemctl status postgresql` | active (running) |
| IBM MQ | `sudo systemctl status ibmmq-finvest` | active (exited) |
| BCSrvSqlMq | `pgrep -f bcsrvsqlmq` | PID returned |
| SPBSite | `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/login` | 200 |

### Starting Services (if not running)

```bash
cd /home/ubuntu/SPBFinal/SPB_FINAL
source venv/bin/activate

# PostgreSQL (auto-starts on boot)
sudo systemctl start postgresql

# IBM MQ (auto-starts on boot)
sudo systemctl start ibmmq-finvest

# BCSrvSqlMq
cd BCSrvSqlMq/python
nohup python -m bcsrvsqlmq -d > /dev/null 2>&1 &
cd ../..

# SPBSite
cd spbsite
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
cd ..
```

---

## Option 1: Visual Flow Monitor (Recommended)

The `monitor_live.py` script provides an event-driven, single-terminal view of the complete message flow. It only prints when something changes.

### Running the Monitor

SSH into the server and run:

```bash
cd /home/ubuntu/SPBFinal/SPB_FINAL
source venv/bin/activate

# Monitor only — submit messages from browser
python monitor_live.py

# Monitor + inject a test GEN0001 message automatically
python monitor_live.py --inject

# Monitor without auto-responder (manual testing)
python monitor_live.py --no-responder
```

### What You See

```
╔══════════════════════════════════════════════════════════════════╗
║           SPB LIVE FLOW MONITOR                                 ║
╚══════════════════════════════════════════════════════════════════╝

MESSAGE FLOW:

 SPBSite  ━━▶  PostgreSQL  ━━▶  BCSrvSqlMq  ━━▶  MQ Queues  ━━▶  BACEN
 :8000         BanuxSPB       8 threads        port 1414       simulator
                                                       ◀━━━━━━━━━━━━  response

SERVICES:  ● PostgreSQL   ● IBM MQ   ● BCSrvSqlMq   ● SPBSite

─────────────────────────────────────────────────────────────────
      TIME  EVENT
─────────────────────────────────────────────────────────────────
13:26:38  ▶  BACEN Auto-Responder started (PID 122401)
13:26:38  ◉  Monitoring started. Waiting for events...
```

### Flow Steps (when a message is submitted)

| Step | Icon | Event | Description |
|------|------|-------|-------------|
| ① | 📥 | `DB INSERT` | Message inserted into `spb_local_to_bacen` with `flag_proc='P'` |
| ② | 📤 | `BCSrvSqlMq PROCESSED` | Worker thread picks up message, signs, encrypts, sends to MQ. Flag changes `P→E` |
| ③ | ▲/▼ | `MQ PUT/GET` | Queue depth changes — message enters/leaves MQ queues |
| ③ | 🔵 | `MQ PUT BACEN RSP` | BACEN auto-responder placed response on RSP queue |
| ③ | ✓ | `MQ GET BACEN RSP` | BCSrvSqlMq picked up the response from RSP queue |
| ④ | 📩 | `RESPONSE` | BACEN response stored in `spb_bacen_to_local` |
| ✓ | ✓ | `FLOW COMPLETE` | Full roundtrip confirmed — outbound sent, inbound received |
| 📋 | 📋 | `Audit log` | New entries added to `spb_log_bacen` |

### Example Output — Complete Flow

```
13:27:16  ①  DB INSERT      GEN0001  nu_ope=36266751202603150000010  flag=P
13:27:16  ②  BCSrvSqlMq     PROCESSED  flag=P→E  → signed, encrypted, sent to MQ
13:27:16  ③  MQ PUT         ENTRADA.IF  depth ↑ 0→1  → message waiting in queue
13:27:16  📋  Audit log:    +2 new entries (total: 2)
13:27:17  ③  MQ PUT         BACEN RSP  depth ↑ 0→1  → BACEN response queued
13:27:17  ③  MQ GET         BACEN RSP  depth ↓ 1→0  → BCSrvSqlMq picked up response
13:27:17  ④  RESPONSE       GEN0001R1  → BACEN response stored in DB
13:27:17  ✓  FLOW COMPLETE  outbound=1 sent, inbound=1 received
13:27:17  ③  MQ GET         ENTRADA.IF  depth ↓ 1→0  → message consumed from queue
```

---

## Option 2: Submitting Messages from the Browser

1. Open browser at `http://<server-ip>:8000`
2. Login with `admin` / `admin`
3. Navigate to **Messages → Combined** (`/messages/combined`)
4. Select a message type from the dropdown (e.g., `GEN0001`)
5. Fill the form fields
6. Click **Submit**
7. Watch the monitor terminal for the flow events

### Verifying in SPBSite

After submitting:

| Page | URL | What to check |
|------|-----|---------------|
| Outbound messages | `/monitoring/messages/outbound/bacen` | Your message with `flag=E` (sent) |
| Inbound messages | `/monitoring/messages/inbound/bacen` | BACEN response (e.g., GEN0001R1) |
| XML Viewer | Click on any message row | Full XML payload |

---

## Option 3: Automated E2E Test

Run the automated test that checks all 15 integration points:

```bash
cd /home/ubuntu/SPBFinal/SPB_FINAL
source venv/bin/activate
python test_scripts/e2e_full_system_test.py
```

### What It Tests

| # | Check | Component |
|---|-------|-----------|
| 1 | PostgreSQL connection | Database |
| 2 | IBM MQ connection | Message Queue |
| 3 | BCSrvSqlMq process running | Service |
| 4 | SPBSite HTTP response | Web Interface |
| 5 | SPBSite login/session | Authentication |
| 6 | Insert outbound message | Database |
| 7 | BCSrvSqlMq processes message (flag P→E) | Service |
| 8-9 | MQ queue depths | Message Queue |
| 10 | BACEN auto-responder generates response | Simulator |
| 11-12 | SPBSite monitoring pages accessible | Web Interface |
| 13-14 | Outbound/inbound records in DB | Database |
| 15 | Audit log entries created | Database |

### Expected Output

```
15 passed, 0 failed out of 15 checks
```

---

## Option 4: tmux 4-Pane Monitor

For advanced users who want to see raw logs, MQ depths, DB rows, and auto-responder output simultaneously:

```bash
cd /home/ubuntu/SPBFinal/SPB_FINAL
./live_test.sh
```

### Layout

```
┌──────────────────────┬──────────────────────┐
│  BCSrvSqlMq Logs     │  MQ Queue Depths     │
├──────────────────────┼──────────────────────┤
│  BACEN Auto-Responder│  DB Message Watcher  │
└──────────────────────┴──────────────────────┘
```

### tmux Controls

| Keys | Action |
|------|--------|
| `Ctrl+B` then arrow keys | Switch between panes |
| `Ctrl+B` then `z` | Zoom/unzoom current pane |
| `Ctrl+B` then `d` | Detach (session keeps running) |
| `tmux attach -t spb-live` | Reattach to session |
| `tmux kill-session -t spb-live` | Stop everything |

**Important:** Press `ENTER` in the bottom-left pane to start the BACEN auto-responder.

---

## Cleaning Up Before Testing

To start fresh, clear all message tables and MQ queues:

```bash
# 1. Stop BCSrvSqlMq (to release queue locks)
kill $(pgrep -f bcsrvsqlmq)
sleep 2

# 2. Clean database tables
sudo -u postgres psql -d BanuxSPB -c "
  DELETE FROM spb_local_to_bacen;
  DELETE FROM spb_bacen_to_local;
  DELETE FROM spb_log_bacen;
"

# 3. Clear MQ queues
sg mqm -c '/opt/mqm/bin/runmqsc QM.36266751.01 <<EOF
CLEAR QLOCAL(QL.REQ.00038166.36266751.01)
CLEAR QLOCAL(QL.RSP.00038166.36266751.01)
CLEAR QLOCAL(QL.REP.00038166.36266751.01)
CLEAR QLOCAL(QL.SUP.00038166.36266751.01)
CLEAR QLOCAL(QL.36266751.01.ENTRADA.IF)
CLEAR QLOCAL(QL.36266751.01.SAIDA.IF)
CLEAR QLOCAL(QL.36266751.01.REPORT.IF)
CLEAR QLOCAL(QL.36266751.01.SUPORTE.IF)
EOF'

# 4. Restart BCSrvSqlMq
source venv/bin/activate
cd BCSrvSqlMq/python
nohup python -m bcsrvsqlmq -d > /dev/null 2>&1 &
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `flag_proc` stays `P` | BCSrvSqlMq not running or crashed | Restart: `cd BCSrvSqlMq/python && nohup python -m bcsrvsqlmq -d &` |
| MQ ENTRADA.IF depth grows but never drops | Auto-responder not running | Start: `python monitor_live.py` (auto-starts responder) |
| RSP queue depth grows but never drops | BCSrvSqlMq inbound thread stuck | Check trace log: `tail -f BCSrvSqlMq/Traces/TRACE_SPB__$(date +%Y%m%d).log` |
| Inbound response has `cod_msg=None` | XML parsing issue in auto-responder | Check auto-responder output for errors |
| SPBSite returns 500 | Database connection lost after restart | Restart uvicorn: `pkill -f uvicorn && cd spbsite && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &` |
| `MQRC_UNKNOWN_OBJECT_NAME` | IF staging queues not created | Run: `bash setup_mq_ubuntu.sh` |
| Monitor shows `● BCSrvSqlMq` as red | Process not running | Check log: `cat BCSrvSqlMq/Traces/TRACE_SPB__$(date +%Y%m%d).log` |

---

## Message Types for Testing

| Message | Description | Complexity |
|---------|-------------|------------|
| GEN0001 | Echo/Ping request | Simple — 2 fields |
| GEN0002 | Log request | Simple — 2 fields |
| GEN0003 | Last message (UltMsg) | Simple — 2 fields |
| PAG0104 | Payment order | Complex — many fields |

Start with `GEN0001` for basic testing, then try more complex messages.

---

## Architecture Reference

```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌───────────┐     ┌───────────┐
│ SPBSite  │────▶│PostgreSQL│────▶│ BCSrvSqlMq │────▶│  IBM MQ   │────▶│  BACEN    │
│ :8000    │     │ BanuxSPB │     │ 8 threads  │     │ :1414     │     │ Simulator │
│          │     │          │     │            │     │           │     │           │
│ FastAPI  │     │ outbound │     │ sign       │     │ ENTRADA.IF│     │ auto-     │
│ browser  │     │ inbound  │     │ encrypt    │     │ SAIDA.IF  │     │ responder │
│ forms    │     │ audit    │     │ route      │     │ REQ/RSP   │     │           │
└─────────┘     └──────────┘     └────────────┘     └───────────┘     └───────────┘
                      ▲                                    │
                      └────────────────────────────────────┘
                              inbound response flow
```

### Key Files

| File | Purpose |
|------|---------|
| `monitor_live.py` | Event-driven visual flow monitor |
| `live_test.sh` | tmux 4-pane raw monitor |
| `test_scripts/e2e_full_system_test.py` | Automated 15-check E2E test |
| `BCSrvSqlMq/bacen_auto_responder.py` | Simulated BACEN responses |
| `BCSrvSqlMq/BCSrvSqlMq.ini` | Service configuration |
| `setup_mq_ubuntu.sh` | MQ queue/channel setup |
