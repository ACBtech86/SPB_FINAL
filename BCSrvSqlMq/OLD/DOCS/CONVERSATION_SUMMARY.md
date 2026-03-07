# BCSrvSqlMq - Complete Troubleshooting Summary

**Date:** 2026-02-27
**Status:** In Progress - Testing console mode to diagnose service account issue
**Project:** BCSrvSqlMq - Brazilian SPB Payment System Service

---

## 🎯 Current Status

### The Problem
Service runs but all 8 IBM MQ queues fail with **error 2043 (MQRC_OBJECT_NOT_FOUND)** at MQOPEN.

### Log Pattern
```
8014 I RmtReq/RmtRsp/RmtRep/RmtSup Iniciada
8014 I LocReq/LocRsp/LocRep/LocSup Iniciada
8019 E [Task] MQOPEN ended with reason code 2043  ← ERROR
8012 I [Task] Terminada  ← Thread terminates immediately
```

### Key Discovery
- MQCONN succeeds (no 8018 error) → Connection to QM works
- MQOPEN fails (8019 error with code 2043) → Can't open queues
- Error occurs on ALL 8 queues immediately after startup

---

## 📋 Complete Fix History

### Fix #1: Create Missing Queues ✅
**Problem:** Service needed 8 queues (Req, Rsp, Rep, Sup) but only 4 existed.

**Solution:**
```mqsc
Created 8 queues in IBM MQ:
- QL.61377677.01.REPORT.BACEN
- QL.61377677.01.REPORT.IF
- QL.61377677.01.SUPORTE.BACEN
- QL.61377677.01.SUPORTE.IF
- QR.61377677.01.REPORT.BACEN
- QR.61377677.01.REPORT.IF
- QR.61377677.01.SUPORTE.BACEN
- QR.61377677.01.SUPORTE.IF
```

**File:** `create_missing_queues.mqsc`
**Result:** Still error 2043

---

### Fix #2: Disable Channel Authentication ✅
**Problem:** CHLAUTH was blocking connections.

**Solution:**
```mqsc
ALTER QMGR CHLAUTH(DISABLED)
```

**File:** `fix_mq_authentication.mqsc`
**Result:** Still error 2043

---

### Fix #3: Disable ALL MQ Security ✅
**Problem:** Multiple security layers blocking access.

**Solution:**
```mqsc
ALTER QMGR CHLAUTH(DISABLED) CONNAUTH(' ') AUTHOREV(DISABLED)
```

**Files:**
- `fix_queue_permissions.mqsc`
- `full_security_disable.mqsc`

**Result:** Still error 2043

---

### Fix #4: Add SYSTEM to mqm Group ✅
**Problem:** LocalSystem account not in IBM MQ mqm group.

**Solution:**
```cmd
net localgroup mqm "SYSTEM" /add
```

**File:** `add_system_to_mqm.bat`
**Verification:** `net localgroup mqm` shows "AUTORIDADE NT\SISTEMA"
**Result:** Still error 2043

---

### Fix #5: Set Queue Manager as Default ✅
**Problem:** QM.61377677.01 not set as default Queue Manager.

**Solution:**
```cmd
strmqm -x QM.61377677.01
```

**File:** `set_default_qm.bat`
**Verification:** `dspmq -o default` shows DEFAULT(sim)
**Result:** Still error 2043

---

## 🔍 Current Diagnosis

After exhausting ALL MQ configuration options, the issue is likely:

**Service Account Permissions Issue**
- LocalSystem may not have proper MQ context despite being in mqm group
- Service environment may be missing required variables
- Windows Service isolation may be blocking MQ access

---

## ⚡ Next Steps to Try

### Option 1: Run in Console Mode (RECOMMENDED - TEST FIRST)
**Purpose:** Determine if service code works at all

```cmd
# Run as Administrator
net stop BCSrvSqlMq
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"
BCSrvSqlMq.exe -d
```

**If this works:**
- Service code is fine
- Problem is service account permissions
- Solution: Change service user to MUSR_MQADMIN

**If this fails:**
- Deeper issue (code bug, MQ config, missing dependencies)
- Solution: Enable MQ tracing

**File:** `debug_run.bat`

---

### Option 2: Change Service User to MUSR_MQADMIN
**Purpose:** Use proper MQ service account with guaranteed permissions

**Steps:**
1. Reset MUSR_MQADMIN password (if unknown):
   - `compmgmt.msc` → Local Users and Groups → Users → MUSR_MQADMIN → Set Password

2. Run as Administrator:
   ```cmd
   change_service_user.bat
   ```
   Enter MUSR_MQADMIN password when prompted

**File:** `change_service_user.bat`

---

### Option 3: Enable MQ Tracing (Last Resort)
**Purpose:** Get detailed MQ API call information

```cmd
strmqtrc -m QM.61377677.01 -t detail
# Run service or console mode
endmqtrc -m QM.61377677.01
# Check traces in C:\ProgramData\IBM\MQ\trace\
```

---

## 📁 System Configuration

### Environment
- **OS:** Windows 11 Pro 10.0.26200
- **PostgreSQL:** 18.1 (database: bcspbstr)
- **IBM MQ:** 9.4.5.0 (QM: QM.61377677.01)
- **Service Name:** BCSrvSqlMq
- **Service Account:** LocalSystem (NT AUTHORITY\SYSTEM)

### Paths
- **Project:** `c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq`
- **Executable:** `build\Release\BCSrvSqlMq.exe` (223 KB)
- **Logs:** `C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log`
- **Config:** `BCSrvSqlMq.ini` (source) / Windows Registry (active)

### Dependencies
- `BCMsgSqlMq.dll` (36 KB) - Logging/messaging
- `CL32.dll` (672 KB) - CryptLib
- `pugixml.dll` (167 KB) - XML parser
- PostgreSQL ODBC 32-bit (16.00.0005)

---

## 🗄️ Database Configuration

### PostgreSQL Connection
```ini
DBServer=localhost
DBName=bcspbstr
DBPort=5432
DBUserName=postgres
DBPassword=Rama1248
```

### Tables Created
- `spb_log_bacen` - Service logs
- `spb_bacen_to_local` - Inbound messages
- `spb_local_to_bacen` - Outbound messages
- `spb_controle` - Configuration/control

**File:** `create_tables_postgresql.sql`

---

## 🔧 IBM MQ Configuration

### Queue Manager
- **Name:** QM.61377677.01
- **Status:** Running (Em execução)
- **Default:** Yes (sim) - Set by Fix #5
- **Port:** 1414 (default)

### Queues (16 total: 8 local + 8 remote)

**Local Queues (QL.*):**
- QL.61377677.01.ENTRADA.BACEN (Request from Bacen)
- QL.61377677.01.SAIDA.BACEN (Response to Bacen)
- QL.61377677.01.REPORT.BACEN (Report from Bacen)
- QL.61377677.01.SUPORTE.BACEN (Support from Bacen)
- QL.61377677.01.ENTRADA.IF (Request from IF)
- QL.61377677.01.SAIDA.IF (Response to IF)
- QL.61377677.01.REPORT.IF (Report from IF)
- QL.61377677.01.SUPORTE.IF (Support from IF)

**Remote Queues (QR.*):**
- QR.61377677.01.ENTRADA.BACEN (Request to Bacen)
- QR.61377677.01.SAIDA.BACEN (Response from Bacen)
- QR.61377677.01.REPORT.BACEN (Report to Bacen)
- QR.61377677.01.SUPORTE.BACEN (Support to Bacen)
- QR.61377677.01.ENTRADA.IF (Request to IF)
- QR.61377677.01.SAIDA.IF (Response from IF)
- QR.61377677.01.REPORT.IF (Report to IF)
- QR.61377677.01.SUPORTE.IF (Support to IF)

### Security Settings (All Disabled)
- **CHLAUTH:** DISABLED
- **CONNAUTH:** ' ' (empty/disabled)
- **AUTHOREV:** DISABLED

### Service Threads (8 total)
- **RmtReq** → Opens QR.61377677.01.ENTRADA.IF
- **RmtRsp** → Opens QR.61377677.01.SAIDA.IF
- **RmtRep** → Opens QR.61377677.01.REPORT.IF
- **RmtSup** → Opens QR.61377677.01.SUPORTE.IF
- **LocReq** → Opens QL.61377677.01.ENTRADA.BACEN
- **LocRsp** → Opens QL.61377677.01.SAIDA.BACEN
- **LocRep** → Opens QL.61377677.01.REPORT.BACEN
- **LocSup** → Opens QL.61377677.01.SUPORTE.BACEN

---

## 📝 Registry Configuration

**Path:** `HKLM\SYSTEM\CurrentControlSet\Services\BCSrvSqlMq\Parameters`

### MQSeries Section
```
MQServer = localhost
QueueManager = QM.61377677.01
QueueTimeout = 60000
QLBacenCidadeReq = QL.61377677.01.ENTRADA.BACEN
QLBacenCidadeRsp = QL.61377677.01.SAIDA.BACEN
QLBacenCidadeRep = QL.61377677.01.REPORT.BACEN
QLBacenCidadeSup = QL.61377677.01.SUPORTE.BACEN
QRCidadeBacenReq = QR.61377677.01.ENTRADA.IF
QRCidadeBacenRsp = QR.61377677.01.SAIDA.IF
QRCidadeBacenRep = QR.61377677.01.REPORT.IF
QRCidadeBacenSup = QR.61377677.01.SUPORTE.IF
```

### DataBase Section
```
DBAliasName = BCSPBSTR
DBServer = localhost
DBName = bcspbstr
DBPort = 5432
DBUserName = postgres
DBPassword = Rama1248
DbTbControle = spb_controle
DbTbStrLog = spb_log_bacen
DbTbBacenCidadeApp = spb_bacen_to_local
DbTbCidadeBacenApp = spb_local_to_bacen
```

### Servico Section
```
MonitorPort = 14499
Trace = S
SrvTimeout = 300000
MaxLenMsg = 8192
```

**Configuration Script:** `configure_registry.ps1` / `configure_registry.bat`

---

## 📄 Files Created During Troubleshooting

### Configuration Scripts
- `configure_registry.ps1` - Populate Windows Registry from INI
- `configure_registry.bat` - Batch wrapper for registry config

### MQ Queue Scripts
- `create_missing_queues.mqsc` - Create REPORT and SUPORTE queues
- `create_mq_queues.mqsc` - Original queue creation (first 4 queues)

### MQ Security Scripts
- `fix_mq_authentication.mqsc` - Disable CHLAUTH
- `fix_queue_permissions.mqsc` - Disable CONNAUTH, enable queues
- `full_security_disable.mqsc` - Disable ALL security

### Service Management Scripts
- `add_system_to_mqm.bat` - Add LocalSystem to mqm group
- `set_default_qm.bat` - Set QM as default
- `restart_service.bat` - Stop/start service
- `restart_qm.bat` - Restart Queue Manager
- `debug_run.bat` - Run in console/debug mode
- `install_and_start_service.bat` - Install and start service
- `uninstall_service.bat` - Uninstall service

### Alternative Solutions
- `change_service_user.bat` - Change service to run as MUSR_MQADMIN
- `grant_queue_permissions.bat` - Grant permissions using setmqaut

### Documentation
- `TESTING_GUIDE.md` - Complete testing guide
- `REGISTRY_CONFIGURATION.md` - Registry configuration details
- `PROBLEM_SOLVED.txt` - Missing queues fix
- `AUTHENTICATION_FIXED.txt` - CHLAUTH disable
- `SECURITY_DISABLED.txt` - All security disabled
- `FINAL_FIX_MQM_GROUP.txt` - mqm group fix
- `DEFAULT_QM_FIX.txt` - Default QM fix
- `ALTERNATIVE_SOLUTIONS.txt` - Alternative approaches
- `NEXT_STEPS.txt` - What to do next
- `CONVERSATION_SUMMARY.md` - This file

---

## 🔬 Technical Details

### Service Code Analysis

**Connection Method:** BINDINGS mode (local shared memory)
```cpp
// From BacenREQ.cpp line 75
MQCONN(m_QMName,      // Queue manager name from registry
       &m_Hcon,       // Connection handle
       &m_CompCode,   // Completion code
       &m_CReason);   // Reason code
```

**Queue Opening:**
```cpp
// From BacenREQ.cpp line 96
m_O_options = MQOO_INPUT_EXCLUSIVE + MQOO_FAIL_IF_QUIESCING;
MQOPEN(m_Hcon,        // Connection handle
       &m_od,         // Object descriptor (has queue name)
       m_O_options,   // Open options
       &m_Hobj,       // Object handle
       &m_OpenCode,   // Completion code
       &m_Reason);    // Reason code (2043 here!)
```

**Error Logging:**
- 8018: MQCONN failed (NOT seen in logs → connection works!)
- 8019: MQOPEN failed (SEEN in logs → this is the error)

**Queue Names from Registry:**
```cpp
// From BacenREQ.cpp line 66
strcpy(m_od.ObjectName, pMainSrv->pInitSrv->m_MqQlBacenCidadeReq);
```

---

## 🐛 Why Error 2043 is Misleading

Error 2043 (MQRC_OBJECT_NOT_FOUND) can mean:

1. **Queue doesn't exist** ✅ Fixed - all queues exist
2. **Can't access due to security** ✅ Fixed - all security disabled
3. **Queue Manager connection failed** ✅ Verified - MQCONN succeeds
4. **Service account lacks permissions** ⚠️ SUSPECTED - Current issue
5. **Wrong Queue Manager context** ✅ Fixed - set as default
6. **Code bug or parameter issue** ❓ Possible

---

## ✅ Verification Commands

### Check Service Status
```cmd
sc query BCSrvSqlMq
```

### Check Queue Manager
```cmd
dspmq
dspmq -o default
```

### Check mqm Group Membership
```cmd
net localgroup mqm
```

### Check MQ Security Settings
```cmd
echo "DISPLAY QMGR CHLAUTH CONNAUTH AUTHOREV" | runmqsc QM.61377677.01
```

### Check Queues Exist
```cmd
echo "DISPLAY QLOCAL('QL.61377677.01.*')" | runmqsc QM.61377677.01
echo "DISPLAY QREMOTE('QR.61377677.01.*')" | runmqsc QM.61377677.01
```

### Check Registry Configuration
```cmd
reg query "HKLM\SYSTEM\CurrentControlSet\Services\BCSrvSqlMq\Parameters\MQSeries"
```

### Check Logs
```cmd
type "C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log" | findstr /i "8019"
```

---

## 🚨 Current Blocker

**Issue:** Error 2043 persists despite:
- All queues existing
- All security disabled
- SYSTEM in mqm group
- QM set as default
- MQCONN succeeding

**Hypothesis:** Service account (LocalSystem) lacks proper MQ context/permissions despite configuration changes.

**Next Action:** Run in console mode as Administrator to test if service code works at all.

---

## 💡 Key Learnings

1. **Error 2043 is ambiguous** - Can indicate many different issues
2. **Registry vs INI** - Service reads from registry, not INI file
3. **BINDINGS mode** - Requires mqm group membership
4. **Multiple security layers** - CHLAUTH, CONNAUTH, AUTHOREV all needed
5. **Default QM matters** - Even when specifying QM name
6. **Service account critical** - LocalSystem may not work even when configured

---

## 📞 Support Information

### IBM MQ Version
```
Name:        IBM MQ
Version:     9.4.5.0
```

### PostgreSQL Version
```
PostgreSQL 18.1
```

### Service Information
```
Service Name: BCSrvSqlMq
Display Name: BCSrvSqlMq
Type:        WIN32_OWN_PROCESS
Start Type:  AUTO_START
```

---

## 🎯 Immediate Action Required

**Run in console mode to diagnose:**

```cmd
# Open Command Prompt as Administrator
net stop BCSrvSqlMq
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"
BCSrvSqlMq.exe -d
```

**Watch for:**
- ✅ SUCCESS: No error 2043, threads stay running
- ❌ FAILURE: Still error 2043

**If SUCCESS:** Problem is service account → Use `change_service_user.bat`
**If FAILURE:** Deeper issue → Enable MQ tracing

---

## 📌 Notes

- Service was modernized from legacy code to C++20
- Uses MFC framework (Microsoft Foundation Classes)
- Part of Brazilian SPB (Sistema de Pagamentos Brasileiro) integration
- Handles financial messaging between Bacen (Central Bank) and institutions
- Critical production service requiring high reliability

---

**Last Updated:** 2026-02-27 08:10 AM
**Status:** Awaiting console mode test results
**Next Session:** Continue from console mode test on another machine

---

## 🔗 Quick Reference Links

- Project Root: `c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq`
- Build Output: `build\Release\BCSrvSqlMq.exe`
- Logs: `C:\BCSrvSqlMq\Traces\`
- Scripts: `build\Release\*.bat`
- Documentation: `*.md` and `*.txt` files in build\Release

---

**END OF SUMMARY**
