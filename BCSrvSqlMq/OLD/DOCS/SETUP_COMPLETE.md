# BCSrvSqlMq - Setup Complete! ✅

**Date:** 2026-02-26
**Status:** Ready to Test

---

## 🎉 Setup Summary

Congratulations! Your BCSrvSqlMq environment is **95% complete**!

---

## ✅ What's Working

| Component | Status | Details |
|-----------|--------|---------|
| **PostgreSQL 18.1** | ✅ Running | Service active |
| **Database `bcspbstr`** | ✅ Created | With 4 tables |
| **Tables & Indexes** | ✅ Created | All schemas ready |
| **Initial Data** | ✅ Loaded | Control table configured |
| **PostgreSQL Password** | ✅ Set | `Rama1248` |
| **psqlODBC 32-bit** | ✅ Installed | Version 16.00.0005 |
| **BCSrvSqlMq.exe** | ✅ Built | 223 KB (PE32 x86) |
| **CL32.dll** | ✅ Deployed | 672 KB |
| **pugixml.dll** | ✅ Deployed | 167 KB |
| **BCSrvSqlMq.ini** | ✅ Configured | All parameters set |
| **Working Directories** | ✅ Created | Traces, AuditFiles |

---

## ⚠️ One Minor Issue

### IBM MQ Queue Manager

The Queue Manager `QM.61377677.01` needs to be started:

**To start it:**
1. Right-click [`start_mq.bat`](start_mq.bat)
2. Select **"Run as administrator"**
3. Done!

Or manually:
```cmd
strmqm QM.61377677.01
dspmq
```

---

## 📊 Database Schema

### Tables Created

#### 1. **spb_log_bacen** - Service Activity Log
```sql
Columns: log_id, log_timestamp, log_level, log_source,
         log_message, log_details, session_id, user_id
Indexes: timestamp, level, session
```

#### 2. **spb_bacen_to_local** - Inbound Messages
```sql
Columns: msg_id, msg_timestamp, msg_type, msg_content,
         msg_status, msg_priority, msg_queue, msg_correlation_id,
         processed_at, error_message, retry_count
Indexes: timestamp, status, correlation_id, type
```

#### 3. **spb_local_to_bacen** - Outbound Messages
```sql
Columns: msg_id, msg_timestamp, msg_type, msg_content,
         msg_status, msg_priority, msg_queue, msg_correlation_id,
         sent_at, confirmed_at, error_message, retry_count
Indexes: timestamp, status, correlation_id, type
```

#### 4. **spb_controle** - Configuration
```sql
Columns: control_id, control_key, control_value, control_type,
         description, is_active
Initial data: SERVICE_VERSION, MAX_RETRY_COUNT,
              RETRY_DELAY_MS, SERVICE_ENABLED
```

---

## 🚀 Running BCSrvSqlMq

### Method 1: Test Run (Console Mode)

```cmd
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"

REM Copy config file if not there
copy ..\..\BCSrvSqlMq.ini .

REM Run
BCSrvSqlMq.exe
```

**What to expect:**
- Console window opens
- Service initializes
- Connects to PostgreSQL
- Connects to IBM MQ
- Starts processing threads
- Logs appear in `C:\BCSrvSqlMq\Traces\`

**To stop:** Press `Ctrl+C`

---

### Method 2: Install as Windows Service

```cmd
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"

REM Install service (as Administrator)
BCSrvSqlMq.exe -install

REM Start service
net start BCSrvSqlMq

REM Check status
sc query BCSrvSqlMq

REM View logs
type C:\BCSrvSqlMq\Traces\*.log

REM Stop service
net stop BCSrvSqlMq

REM Uninstall service (if needed)
BCSrvSqlMq.exe -uninstall
```

---

## 📁 Important Paths

### Executable and DLLs
```
c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release\
├── BCSrvSqlMq.exe  (223 KB)
├── CL32.dll        (672 KB)
├── pugixml.dll     (167 KB)
└── BCSrvSqlMq.ini  (copy from project root)
```

### Configuration
```
c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\
└── BCSrvSqlMq.ini
```

### Logs
```
C:\BCSrvSqlMq\
├── Traces\         (Service logs)
└── AuditFiles\     (Audit trail)
```

### Database
```
PostgreSQL Server: localhost:5432
Database: bcspbstr
Username: postgres
Password: Rama1248
```

### IBM MQ
```
Queue Manager: QM.61377677.01
Server: localhost
Queues:
  - QL.61377677.01.ENTRADA.BACEN
  - QL.61377677.01.SAIDA.BACEN
  - QL.61377677.01.ENTRADA.IF
  - QL.61377677.01.SAIDA.IF
  + 4 remote queues (QR.*)
```

---

## 🧪 Testing Checklist

Before production deployment:

### Pre-Flight Checks
- [ ] Start IBM MQ Queue Manager (`start_mq.bat`)
- [ ] Verify PostgreSQL is running (`Get-Service postgresql-x64-18`)
- [ ] Verify database connection (`test_connection.ps1`)
- [ ] Copy BCSrvSqlMq.ini to build\Release directory

### Test Run
- [ ] Run BCSrvSqlMq.exe in console mode
- [ ] Check console output for errors
- [ ] Verify log files are created in C:\BCSrvSqlMq\Traces
- [ ] Check database connection in logs
- [ ] Check MQ connection in logs
- [ ] Verify all 8 task threads start successfully

### Functional Tests
- [ ] Test inbound message processing (Bacen → Local)
- [ ] Test outbound message processing (Local → Bacen)
- [ ] Verify database inserts
- [ ] Check audit file creation
- [ ] Test error handling and retry logic

### Service Installation
- [ ] Install as Windows Service
- [ ] Start service
- [ ] Check Windows Event Viewer for errors
- [ ] Verify service auto-starts after reboot

---

## 📝 Configuration Summary

### BCSrvSqlMq.ini Key Settings

```ini
[Servico]
ServiceName=BCSrvSqlMq
MonitorPort=14499          ; Health check port
Trace=D                    ; Debug level logging

[DataBase]
DBServer=localhost
DBPort=5432
DBName=bcspbstr
DBUserName=postgres
DBPassword=Rama1248        ; ✅ Configured

[MQSeries]
QueueManager=QM.61377677.01  ; ✅ Configured
MQServer=localhost

[Security]
SecurityEnable=N           ; Crypto disabled for now
```

---

## 🔧 Troubleshooting

### Issue: "Cannot connect to database"

**Check:**
```powershell
Get-Service postgresql-x64-18
Test-NetConnection -ComputerName localhost -Port 5432
```

**Test connection:**
```cmd
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d bcspbstr
```

---

### Issue: "Cannot connect to Queue Manager"

**Check:**
```cmd
dspmq
```

**Should show:**
```
QMNAME(QM.61377677.01)  STATUS(Running)
```

**If not running:**
```cmd
strmqm QM.61377677.01
```

---

### Issue: "DLL not found"

**Ensure these files are in build\Release:**
- BCSrvSqlMq.exe
- CL32.dll
- pugixml.dll
- BCSrvSqlMq.ini

---

### Issue: "Access denied to directories"

**Grant permissions:**
```powershell
# Run as Administrator
$acl = Get-Acl "C:\BCSrvSqlMq"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "NETWORK SERVICE", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
)
$acl.SetAccessRule($rule)
Set-Acl "C:\BCSrvSqlMq" $acl
```

---

## 📞 Support Scripts

Helper scripts in project directory:

| Script | Purpose |
|--------|---------|
| `verify_complete_setup.ps1` | Check all components |
| `start_mq.bat` | Start IBM MQ Queue Manager |
| `test_connection.ps1` | Test database ODBC connection |
| `setup_database.bat` | Create database and tables |
| `reset_password_easy.bat` | Reset PostgreSQL password |

---

## ⏭️ Next Steps

### 1. Start IBM MQ (if not running)
```cmd
REM Right-click and run as Administrator
start_mq.bat
```

### 2. Copy config to executable directory
```cmd
copy BCSrvSqlMq.ini build\Release\
```

### 3. Test run BCSrvSqlMq
```cmd
cd build\Release
BCSrvSqlMq.exe
```

### 4. Monitor logs
```cmd
type C:\BCSrvSqlMq\Traces\*.log
```

### 5. Install as service (when ready)
```cmd
cd build\Release
BCSrvSqlMq.exe -install
net start BCSrvSqlMq
```

---

## 🎯 Success Criteria

✅ BCSrvSqlMq.exe runs without crashing
✅ Database connection established
✅ IBM MQ connection established
✅ All 8 threads start successfully:
   - RmtReq (TASKS_BACENREQ)
   - RmtRsp (TASKS_BACENRSP)
   - RmtRep (TASKS_BACENREP)
   - RmtSup (TASKS_BACENSUP)
   - LocReq (TASKS_IFREQ)
   - LocRsp (TASKS_IFRSP)
   - LocRep (TASKS_IFREP)
   - LocSup (TASKS_IFSUP)
✅ Monitor thread starts (TCP port 14499)
✅ Logs written to C:\BCSrvSqlMq\Traces
✅ Audit files written to C:\BCSrvSqlMq\AuditFiles

---

## 🏆 Congratulations!

You've successfully:
- ✅ Built BCSrvSqlMq.exe from legacy VS6 code to modern C++20
- ✅ Installed and configured PostgreSQL 18.1
- ✅ Migrated database schema to PostgreSQL
- ✅ Set up IBM MQ 9.4.5.0 with 8 queues
- ✅ Configured ODBC connectivity
- ✅ Prepared for service deployment

**You're ready to run BCSrvSqlMq!** 🚀

---

**Setup completed:** 2026-02-26
**Ready for:** Testing and deployment
