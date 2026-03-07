# BCSrvSqlMq - Testing Guide

**Date:** 2026-02-26
**Status:** Ready for Testing

---

## 🎯 Current Status

✅ **All components configured and ready**
- PostgreSQL database created with tables
- IBM MQ Queue Manager configured
- BCSrvSqlMq.exe built successfully
- All DLLs and config files in place

⏳ **Next step:** Test run to verify everything connects properly

---

## 🚀 How to Test BCSrvSqlMq

### **Option 1: Debug Console Mode** ⭐ **RECOMMENDED FOR FIRST TEST**

This runs the service in the foreground with console output - perfect for testing and debugging.

#### Steps:

1. **Navigate to** `build\Release` directory:
   ```
   cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"
   ```

2. **Double-click** `debug_run.bat`

   OR run manually:
   ```cmd
   BCSrvSqlMq.exe -d
   ```

3. **Watch the console output** for:
   - ✅ "BCSrvSqlMq esta rodando em modo console" (Service started)
   - ✅ Database connection messages
   - ✅ IBM MQ connection messages
   - ✅ Task threads starting (8 threads: Bacen + IF)
   - ❌ Any error messages

4. **Press Ctrl+C** to stop when done testing

5. **Check logs** in `C:\BCSrvSqlMq\Traces\` for detailed output

---

### **Option 2: Install as Windows Service** (After successful test)

Once debug mode works correctly, install as a permanent service.

#### Steps:

1. **Right-click** `install_and_start_service.bat`
2. Select **"Run as administrator"**
3. Follow the prompts

OR manually:
```cmd
REM Install
BCSrvSqlMq.exe -i

REM Start
net start BCSrvSqlMq

REM Check status
sc query BCSrvSqlMq

REM View logs
type C:\BCSrvSqlMq\Traces\*.log
```

---

### **Option 3: Configure Windows Registry** ⚠️ **REQUIRED FOR SERVICE MODE**

When the service is installed (not debug mode), it reads configuration from Windows Registry, **NOT** from BCSrvSqlMq.ini. You must configure the registry after installing the service.

#### Steps:

1. **Right-click** `configure_registry.bat`
2. Select **"Run as administrator"**
3. Press Enter to confirm
4. Choose "Y" when asked to restart the service

OR manually run PowerShell script:
```powershell
# Run PowerShell as Administrator
powershell.exe -ExecutionPolicy Bypass -File configure_registry.ps1
```

#### What this does:
- Reads configuration from BCSrvSqlMq.ini
- Writes all settings to Windows Registry at:
  `HKLM\SYSTEM\CurrentControlSet\Services\BCSrvSqlMq\Parameters`
- Creates registry sections:
  - **DataBase** - PostgreSQL connection settings
  - **MQSeries** - IBM MQ Queue Manager and queue names
  - **Diretorios** - Log and audit directories
  - **Servico** - Monitor port, trace, timeouts
  - **E-Mail** - Email notification settings
  - **Security** - Security and encryption settings
- Optionally restarts the service to apply changes

#### When to use:
✅ **Always after installing the service** (BCSrvSqlMq.exe -i)
✅ After changing any configuration in BCSrvSqlMq.ini
✅ If you get IBM MQ error 2043 (MQRC_OBJECT_NOT_FOUND)
❌ Not needed for debug/console mode (BCSrvSqlMq.exe -d)

---

## 📋 Pre-Test Checklist

Before running, verify:

- [x] **PostgreSQL running**
  ```powershell
  Get-Service postgresql-x64-18
  # Should show: Running
  ```

- [x] **IBM MQ Queue Manager running**
  ```cmd
  dspmq
  # Should show: QMNAME(QM.61377677.01) STATUS(Em execução)
  ```

  If not running:
  ```cmd
  REM Right-click and Run as administrator
  start_mq.bat
  ```

- [x] **Files in build\Release:**
  - BCSrvSqlMq.exe (223 KB)
  - CL32.dll (672 KB)
  - pugixml.dll (167 KB)
  - BCSrvSqlMq.ini (configured)

---

## 🔍 What to Look For

### Success Indicators:

✅ **Console Output:**
```
BCSrvSqlMq esta rodando em modo console.
[Initializing...]
[Database connected]
[MQ connected to QM.61377677.01]
[Starting threads...]
[Thread TASKS_BACENREQ started]
[Thread TASKS_BACENRSP started]
... (8 threads total)
[Monitor started on port 14499]
```

✅ **Log Files Created:**
```
C:\BCSrvSqlMq\Traces\
├── BCSrvSqlMq_2026-02-26.log
└── [Task logs]
```

✅ **Database Activity:**
```sql
-- Check if service wrote to log table
SELECT * FROM spb_log_bacen ORDER BY log_timestamp DESC LIMIT 10;
```

---

### Common Issues:

❌ **"Cannot connect to database"**
- **Check:** PostgreSQL is running
- **Check:** Password in BCSrvSqlMq.ini is correct (`Rama1248`)
- **Test:** Run `test_connection.ps1`

❌ **"Cannot connect to Queue Manager"**
- **Check:** IBM MQ is running (`dspmq`)
- **Fix:** Run `start_mq.bat` as Administrator

❌ **"MQOPEN ended with reason code 2043" (IBM MQ Error)**
- **Cause:** Service is reading from Windows Registry, not BCSrvSqlMq.ini
- **Fix:** Run `configure_registry.bat` as Administrator to update registry
- **Details:** Error 2043 = MQRC_OBJECT_NOT_FOUND (queue names mismatch)
- **When:** Always occurs after installing service before configuring registry

❌ **"DLL not found"**
- **Check:** CL32.dll and pugixml.dll are in same directory as exe
- **Copy:** From project root if missing

❌ **"Access denied to C:\BCSrvSqlMq"**
- **Fix:** Run as Administrator OR grant permissions:
  ```powershell
  # Run as Administrator
  icacls "C:\BCSrvSqlMq" /grant "Users:(OI)(CI)F" /T
  ```

---

## 📊 Expected Behavior

### Startup Sequence:

1. **Initialization** (1-2 seconds)
   - Read BCSrvSqlMq.ini
   - Initialize logging system
   - Load DLLs (CL32, pugixml)

2. **Database Connection** (1-2 seconds)
   - Connect to PostgreSQL via ODBC
   - Verify tables exist
   - Write startup log entry

3. **IBM MQ Connection** (2-3 seconds)
   - Connect to QM.61377677.01
   - Open 8 queues (4 local + 4 remote)
   - Verify queue access

4. **Thread Startup** (3-5 seconds)
   - Start 8 task threads:
     - RmtReq (TASKS_BACENREQ)
     - RmtRsp (TASKS_BACENRSP)
     - RmtRep (TASKS_BACENREP)
     - RmtSup (TASKS_BACENSUP)
     - LocReq (TASKS_IFREQ)
     - LocRsp (TASKS_IFRSP)
     - LocRep (TASKS_IFREP)
     - LocSup (TASKS_IFSUP)

5. **Monitor Thread** (1 second)
   - Start TCP monitor on port 14499
   - Accept health check connections

**Total startup time: ~10-15 seconds**

---

## 🧪 Testing Commands

### Test Database Connection:
```powershell
# Run test script
.\test_connection.ps1

# Or manually via psql
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d bcspbstr -c "SELECT version();"
```

### Test IBM MQ:
```cmd
# Check Queue Manager status
dspmq

# List queues
runmqsc QM.61377677.01
  DISPLAY QLOCAL(*)
  END
```

### Test TCP Monitor (after service starts):
```powershell
Test-NetConnection -ComputerName localhost -Port 14499
```

---

## 📝 Interpreting Logs

### Log File Location:
```
C:\BCSrvSqlMq\Traces\BCSrvSqlMq_YYYY-MM-DD.log
```

### Log Levels:
- **D** (Debug) - Detailed information
- **I** (Info) - General information
- **W** (Warning) - Potential issues
- **E** (Error) - Failures

### Key Log Messages to Look For:

**✅ Good:**
```
[8002] MainSrv: Iniciando PreparaTasks
[8004] MainSrv: Configurando DSN database
[8007] MainSrv: Criando threads
[8008] MainSrv: Thread Monitor ThreadId = xxxx
```

**❌ Problems:**
```
[8003] MainSrv: Erro ao criar Monitor
[8008] MainSrv: Erro SQLConfigDataSource
[80xx] MainSrv: Falha ao conectar MQ
```

---

## 🔧 Command Line Options

BCSrvSqlMq supports these flags:

| Flag | Description |
|------|-------------|
| `-v` | Show version and installation status |
| `-i` | Install as Windows Service |
| `-u` | Uninstall Windows Service |
| `-d` | Run in debug/console mode (foreground) |

**Examples:**
```cmd
REM Check version
BCSrvSqlMq.exe -v

REM Test in console
BCSrvSqlMq.exe -d

REM Install service
BCSrvSqlMq.exe -i

REM Uninstall service
BCSrvSqlMq.exe -u
```

---

## 📁 Helper Scripts Created

| File | Purpose |
|------|---------|
| `debug_run.bat` | ⭐ Run in console/debug mode |
| `install_and_start_service.bat` | Install and start as Windows Service |
| `uninstall_service.bat` | Remove Windows Service |
| `start_mq.bat` | Start IBM MQ Queue Manager |
| `test_connection.ps1` | Test database connectivity |
| `verify_complete_setup.ps1` | Check all components |

---

## ⏭️ Next Steps

### 1. **First Test Run** (Do this now!)

```cmd
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"
debug_run.bat
```

Watch for errors and check `C:\BCSrvSqlMq\Traces\` for logs.

### 2. **If Test Succeeds:**
- Review logs for any warnings
- Test message processing (send test messages to queues)
- Install as Windows Service
- Configure for automatic startup

### 3. **If Test Fails:**
- Note the error message
- Check logs in C:\BCSrvSqlMq\Traces
- Check Windows Event Viewer (Application log)
- Verify pre-test checklist items

---

## 🆘 Getting Help

### Debug Information to Collect:

1. **Console output** (copy from console window)
2. **Log files** (`C:\BCSrvSqlMq\Traces\*.log`)
3. **Windows Event Log**:
   ```powershell
   Get-EventLog -LogName Application -Newest 20 | Where-Object {$_.Message -like '*BCSrvSqlMq*'}
   ```
4. **Component status**:
   ```cmd
   dspmq
   sc query postgresql-x64-18
   netstat -an | findstr 14499
   ```

---

## 🎯 Success Criteria

The service is working correctly when:

✅ Service starts without errors
✅ Database connection established
✅ MQ connection established
✅ All 8 threads running
✅ Monitor listening on port 14499
✅ Logs being written
✅ Can process test messages

---

**Testing guide created:** 2026-02-26
**Ready for:** First test run!

## 🚀 **START HERE:**

```cmd
cd build\Release
debug_run.bat
```

**Good luck!** 🍀
