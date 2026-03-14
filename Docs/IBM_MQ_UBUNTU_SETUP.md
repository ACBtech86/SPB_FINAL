# IBM MQ Installation & Setup Guide — Ubuntu 22.04 / 24.04

**Project:** BCSrvSqlMq — FINVEST BACEN Integration (ISPB 36266751)
**IBM MQ Version:** 9.4.x Advanced for Developers
**Date:** 2026-03-14

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1 — Download IBM MQ](#step-1--download-ibm-mq)
4. [Step 2 — Install IBM MQ Packages](#step-2--install-ibm-mq-packages)
5. [Step 3 — Configure Environment](#step-3--configure-environment)
6. [Step 4 — Create Queue Manager](#step-4--create-queue-manager)
7. [Step 5 — Create Queues and Channels](#step-5--create-queues-and-channels)
8. [Step 6 — Install pymqi](#step-6--install-pymqi)
9. [Step 7 — systemd Service (Optional)](#step-7--systemd-service-optional)
10. [Verification](#verification)
11. [Troubleshooting](#troubleshooting)

---

## Overview

This guide installs IBM MQ on Ubuntu and configures the queue manager and queues required for the BCSrvSqlMq Python application.

### Queue Architecture Summary

| Direction | Queue Name | Type |
|-----------|-----------|------|
| BACEN → Finvest | `QL.REQ.00038166.36266751.01` | Local |
| BACEN → Finvest | `QL.RSP.00038166.36266751.01` | Local |
| BACEN → Finvest | `QL.REP.00038166.36266751.01` | Local |
| BACEN → Finvest | `QL.SUP.00038166.36266751.01` | Local |
| Finvest → BACEN | `QR.REQ.36266751.00038166.01` | Remote |
| Finvest → BACEN | `QR.RSP.36266751.00038166.01` | Remote |
| Finvest → BACEN | `QR.REP.36266751.00038166.01` | Remote |
| Finvest → BACEN | `QR.SUP.36266751.00038166.01` | Remote |

**Connection:** pymqi uses TCP client mode via `localhost(1414)` and channel `FINVEST.SVRCONN`.

---

## Prerequisites

```bash
# Update package index
sudo apt update

# Install dependencies
sudo apt install -y tar gzip curl wget bc

# Verify architecture (must be x86_64)
uname -m
```

Expected: `x86_64`

---

## Step 1 — Download IBM MQ

IBM MQ Advanced for Developers is **free** for non-production use.

### Option A: Download from IBM Developer (recommended)

1. Go to: https://developer.ibm.com/articles/mq-downloads/
2. Sign in with a free IBM ID
3. Download **IBM MQ 9.4 for Linux x86_64** — the file will be named:
   ```
   IBM_MQ_9.4.x_LINUX_X86-64.tar.gz
   ```

### Option B: Download via IBM Fix Central

```bash
# After downloading, copy to the server:
scp IBM_MQ_9.4.x_LINUX_X86-64.tar.gz ubuntu@<server-ip>:/home/ubuntu/
```

### Verify the Download

```bash
ls -lh ~/IBM_MQ_9.4*.tar.gz
# Should show ~1-2 GB file
```

---

## Step 2 — Install IBM MQ Packages

```bash
# Extract the archive
cd ~
tar -xzf IBM_MQ_9.4*.tar.gz
cd MQServer

# Accept the license
sudo ./mqlicense.sh -accept

# Install packages in dependency order (runtime must be first)
sudo dpkg -i ibmmq-runtime_*.deb
sudo dpkg -i ibmmq-gskit_*.deb
sudo dpkg -i ibmmq-client_*.deb
sudo dpkg -i ibmmq-server_*.deb
sudo dpkg -i ibmmq-sdk_*.deb
sudo dpkg -i ibmmq-java_*.deb
sudo dpkg -i ibmmq-jre_*.deb
```

**Expected output:** Each package should end with `Setting up ibmmq-<name>...`

> **WARNING during ibmmq-server install:** You may see:
> ```
> WARNING: System settings for this system do not meet recommendations for this product
> See the log file at "/tmp/mqconfig.XXXX.log" for more information
> ```
> This is **not a fatal error** — the installation succeeds. The only typical `FAIL` is the soft
> open-file limit (`nofile -Sn = 1024`, IBM requires ≥10240). Fix it immediately after install:
>
> ```bash
> sudo bash -c 'echo "mqm soft nofile 10240
> mqm hard nofile 65536" >> /etc/security/limits.conf'
> ```
>
> This takes effect on the next login of the `mqm` user (or after rebooting). You can verify with:
> ```bash
> sudo -u mqm bash -c 'ulimit -Sn'
> # Expected: 10240
> ```

### Verify Installation

```bash
ls /opt/mqm/bin/crtmqm
# Should print: /opt/mqm/bin/crtmqm
```

IBM MQ installs to `/opt/mqm/` by default. An `mqm` system user and group are created automatically.

---

## Step 3 — Configure Environment

### Set Default Installation

```bash
sudo /opt/mqm/bin/setmqinst -i -p /opt/mqm
```

### Add Environment to Your Shell

```bash
# Add to ~/.bashrc (or ~/.profile for system-wide)
echo 'source /opt/mqm/bin/setmqenv -s 2>/dev/null' >> ~/.bashrc
source ~/.bashrc
```

### Add Your User to the mqm Group

```bash
sudo usermod -aG mqm $USER

# Log out and back in, then verify:
groups | grep mqm
```

> **Important:** You must log out and back in (or run `newgrp mqm`) for group membership to take effect.

### Verify MQ Commands are Available

```bash
dspmq
# Expected: no output (normal — no queue managers created yet)
# After Step 4 this will show: QMNAME(QM.36266751.01)   STATUS(Running)
```

---

## Step 4 — Create Queue Manager

## Automated Setup (Steps 4 + 5 combined)

Run the provided setup script — it handles queue manager creation, all queues, the listener, and the SVRCONN channel in one step:

```bash
cd /home/ubuntu/SPBFinal/SPB_FINAL
chmod +x setup_mq_ubuntu.sh

# If you just added your user to mqm and haven't logged out yet, use sg:
sg mqm -c "./setup_mq_ubuntu.sh"

# Otherwise (after re-login):
./setup_mq_ubuntu.sh
```

The script will ask before deleting any existing queue manager. Skip to [Step 6](#step-6--install-pymqi) after it completes successfully.

---

### Manual Steps (if not using the script)

```bash
# Create the queue manager
crtmqm QM.36266751.01

# Start it
strmqm QM.36266751.01

# Verify it is running
dspmq
```

**Expected output:**
```
QMNAME(QM.36266751.01)                  STATUS(Running)
```

---

## Step 5 — Create Queues and Channels

### Create the MQSC Script

```bash
cat > /tmp/setup_finvest.mqsc << 'MQSC'
* ====================================================================
* FINVEST ISPB: 36266751  |  BACEN ISPB: 00038166
* Queue Manager: QM.36266751.01
* ====================================================================

* --- Local Queues: Messages FROM Bacen TO Finvest ---
DEFINE QLOCAL('QL.REQ.00038166.36266751.01') DESCR('Bacen Request to Finvest')   DEFPSIST(YES) MAXDEPTH(5000) REPLACE
DEFINE QLOCAL('QL.RSP.00038166.36266751.01') DESCR('Bacen Response to Finvest')  DEFPSIST(YES) MAXDEPTH(5000) REPLACE
DEFINE QLOCAL('QL.REP.00038166.36266751.01') DESCR('Bacen Report to Finvest')    DEFPSIST(YES) MAXDEPTH(5000) REPLACE
DEFINE QLOCAL('QL.SUP.00038166.36266751.01') DESCR('Bacen Support to Finvest')   DEFPSIST(YES) MAXDEPTH(5000) REPLACE

* --- Remote Queues: Messages FROM Finvest TO Bacen ---
DEFINE QREMOTE('QR.REQ.36266751.00038166.01') DESCR('Finvest Request to Bacen')  RNAME('QL.REQ.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE
DEFINE QREMOTE('QR.RSP.36266751.00038166.01') DESCR('Finvest Response to Bacen') RNAME('QL.RSP.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE
DEFINE QREMOTE('QR.REP.36266751.00038166.01') DESCR('Finvest Report to Bacen')   RNAME('QL.REP.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE
DEFINE QREMOTE('QR.SUP.36266751.00038166.01') DESCR('Finvest Support to Bacen')  RNAME('QL.SUP.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE

* --- Dead Letter Queue ---
DEFINE QLOCAL('SYSTEM.DEAD.LETTER.QUEUE') REPLACE

* --- TCP Listener on port 1414 ---
DEFINE LISTENER('FINVEST.LISTENER') TRPTYPE(TCP) PORT(1414) CONTROL(QMGR) REPLACE
START LISTENER('FINVEST.LISTENER')

* --- Server Connection Channel for pymqi ---
DEFINE CHANNEL('FINVEST.SVRCONN') CHLTYPE(SVRCONN) TRPTYPE(TCP) REPLACE

* --- Disable auth for local development ---
ALTER QMGR CHLAUTH(DISABLED)
ALTER QMGR CONNAUTH('')
REFRESH SECURITY TYPE(CONNAUTH)

END
MQSC
```

### Run the MQSC Script

```bash
runmqsc QM.36266751.01 < /tmp/setup_finvest.mqsc
```

**Expected:** Each `DEFINE` line should print `AMQ8006I: IBM MQ queue created.`

---

## Step 6 — Install pymqi

pymqi is a Python client for IBM MQ. It requires the IBM MQ client libraries already installed (done in Step 2).

### Fix requirements.txt for Linux

The project's `requirements.txt` includes `pywin32` which is Windows-only. On Ubuntu, install without it:

```bash
cd /home/ubuntu/SPBFinal/SPB_FINAL
source venv/bin/activate   # or your virtualenv

# Install all deps except pywin32
pip install pymqi psycopg2-binary cryptography lxml
```

Or create a Linux-specific requirements file:

```bash
grep -v pywin32 BCSrvSqlMq/python/requirements.txt | pip install -r /dev/stdin
```

### Verify pymqi

```python
python3 -c "
import pymqi
cd = pymqi.CD()
cd.ChannelName = b'FINVEST.SVRCONN'
cd.ConnectionName = b'localhost(1414)'
cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
cd.TransportType = pymqi.CMQC.MQXPT_TCP
qm = pymqi.QueueManager(None)
qm.connect_with_options('QM.36266751.01', cd)
print('pymqi connection: OK')
qm.disconnect()
"
```

---

## Step 7 — systemd Service (Optional)

To start the queue manager automatically on boot:

```bash
sudo tee /etc/systemd/system/ibmmq-finvest.service > /dev/null << 'EOF'
[Unit]
Description=IBM MQ Queue Manager QM.36266751.01
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=mqm
Group=mqm
Environment="AMQ_MQ_INSTALLATION_PATH=/opt/mqm"
ExecStart=/opt/mqm/bin/strmqm QM.36266751.01
ExecStop=/opt/mqm/bin/endmqm -w QM.36266751.01
SuccessExitStatus=0 5
TimeoutStartSec=120
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ibmmq-finvest
sudo systemctl start ibmmq-finvest
sudo systemctl status ibmmq-finvest
```

---

## Verification

### 1. Check Queue Manager Status

```bash
dspmq
# Expected: QMNAME(QM.36266751.01)   STATUS(Running)
```

### 2. Check All Queues Exist

```bash
echo "DISPLAY QLOCAL(*) CURDEPTH" | runmqsc QM.36266751.01
echo "DISPLAY QREMOTE(*)" | runmqsc QM.36266751.01
```

### 3. Check Listener is Running

```bash
echo "DISPLAY LSSTATUS(*) STATUS" | runmqsc QM.36266751.01
# Expected: STATUS(RUNNING)
```

```bash
# Confirm port 1414 is listening
ss -tlnp | grep 1414
```

### 4. Run Integration Tests

```bash
cd /home/ubuntu/SPBFinal/SPB_FINAL
source venv/bin/activate
pytest BCSrvSqlMq/python/tests/integration/test_mq_integration.py -v
```

---

## Troubleshooting

### Problem: `dspmq: command not found`

The MQ environment is not loaded.

```bash
source /opt/mqm/bin/setmqenv -s
# or add to ~/.bashrc as shown in Step 3
```

### Problem: `AMQ7077E: You are not authorized to perform the requested operation`

Your user is not in the `mqm` group.

```bash
sudo usermod -aG mqm $USER
newgrp mqm   # apply without logging out
```

### Problem: Queue manager won't start — `AMQ7048E`

Queue manager doesn't exist yet. Run `crtmqm QM.36266751.01` first.

### Problem: `AMQ8110E: IBM MQ queue manager already exists`

Normal if running setup again. To reset completely:

```bash
endmqm -i QM.36266751.01   # force stop
dltmqm QM.36266751.01      # delete all data (irreversible)
crtmqm QM.36266751.01      # recreate
strmqm QM.36266751.01
runmqsc QM.36266751.01 < /tmp/setup_finvest.mqsc
```

### Problem: `pymqi.MQMIError: MQI Error. Comp: 2, Reason 2059`

MQRC_Q_MGR_NOT_AVAILABLE. The queue manager is not running or the listener isn't up.

```bash
dspmq                           # check QM status
echo "DISPLAY LSSTATUS(*)" | runmqsc QM.36266751.01   # check listener
strmqm QM.36266751.01          # start if not running
```

### Problem: `pymqi.MQMIError: Reason 2035` (MQRC_NOT_AUTHORIZED)

CHLAUTH rules are blocking the connection.

```bash
# Run inside runmqsc:
echo "ALTER QMGR CHLAUTH(DISABLED)" | runmqsc QM.36266751.01
echo "REFRESH SECURITY TYPE(CONNAUTH)" | runmqsc QM.36266751.01
```

### Problem: pip install pymqi fails

pymqi needs the MQ client libraries at compile time. Ensure `ibmmq-sdk` is installed and the environment is set:

```bash
sudo dpkg -i ~/MQServer/ibmmq-sdk_*.deb
source /opt/mqm/bin/setmqenv -s
pip install pymqi
```

### Problem: `ImportError: libmqic_r.so: cannot open shared object file`

The MQ client library path is not in `LD_LIBRARY_PATH`.

```bash
export LD_LIBRARY_PATH=/opt/mqm/lib64:$LD_LIBRARY_PATH
# Add to ~/.bashrc to persist
```

---

## Quick Reference Commands

```bash
# Queue manager
crtmqm QM.36266751.01          # create
strmqm QM.36266751.01          # start
endmqm -w QM.36266751.01       # graceful stop
endmqm -i QM.36266751.01       # immediate stop
dspmq                          # list status

# Interactive MQSC console
runmqsc QM.36266751.01

# Common MQSC commands (run inside runmqsc):
# DISPLAY QLOCAL(*)  CURDEPTH
# DISPLAY QREMOTE(*)
# DISPLAY LSSTATUS(*)  STATUS
# CLEAR QLOCAL('QL.REQ.00038166.36266751.01')
# END

# Listener
echo "START LISTENER('FINVEST.LISTENER')" | runmqsc QM.36266751.01
echo "STOP  LISTENER('FINVEST.LISTENER')" | runmqsc QM.36266751.01
```

---

## Key Differences vs Windows Setup

| Aspect | Windows | Ubuntu |
|--------|---------|--------|
| Install path | `C:\Program Files\IBM\MQ` | `/opt/mqm` |
| Service management | `services.msc` / `net start` | `systemctl` |
| MQ binary path | Added to PATH by installer | Requires `setmqenv` or `source` |
| pymqi mode | TCP client (`mqic.dll`) | TCP client (`libmqic_r.so`) |
| `pywin32` dependency | Required | **Not installed** — skip it |
| Setup script | `setup_mq_36266751.cmd` | MQSC file + `runmqsc` |
| User/group | Local System account | `mqm` user and group |

---

**Document Version:** 1.0
**Last Updated:** 2026-03-14
**Applies to:** Ubuntu 22.04 LTS and Ubuntu 24.04 LTS
**Related:** [IBM_MQ_SETUP_GUIDE.md](IBM_MQ_SETUP_GUIDE.md) (Windows), [UBUNTU_DEPLOYMENT_GUIDE.md](UBUNTU_DEPLOYMENT_GUIDE.md)
