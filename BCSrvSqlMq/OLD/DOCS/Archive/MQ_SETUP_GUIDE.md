# 🔧 IBM MQ Queue Setup Guide

## Overview

This guide walks you through setting up the IBM MQ queues required for BCSrvSqlMq service to process messages.

---

## ✅ Prerequisites

- [x] IBM MQ installed ✅ (Found: IBM MQ FinvestDTVM)
- [x] Queue Manager created ✅ (QM.61377677.01)
- [x] BCSrvSqlMq service installed ✅

---

## 📋 Required Queues

### Local Queues (4)
These queues are local to this Queue Manager:

1. `QL.61377677.01.ENTRADA.BACEN` - BACEN incoming messages
2. `QL.61377677.01.SAIDA.BACEN` - BACEN outgoing messages
3. `QL.61377677.01.ENTRADA.IF` - IF incoming messages
4. `QL.61377677.01.SAIDA.IF` - IF outgoing messages

### Remote Queues (4)
These queues point to external systems:

1. `QR.61377677.01.ENTRADA.BACEN` → Remote BACEN system
2. `QR.61377677.01.SAIDA.BACEN` → Remote BACEN system
3. `QR.61377677.01.ENTRADA.IF` → Remote IF system
4. `QR.61377677.01.SAIDA.IF` → Remote IF system

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Check Current Queues

Open **Command Prompt** (as Administrator):

```cmd
cd "C:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq"
Scripts\check_mq_queues.bat
```

**What to look for:**
- If queues exist: You'll see queue details
- If queues don't exist: "AMQ8147: WebSphere MQ queue not found"

---

### Step 2: Create Queues

If queues don't exist, run:

```cmd
Scripts\setup_mq_queues.bat
```

**What it does:**
- Creates all 8 queues (4 local + 4 remote)
- Configures queue properties (persistent, max depth 50,000 msgs)
- Displays queue information
- Saves MQSC script for reference

**Expected output:**
```
[SUCCESS] Queues created successfully!

Local Queues (4):
  - QL.61377677.01.ENTRADA.BACEN
  - QL.61377677.01.SAIDA.BACEN
  - QL.61377677.01.ENTRADA.IF
  - QL.61377677.01.SAIDA.IF

Remote Queues (4):
  - QR.61377677.01.ENTRADA.BACEN
  - QR.61377677.01.SAIDA.BACEN
  - QR.61377677.01.ENTRADA.IF
  - QR.61377677.01.SAIDA.IF
```

---

### Step 3: Restart BCSrvSqlMq Service

After creating queues, restart the service:

```cmd
sc stop BCSrvSqlMq
timeout /t 3
sc start BCSrvSqlMq
```

Or use the quick restart script (if available):
```cmd
Scripts\INICIAR-RAPIDO.bat
```

---

## 🔍 Verification

### Check Service Logs

After restarting, check the service log:

```cmd
Scripts\VER-LOG.bat
```

**What to look for:**

**BEFORE queue setup:**
```
[MsgID:8019] p1=2085  - MQRC_UNKNOWN_OBJECT_NAME
[MsgID:8019] p1=2092  - MQRC_UNKNOWN_OBJECT_TYPE
```

**AFTER queue setup (SUCCESS):**
```
[INFO] Task RmtReq - Connected to queue
[INFO] Task RmtRsp - Connected to queue
[INFO] Task RmtRep - Connected to queue
[INFO] Task RmtSup - Connected to queue
[INFO] Task LocReq - Connected to queue
[INFO] Task LocRsp - Connected to queue
[INFO] Task LocRep - Connected to queue
[INFO] Task LocSup - Connected to queue
```

MQ errors (2085, 2092) should **disappear**! ✅

---

## 🧪 Test Message Flow

### Send Test Message

Once queues are working, you can test the full crypto flow:

1. **Put a test message** on `QL.61377677.01.ENTRADA.IF`
2. **Service will:**
   - Receive the message
   - Load certificates (ReadPublicKey, ReadPrivatKey)
   - Sign the message (funcAssinar) ← **OpenSSL!**
   - Encrypt sensitive data (funcCript) ← **OpenSSL!**
   - Store in PostgreSQL database
3. **Check logs** for crypto operations

### Manual Test Using IBM MQ Explorer

If you have IBM MQ Explorer installed:

1. Open **IBM MQ Explorer**
2. Navigate to: `QM.61377677.01` → `Queues`
3. Right-click `QL.61377677.01.ENTRADA.IF` → **Put Test Message**
4. Enter test content: `{"test": "OpenSSL x64 migration"}`
5. Click **Put message**
6. Check service logs for processing

---

## 📊 Queue Properties

### Local Queues Configuration

```
Type:         QLOCAL (Local Queue)
Persistence:  YES (messages survive restart)
Max Depth:    50,000 messages
Usage:        NORMAL
```

### Remote Queues Configuration

```
Type:         QREMOTE (Remote Queue)
Remote Name:  QL.BACEN.* or QL.IF.*
Remote QMgr:  QM.BACEN or QM.IF
Transmission: SYSTEM.DEFAULT.XMITQ
```

**Note:** Remote queue configuration may need adjustment based on your actual remote systems.

---

## 🔧 Troubleshooting

### Error: "runmqsc not found"

**Solution:** Add IBM MQ bin to PATH:
```cmd
set PATH=%PATH%;C:\Program Files\IBM\MQ\bin
```

Or run from IBM MQ installation directory.

---

### Error: "AMQ8146: Queue manager not available"

**Solution:** Start the queue manager:
```cmd
strmqm QM.61377677.01
```

Check service:
```cmd
sc query MQ_FinvestDTVM
```

---

### Error: "AMQ8077: Entity has insufficient authority"

**Solution:** Run as Administrator or adjust permissions:
```cmd
setmqaut -m QM.61377677.01 -t qmgr -p %USERNAME% +allmqi
```

---

### Queues Created But Service Still Shows Errors

**Check:**
1. Queue names match exactly (case-sensitive)
2. Service has been restarted
3. Queue manager is running
4. No typos in BCSrvSqlMq.ini

**View current configuration:**
```cmd
type BCSrvSqlMq.ini | findstr Queue
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `Scripts/check_mq_queues.bat` | Check if queues exist |
| `Scripts/setup_mq_queues.bat` | Create all 8 queues |
| `temp_create_queues.mqsc` | MQSC script (generated) |
| `MQ_SETUP_GUIDE.md` | This guide |

---

## 🎯 Expected End Result

After successful setup:

✅ **8 queues created** (4 local + 4 remote)
✅ **Service connected** to all queues
✅ **MQ errors gone** (no more 2085/2092)
✅ **Ready for messages** - crypto functions will trigger
✅ **OpenSSL functional** - sign/encrypt will work on real messages

---

## 📝 Next Steps After MQ Setup

Once MQ queues are working:

1. **Test database connectivity** (`Scripts\setup_database.bat`)
2. **Send test message** through MQ
3. **Verify crypto operations** in logs:
   - Look for "ReadPublicKey" / "ReadPrivatKey"
   - Look for "funcAssinar" / "funcCript"
4. **Check database** for encrypted records
5. **Verify signature** and decryption work

---

**Date:** 2026-03-01
**Queue Manager:** QM.61377677.01
**Service:** BCSrvSqlMq (x64 with OpenSSL 3.6.1)
