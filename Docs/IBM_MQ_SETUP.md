# IBM MQ Setup Guide for SPB System

Complete guide to install and configure IBM MQ for the SPB messaging system.

---

## Prerequisites

- Windows 10/11 Pro or Enterprise
- Administrator access
- At least 2GB free disk space
- Port 1414 available (default MQ listener port)

---

## Step 1: Download IBM MQ

### Option A: IBM MQ Developer Edition (Free)

1. Visit: https://www.ibm.com/products/mq/advanced
2. Click "Try IBM MQ"
3. Select "IBM MQ Advanced for Developers (Windows)"
4. Download the latest version (e.g., 9.3.x)
5. File will be named something like: `9.3.0.x-IBM-MQ-Advanced-for-Developers-Non-Install-Windows-x86-64.zip`

### Option B: IBM MQ Trial (90 days)

1. Visit: https://www.ibm.com/account/reg/us-en/signup?formid=urx-30282
2. Register and download IBM MQ Advanced

---

## Step 2: Install IBM MQ

### Installation Steps:

1. **Extract the downloaded ZIP** to `C:\IBM\MQ` (or preferred location)

2. **Run installer as Administrator:**
   ```cmd
   cd C:\IBM\MQ
   setup.exe
   ```

3. **Installation Wizard:**
   - Accept license agreement
   - Choose "Typical" installation
   - Installation directory: `C:\Program Files\IBM\MQ`
   - Select features:
     - ✅ Server
     - ✅ MQ Explorer (optional, useful for GUI management)
     - ✅ Development Toolkit
   - Click "Install"

4. **Verify Installation:**
   ```cmd
   dspmqver
   ```
   Should show IBM MQ version information.

---

## Step 3: Create Queue Manager

Open **Command Prompt as Administrator**:

```cmd
# Create queue manager QM.36266751.01
crtmqm QM.36266751.01

# Start the queue manager
strmqm QM.36266751.01

# Verify it's running
dspmq
```

Expected output:
```
QMNAME(QM.36266751.01)                                        STATUS(Running)
```

---

## Step 4: Configure Queue Manager

Run `runmqsc` to configure the queue manager:

```cmd
runmqsc QM.36266751.01
```

In the MQSC console, enter these commands:

```mqsc
* Define server connection channel
DEFINE CHANNEL(FINVEST.SVRCONN) CHLTYPE(SVRCONN)

* Define listener on port 1414
DEFINE LISTENER(FINVEST.LISTENER) TRPTYPE(TCP) PORT(1414) CONTROL(QMGR)
START LISTENER(FINVEST.LISTENER)

* Set channel authentication to allow connections
ALTER QMGR CHLAUTH(DISABLED)

* Set connection authentication (for development - less secure)
ALTER QMGR CONNAUTH(' ')
REFRESH SECURITY TYPE(CONNAUTH)

* Exit MQSC
END
```

---

## Step 5: Create SPB Queues

### Create all required queues from BCSrvSqlMq.ini:

```cmd
runmqsc QM.36266751.01
```

```mqsc
* BACEN Local Queues (receive from BACEN)
DEFINE QLOCAL(QL.REQ.00038166.36266751.01) MAXDEPTH(100000)
DEFINE QLOCAL(QL.RSP.00038166.36266751.01) MAXDEPTH(100000)
DEFINE QLOCAL(QL.REP.00038166.36266751.01) MAXDEPTH(100000)
DEFINE QLOCAL(QL.SUP.00038166.36266751.01) MAXDEPTH(100000)

* BACEN Remote Queues (send to BACEN)
DEFINE QREMOTE(QR.REQ.36266751.00038166.01) RNAME(QL.REQ.36266751.00038166.01) RQMNAME(QM.BACEN) XMITQ(BACEN.XMITQ)
DEFINE QREMOTE(QR.RSP.36266751.00038166.01) RNAME(QL.RSP.36266751.00038166.01) RQMNAME(QM.BACEN) XMITQ(BACEN.XMITQ)
DEFINE QREMOTE(QR.REP.36266751.00038166.01) RNAME(QL.REP.36266751.00038166.01) RQMNAME(QM.BACEN) XMITQ(BACEN.XMITQ)
DEFINE QREMOTE(QR.SUP.36266751.00038166.01) RNAME(QL.SUP.36266751.00038166.01) RQMNAME(QM.BACEN) XMITQ(BACEN.XMITQ)

* IF (Interfaceamento) Local Queues
DEFINE QLOCAL(QL.36266751.01.ENTRADA.IF) MAXDEPTH(100000)
DEFINE QLOCAL(QL.36266751.01.SAIDA.IF) MAXDEPTH(100000)
DEFINE QLOCAL(QL.36266751.01.REPORT.IF) MAXDEPTH(100000)
DEFINE QLOCAL(QL.36266751.01.SUPORTE.IF) MAXDEPTH(100000)

* IF Remote Queues
DEFINE QREMOTE(QR.36266751.01.ENTRADA.IF) RNAME(QL.36266751.01.ENTRADA.IF) RQMNAME(QM.36266751.01)
DEFINE QREMOTE(QR.36266751.01.SAIDA.IF) RNAME(QL.36266751.01.SAIDA.IF) RQMNAME(QM.36266751.01)
DEFINE QREMOTE(QR.36266751.01.REPORT.IF) RNAME(QL.36266751.01.REPORT.IF) RQMNAME(QM.36266751.01)
DEFINE QREMOTE(QR.36266751.01.SUPORTE.IF) RNAME(QL.36266751.01.SUPORTE.IF) RQMNAME(QM.36266751.01)

* Transmission Queue for BACEN (for testing without real BACEN connection)
DEFINE QLOCAL(BACEN.XMITQ) USAGE(XMITQ) MAXDEPTH(100000)

* Dead Letter Queue
DEFINE QLOCAL(DEAD.LETTER.QUEUE) MAXDEPTH(100000)
ALTER QMGR DEADQ(DEAD.LETTER.QUEUE)

* Exit MQSC
END
```

---

## Step 6: Verify Queue Creation

```cmd
runmqsc QM.36266751.01
```

```mqsc
* Display all queues
DISPLAY QLOCAL(*)
DISPLAY QREMOTE(*)

* Display specific queue
DISPLAY QLOCAL(QR.REQ.36266751.00038166.01)

END
```

Or use MQ Explorer (if installed) to visually inspect queues.

---

## Step 7: Test MQ Connection

### Test with Python:

Create test file `test_mq.py`:

```python
import pymqi

qmgr_name = 'QM.36266751.01'
channel = 'FINVEST.SVRCONN'
conn_info = 'localhost(1414)'
queue_name = 'QL.36266751.01.ENTRADA.IF'

try:
    # Connect to queue manager
    qmgr = pymqi.connect(qmgr_name, channel, conn_info)
    print(f'[OK] Connected to {qmgr_name}')

    # Open queue
    queue = pymqi.Queue(qmgr, queue_name)
    print(f'[OK] Opened queue {queue_name}')

    # Put test message
    test_msg = b'TEST MESSAGE FROM PYTHON'
    queue.put(test_msg)
    print(f'[OK] Message sent to queue')

    # Get message back
    msg = queue.get()
    print(f'[OK] Message received: {msg.decode()}')

    # Close
    queue.close()
    qmgr.disconnect()
    print('[OK] Test completed successfully!')

except pymqi.MQMIError as e:
    print(f'[ERROR] MQ Error: {e}')
except Exception as e:
    print(f'[ERROR] {e}')
```

Run test:
```cmd
cd C:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\Novo_SPB\BCSrvSqlMq\python
venv312\Scripts\activate
python test_mq.py
```

---

## Step 8: Configure for Testing (Simulate BACEN)

Since we don't have a real BACEN queue manager, configure for local testing:

### Update BCSrvSqlMq.ini:

The current configuration should work for local testing:
```ini
[MQSeries]
mqserver = localhost
queuemanager = QM.36266751.01
queuetimeout = 30
```

### Create local queues to simulate BACEN responses:

```cmd
runmqsc QM.36266751.01
```

```mqsc
* Create local queues to simulate BACEN endpoints
DEFINE QLOCAL(QL.REQ.36266751.00038166.01) MAXDEPTH(100000)
DEFINE QLOCAL(QL.RSP.36266751.00038166.01) MAXDEPTH(100000)
DEFINE QLOCAL(QL.REP.36266751.00038166.01) MAXDEPTH(100000)
DEFINE QLOCAL(QL.SUP.36266751.00038166.01) MAXDEPTH(100000)

END
```

---

## Step 9: Restart BCSrvSqlMq

In **Terminal 2** (x64 Native Tools Command Prompt):

```cmd
# Stop if running (Ctrl+C)

# Restart BCSrvSqlMq
cd C:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\Novo_SPB\BCSrvSqlMq\python
venv312\Scripts\activate
python -m bcsrvsqlmq -d
```

Watch for successful connection messages in the trace log!

---

## Troubleshooting

### Queue Manager Won't Start

```cmd
# Check status
dspmq

# Check errors
dspmq -m QM.36266751.01 -x

# View error logs
type "C:\ProgramData\IBM\MQ\qmgrs\QM!36266751!01\errors\AMQERR01.LOG"
```

### Connection Refused (2538)

- Verify listener is running:
  ```cmd
  runmqsc QM.36266751.01
  DISPLAY LSSTATUS(*)
  END
  ```

- Check firewall (allow port 1414)
- Verify channel exists:
  ```cmd
  runmqsc QM.36266751.01
  DISPLAY CHANNEL(FINVEST.SVRCONN)
  END
  ```

### Permission Denied (2035)

- Disable channel authentication (for testing):
  ```cmd
  runmqsc QM.36266751.01
  ALTER QMGR CHLAUTH(DISABLED)
  REFRESH SECURITY
  END
  ```

---

## Quick Reference Commands

```cmd
# Start queue manager
strmqm QM.36266751.01

# Stop queue manager
endmqm QM.36266751.01

# Display queue manager status
dspmq

# Run MQSC commands
runmqsc QM.36266751.01

# Display queue depth
echo "DISPLAY QLOCAL(*) CURDEPTH" | runmqsc QM.36266751.01

# Clear queue
runmqsc QM.36266751.01
CLEAR QLOCAL(queue_name)
END
```

---

## Summary

After completing these steps:
- ✅ IBM MQ installed
- ✅ Queue Manager `QM.36266751.01` created and running
- ✅ All SPB queues created
- ✅ Channel `FINVEST.SVRCONN` configured
- ✅ Ready for BCSrvSqlMq to connect

**Next:** Restart BCSrvSqlMq and verify it connects successfully!
