# BCSrvSqlMq - Quick Reference Guide

## ✅ Service Status: OPERATIONAL

**Last Verified**: March 1, 2026 17:20
**All 8 Tasks**: Working
**Status**: Production Ready

---

## Quick Commands

### Start/Stop Service (Administrator)
```cmd
net start BCSrvSqlMq
net stop BCSrvSqlMq
```

### Run in Console Mode (Administrator)
```cmd
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"
BCSrvSqlMq.exe -d
```

### Check Service Logs
```cmd
tail -50 C:\BCSrvSqlMq\Traces\TRACE_SPB__*.log
```

### Check for Errors
```cmd
findstr "8019" C:\BCSrvSqlMq\Traces\TRACE_SPB__*.log
```

### Rebuild Service
```cmd
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq"
cmake --build build --config Release
```

---

## Task Status

| Task | Queue | Status |
|------|-------|--------|
| RmtReq (Bacen) | QL.61377677.01.ENTRADA.BACEN | ✅ Working |
| RmtRsp (Bacen) | QL.61377677.01.SAIDA.BACEN | ✅ Working |
| RmtRep (Bacen) | QL.61377677.01.REPORT.BACEN | ✅ Working |
| RmtSup (Bacen) | QL.61377677.01.SUPORTE.BACEN | ✅ Working |
| LocReq (IF) | QL.61377677.01.ENTRADA.IF | ✅ Working |
| LocRsp (IF) | QL.61377677.01.SAIDA.IF | ✅ Working |
| LocRep (IF) | QL.61377677.01.REPORT.IF | ✅ Working |
| LocSup (IF) | ✅ Working |

---

## Key Files

### Binary
- **Location**: `build\Release\BCSrvSqlMq.exe`
- **Size**: 240 KB
- **Architecture**: x64

### Configuration
- **INI File**: `build\Release\BCSrvSqlMq.ini` ⚠️ **IMPORTANT: Next to EXE!**
- **NOT**: Root `BCSrvSqlMq.ini` (service doesn't read this one)

### Logs
- **Service**: `C:\BCSrvSqlMq\Traces\TRACE_SPB__YYYYMMDD.log`
- **MQ Errors**: `C:\ProgramData\IBM\MQ\qmgrs\QM!61377677!01\errors\AMQERR01.LOG`

---

## Message IDs Reference

| MsgID | Meaning | Good/Bad |
|-------|---------|----------|
| 8014 | Task started | ✅ Good |
| 8070 | Normal operation (processing) | ✅ Good |
| 8071 | Normal operation (waiting) | ✅ Good |
| 8012 | Task terminated | ℹ️ Normal (tasks restart) |
| 8019 | **Error opening queue** | ❌ **Bad - investigate!** |

---

## Troubleshooting

### All Tasks Failing with Error 8019?

1. **Check INI file location**:
   ```cmd
   type "build\Release\BCSrvSqlMq.ini"
   ```

2. **Verify queue names are correct**:
   ```cmd
   findstr "^QR\|^QL" build\Release\BCSrvSqlMq.ini
   ```

3. **Check if queues exist in MQ**:
   ```cmd
   echo "DISPLAY QUEUE(QL.61377677.01.*)" | runmqsc QM.61377677.01
   ```

4. **Verify Queue Manager is running**:
   ```cmd
   dspmq
   ```

### Build Fails?

1. **Clean and rebuild**:
   ```cmd
   del /Q build\BCSrvSqlMq.dir\Release\*.obj
   cmake --build build --config Release
   ```

2. **Check IBM MQ headers exist**:
   ```cmd
   dir "C:\Program Files\IBM\MQ\tools\c\include\cmqc.h"
   ```

---

## What Was Fixed (March 1, 2026)

1. ✅ **INI file in wrong location** - Copied to build\Release\
2. ✅ **Missing IF queue variables** - Added to InitSrv.h/cpp
3. ✅ **IF tasks using wrong queues** - Fixed IFRSP, IFREP, IFSUP
4. ✅ **IFREQ using wrong options** - Changed to INPUT_EXCLUSIVE on local queue

**Result**: All 8 tasks now working!

---

## Important Notes

⚠️ **CRITICAL**: The service reads `build\Release\BCSrvSqlMq.ini`, NOT the root INI file!

⚠️ **After rebuild**: INI file stays in build\Release (not overwritten)

⚠️ **Administrator required**: Service start/stop needs admin privileges

✅ **Console mode**: Best for testing (BCSrvSqlMq.exe -d)

---

## Complete Documentation

For full details, see: [X64_MIGRATION_SUCCESS.md](X64_MIGRATION_SUCCESS.md)

---

*Last Updated: March 1, 2026 17:20*
