# IBM MQ Setup Guide for BCSrvSqlMq
## FINVEST ISPB 36266751 - BACEN Integration

**Date Created:** 2026-03-05
**Queue Manager:** QM.36266751.01
**Service Name:** MQ_FinvestDTVM
**IBM MQ Version:** 9.4.5.0 Advanced for Developers

---

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Queue Configuration](#queue-configuration)
4. [Automated Setup Script](#automated-setup-script)
5. [Manual Verification](#manual-verification)
6. [Troubleshooting](#troubleshooting)
7. [Configuration Files](#configuration-files)

---

## Overview

This guide documents the IBM MQ setup for the BCSrvSqlMq Python application, which handles communication between FINVEST (ISPB 36266751) and BACEN (ISPB 00038166).

### Queue Architecture
- **Total Queues:** 8 (4 local + 4 remote)
- **Local Queues:** Receive messages FROM Bacen TO Finvest
- **Remote Queues:** Send messages FROM Finvest TO Bacen

### Queue Naming Convention
- Format: `QL/QR.TYPE.SOURCE_ISPB.DEST_ISPB.VERSION`
- Example: `QL.REQ.00038166.36266751.01` = Local Request queue from BACEN (00038166) to FINVEST (36266751)

---

## Prerequisites

### Software Requirements
- IBM MQ 9.4.5.0 Advanced for Developers (or equivalent)
- Installation Name: **FinvestDTVM**
- Installation Path: `C:\Program Files\IBM\MQ`

### Service Configuration
- **Service Name:** `MQ_FinvestDTVM`
- **Service Account:** Local System account (not a specific user account)
- **Important:** If service fails to start with Error 1069, change service to use "Local System account" via `services.msc`

### Installation Notes
1. Install IBM MQ with installation name **FinvestDTVM**
2. After installation, ensure service `MQ_FinvestDTVM` is set to use Local System account
3. Verify service starts successfully before running queue setup

---

## Queue Configuration

### Local Queues (4) - Messages FROM Bacen TO Finvest

| Queue Name | Description | Max Depth | Persistent |
|------------|-------------|-----------|------------|
| `QL.REQ.00038166.36266751.01` | Bacen Request to Finvest | 5000 | YES |
| `QL.RSP.00038166.36266751.01` | Bacen Response to Finvest | 5000 | YES |
| `QL.REP.00038166.36266751.01` | Bacen Report to Finvest | 5000 | YES |
| `QL.SUP.00038166.36266751.01` | Bacen Support to Finvest | 5000 | YES |

### Remote Queues (4) - Messages FROM Finvest TO Bacen

| Queue Name | Description | Remote QM | Remote Name | Xmit Queue |
|------------|-------------|-----------|-------------|------------|
| `QR.REQ.36266751.00038166.01` | Finvest Request to Bacen | QM.BACEN | QL.REQ.36266751.00038166.01 | QL.RSP.00038166.36266751.01 |
| `QR.RSP.36266751.00038166.01` | Finvest Response to Bacen | QM.BACEN | QL.RSP.36266751.00038166.01 | QL.RSP.00038166.36266751.01 |
| `QR.REP.36266751.00038166.01` | Finvest Report to Bacen | QM.BACEN | QL.REP.36266751.00038166.01 | QL.RSP.00038166.36266751.01 |
| `QR.SUP.36266751.00038166.01` | Finvest Support to Bacen | QM.BACEN | QL.SUP.36266751.00038166.01 | QL.RSP.00038166.36266751.01 |

---

## Automated Setup Script

### Script Location
`setup_mq_36266751.cmd` - Located in project root directory

### What the Script Does
1. Starts IBM MQ service (MQ_FinvestDTVM)
2. Checks for old queue manager (QM.61377677.01) and deletes if found
3. Creates new queue manager (QM.36266751.01)
4. Starts the queue manager
5. Creates all 8 queues (4 local + 4 remote)
6. Creates TCP listener (FINVEST.LISTENER on port 1414) and SVRCONN channel (FINVEST.SVRCONN) for pymqi client connectivity
7. Disables CHLAUTH and sets CHCKCLNT(OPTIONAL) for local development
8. Verifies queue creation, listener status, and channel

### How to Run
1. Open PowerShell or Command Prompt **as Administrator**
2. Navigate to project directory:
   ```powershell
   cd "C:\Users\AntonioBosco\OneDrive - Finvest\Documentos\GitHub\BCSrvSqlMq"
   ```
3. Run the setup script:
   ```cmd
   .\setup_mq_36266751.cmd
   ```
4. Follow the prompts and press any key to continue through each step

### Expected Output
```
========================================
IBM MQ Complete Setup for FINVEST (ISPB 36266751)
========================================

[1/6] Checking for old queue manager QM.61377677.01...
[4/6] Creating Queue Manager QM.36266751.01...
[5/6] Starting Queue Manager QM.36266751.01...
[6/6] Creating MQSC queue definitions and running script...

AMQ8006I: Foi criada a fila do IBM MQ. (x8 times)

Setup Complete!
Total: 8 queues
```

---

## Manual Verification

### Verify Queue Manager Status
```cmd
"C:\Program Files\IBM\MQ\bin\dspmq"
```

**Expected output:**
```
QMNAME(QM.36266751.01)                  STATUS(Running)
```

### Verify Individual Queues
```cmd
"C:\Program Files\IBM\MQ\bin\runmqsc.exe" QM.36266751.01
```

Then run these MQSC commands:
```mqsc
DISPLAY QLOCAL(QL.REQ.00038166.36266751.01)
DISPLAY QLOCAL(QL.RSP.00038166.36266751.01)
DISPLAY QLOCAL(QL.REP.00038166.36266751.01)
DISPLAY QLOCAL(QL.SUP.00038166.36266751.01)
DISPLAY QREMOTE(QR.REQ.36266751.00038166.01)
DISPLAY QREMOTE(QR.RSP.36266751.00038166.01)
DISPLAY QREMOTE(QR.REP.36266751.00038166.01)
DISPLAY QREMOTE(QR.SUP.36266751.00038166.01)
END
```

### Check Queue Depths
```mqsc
DISPLAY QLOCAL(*) CURDEPTH
```

All queues should show `CURDEPTH(0)` when empty.

---

## Troubleshooting

### Issue 1: Service Won't Start (Error 1069)
**Error:** "Não foi possível iniciar o serviço devido a uma falha de logon"

**Solution:**
1. Open `services.msc`
2. Find service `MQ_FinvestDTVM`
3. Right-click → Properties → Log On tab
4. Select "Local System account"
5. Click OK and restart service

### Issue 2: Queue Manager Already Exists (Error 8)
**Error:** "AMQ8110E: O gerenciador de fila do IBM MQ já existe"

**Solution:**
This is normal if running the script multiple times. The script will skip creation and use the existing queue manager. To start fresh:
```cmd
"C:\Program Files\IBM\MQ\bin\endmqm.exe" -i QM.36266751.01
"C:\Program Files\IBM\MQ\bin\dltmqm.exe" QM.36266751.01
```

### Issue 3: MQSC File Not Created
**Error:** "O sistema não pode encontrar o arquivo especificado"

**Cause:** File path issues or permission problems

**Solution:**
- Ensure running as Administrator
- Check that script is in a writable directory
- Verify no antivirus blocking file creation

### Issue 4: Wildcard Display Commands Fail
**Error:** "AMQ8424E: Detectado erro em uma palavra-chave de nome"

**Cause:** IBM MQ doesn't support wildcards in DISPLAY commands as used in the script

**Solution:**
This is a non-critical verification error. The queues are created successfully. Use individual DISPLAY commands (see Manual Verification section) to check queues.

---

## Configuration Files

### BCSrvSqlMq.ini

The application configuration file is already set up with the correct queue names:

```ini
[MQSeries]
; IBM MQ Configuration - FINVEST ISPB 36266751
MQServer=localhost
QueueManager=QM.36266751.01
QueueTimeout=30

; Local Queues - Messages FROM Bacen (ISPB 00038166) TO Finvest (ISPB 36266751)
QLBacenCidadeReq=QL.REQ.00038166.36266751.01
QLBacenCidadeRsp=QL.RSP.00038166.36266751.01
QLBacenCidadeRep=QL.REP.00038166.36266751.01
QLBacenCidadeSup=QL.SUP.00038166.36266751.01

; Remote Queues - Messages FROM Finvest (ISPB 36266751) TO Bacen (ISPB 00038166)
QRCidadeBacenReq=QR.REQ.36266751.00038166.01
QRCidadeBacenRsp=QR.RSP.36266751.00038166.01
QRCidadeBacenRep=QR.REP.36266751.00038166.01
QRCidadeBacenSup=QR.SUP.36266751.00038166.01
```

### MQSC Script Template

If you need to create queues manually, use this MQSC script:

```mqsc
* ====================================================================
* FINVEST ISPB: 36266751
* BACEN ISPB:   00038166
* ====================================================================

* Local Queues - Messages FROM Bacen TO Finvest (4)
DEFINE QLOCAL('QL.REQ.00038166.36266751.01') DESCR('Bacen Request to Finvest') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
DEFINE QLOCAL('QL.RSP.00038166.36266751.01') DESCR('Bacen Response to Finvest') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
DEFINE QLOCAL('QL.REP.00038166.36266751.01') DESCR('Bacen Report to Finvest') DEFPSIST(YES) MAXDEPTH(5000) REPLACE
DEFINE QLOCAL('QL.SUP.00038166.36266751.01') DESCR('Bacen Support to Finvest') DEFPSIST(YES) MAXDEPTH(5000) REPLACE

* Remote Queues - Messages FROM Finvest TO Bacen (4)
DEFINE QREMOTE('QR.REQ.36266751.00038166.01') DESCR('Finvest Request to Bacen') RNAME('QL.REQ.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE
DEFINE QREMOTE('QR.RSP.36266751.00038166.01') DESCR('Finvest Response to Bacen') RNAME('QL.RSP.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE
DEFINE QREMOTE('QR.REP.36266751.00038166.01') DESCR('Finvest Report to Bacen') RNAME('QL.REP.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE
DEFINE QREMOTE('QR.SUP.36266751.00038166.01') DESCR('Finvest Support to Bacen') RNAME('QL.SUP.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE

END
```

Save this as `queues.mqsc` and run:
```cmd
"C:\Program Files\IBM\MQ\bin\runmqsc.exe" QM.36266751.01 < queues.mqsc
```

---

## pymqi Client Connectivity

The Python application uses **pymqi** which links against `mqic.dll` (client mode). This requires a TCP listener and SVRCONN channel even when connecting to a local queue manager.

> **Note:** The original C++ application used server binding (`mqm.dll`) which connects directly without TCP. The pymqi pip package ships with a pre-compiled `pymqe.pyd` built against `mqic.dll`. Recompiling for server binding requires Visual Studio 2022, so we use TCP client mode.

### Connection Configuration
- **Channel:** `FINVEST.SVRCONN` (CHLTYPE: SVRCONN)
- **Listener:** `FINVEST.LISTENER` (TCP port 1414)
- **Connection string:** `localhost(1414)`
- **CHLAUTH:** Disabled (local development only)
- **CHCKCLNT:** OPTIONAL (no password required)

### Python Connection Code
```python
import pymqi

cd = pymqi.CD()
cd.ChannelName = b'FINVEST.SVRCONN'
cd.ConnectionName = b'localhost(1414)'
cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
cd.TransportType = pymqi.CMQC.MQXPT_TCP

qm = pymqi.QueueManager(None)
qm.connect_with_options('QM.36266751.01', cd)
```

### Integration Tests
Run the integration test suite to verify MQ connectivity:
```cmd
pytest python/tests/integration/test_mq_integration.py -v
```
Tests automatically skip if MQ is unavailable (e.g., on CI machines without MQ installed).

---

## Key Points for Another Machine

### Before Running Setup Script:
1. ✅ Install IBM MQ 9.4.5.0 with installation name **FinvestDTVM**
2. ✅ Configure service `MQ_FinvestDTVM` to use Local System account
3. ✅ Run Command Prompt or PowerShell **as Administrator**
4. ✅ Ensure no firewall/antivirus blocking MQ operations

### After Setup:
1. ✅ Verify all 8 queues created successfully
2. ✅ Update `BCSrvSqlMq.ini` if needed (should already be correct)
3. ✅ Test Python application connection to queue manager
4. ✅ Check queue depths to ensure messages flow correctly

### Quick Reference Commands:
```cmd
REM Check queue manager status
dspmq

REM Start queue manager
strmqm QM.36266751.01

REM Stop queue manager
endmqm -i QM.36266751.01

REM Delete queue manager (WARNING: Deletes all queues!)
dltmqm QM.36266751.01

REM Start IBM MQ service
net start "MQ_FinvestDTVM"

REM Stop IBM MQ service
net stop "MQ_FinvestDTVM"
```

---

## Success Criteria

Your IBM MQ setup is complete and working when:

1. ✅ Service `MQ_FinvestDTVM` is running
2. ✅ Queue Manager `QM.36266751.01` shows STATUS(Running)
3. ✅ All 8 queues exist and can be displayed
4. ✅ Local queues show `DEFPSIST(YES)` and `MAXDEPTH(5000)`
5. ✅ Remote queues point to `RQMNAME(QM.BACEN)`
6. ✅ All queue names match `BCSrvSqlMq.ini` configuration
7. ✅ Queue depths are 0 (CURDEPTH(0))
8. ✅ Listener `FINVEST.LISTENER` is running on port 1414
9. ✅ Channel `FINVEST.SVRCONN` exists and is accessible
10. ✅ Integration tests pass: `pytest python/tests/integration/test_mq_integration.py -v` (29 tests)

---

## Support and Documentation

### Official IBM MQ Documentation
- IBM MQ Knowledge Center: https://www.ibm.com/docs/en/ibm-mq

### Project Files
- Setup Script: `setup_mq_36266751.cmd`
- Configuration: `BCSrvSqlMq.ini`
- Python Application: `python/bcsrvsqlmq/`

### Common Error Codes
- **AMQ7048E:** Queue manager not found
- **AMQ8110E:** Queue manager already exists
- **AMQ8006I:** Queue created successfully (SUCCESS)
- **AMQ8424E:** Error in name keyword (wildcard issue in DISPLAY)
- **Error 1069:** Service logon failure (use Local System account)
- **Error 72:** Invalid queue manager name

---

**Document Version:** 1.0
**Last Updated:** 2026-03-05
**Author:** Claude (Anthropic) + Antonio Bosco
**Project:** BCSrvSqlMq - FINVEST BACEN Integration
