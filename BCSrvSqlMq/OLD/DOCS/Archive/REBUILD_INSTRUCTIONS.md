# BCSrvSqlMq - Rebuild and Deploy Instructions

## Problem Summary

**Issue**: MQ trace shows `ObjectType=0` instead of `ObjectType=1` (MQOT_Q)
**Error**: MQRC_OBJECT_TYPE_ERROR (2043) when opening queues
**Cause**: Binary may have stale build artifacts despite source code having correct fixes
**Solution**: Clean rebuild with proper compilation

## Timeline

- **Feb 27, 11:51-11:52**: Source code fixed with `m_od.ObjectType = MQOT_Q;`
- **Mar 1, 08:53**: Binary compiled (should include fixes)
- **Mar 1, 14:49-15:21**: Testing revealed ObjectType still shows as 0

## Source Code Status ✅

All 8 task files have the correct fix:

- ✅ [IFREQ.cpp:62](IFREQ.cpp#L62) - `m_od.ObjectType = MQOT_Q;`
- ✅ [IFRSP.cpp:62](IFRSP.cpp#L62) - `m_od.ObjectType = MQOT_Q;`
- ✅ [IFREP.cpp:62](IFREP.cpp#L62) - `m_od.ObjectType = MQOT_Q;`
- ✅ [IFSUP.cpp:62](IFSUP.cpp#L62) - `m_od.ObjectType = MQOT_Q;`
- ✅ [BacenREQ.cpp:67](BacenREQ.cpp#L67) - `m_od.ObjectType = MQOT_Q;`
- ✅ [BacenRSP.cpp:67](BacenRSP.cpp#L67) - `m_od.ObjectType = MQOT_Q;`
- ✅ [BacenRep.cpp:67](BacenRep.cpp#L67) - `m_od.ObjectType = MQOT_Q;`
- ✅ [BacenSup.cpp:67](BacenSup.cpp#L67) - `m_od.ObjectType = MQOT_Q;`

## Rebuild Steps

### Option 1: Automated Script (Recommended)

**Run as Administrator:**

```batch
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\Scripts"
rebuild_and_deploy.bat
```

This script will:
1. ✅ Stop the BCSrvSqlMq service
2. ✅ Delete old object files (force recompile)
3. ✅ Rebuild the project
4. ✅ Restart the service
5. ✅ Display service status

### Option 2: Manual Steps

**Open Command Prompt as Administrator:**

```batch
# Stop service
net stop BCSrvSqlMq

# Navigate to project directory
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq"

# Clean rebuild
del /Q build\BCSrvSqlMq.dir\Release\*.obj
cmake --build build --config Release

# Restart service
net start BCSrvSqlMq

# Check status
sc query BCSrvSqlMq
```

## Testing

### Test 1: Console Mode (Recommended for first test)

**Run as Administrator:**

```batch
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\Scripts"
test_console_mode.bat
```

**Expected Output:**
```
BCSrvSqlMq esta rodando em modo console.
Task MainSrv Iniciada
Task Monitor Iniciada
Task BacenREQ Iniciada
Task BacenRSP Iniciada
Task BacenRep Iniciada
Task BacenSup Iniciada
Task IFREQ Iniciada
Task IFRSP Iniciada
Task IFREP Iniciada
Task IFSUP Iniciada
```

**❌ BAD Output (means bug still exists):**
```
8019 E MQOPEN ended with reason code 2043
8012 I Task * Terminada
```

### Test 2: Check Service Logs

```batch
type C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log | findstr /C:"Iniciada" /C:"8019"
```

**Good result:**
- 10 lines with "Iniciada" (8 tasks + MainSrv + Monitor)
- 0 lines with "8019"

**Bad result:**
- Lines with "8019 E MQOPEN ended with reason code 2043"
- Lines with "8012 I Task * Terminada"

### Test 3: MQ API Trace (if bug persists)

If error 2043 still appears, enable MQ tracing:

```batch
cd Scripts
enable_mq_trace.bat

# Restart service to generate fresh traces
net stop BCSrvSqlMq
net start BCSrvSqlMq

# Wait 10 seconds
timeout /t 10

# Check trace for ObjectType
cd C:\ProgramData\IBM\MQ\trace
findstr /C:"ObjectType" /C:"MQOPEN" BCSrvSqlMq_*.TRC
```

Look for:
- ✅ **Good**: `ObjType=00000001` (MQOT_Q)
- ❌ **Bad**: `ObjType=00000000` (MQOT_NONE)

Don't forget to disable tracing when done:
```batch
cd Scripts
disable_mq_trace.bat
```

## Success Criteria

✅ **Build completes without errors**
✅ **Service starts successfully**
✅ **All 8 tasks show "Iniciada" message**
✅ **NO error 2043 (MQRC_OBJECT_TYPE_ERROR) in logs**
✅ **NO error 2085 (MQRC_UNKNOWN_OBJECT_NAME) in logs**
✅ **All tasks remain running (no "Terminada" messages)**

## Troubleshooting

### Problem: "Access Denied" when stopping service

**Solution**: Run Command Prompt as Administrator
- Right-click Command Prompt → "Run as administrator"
- Or right-click the .bat script → "Run as administrator"

### Problem: Build still shows ObjectType=0 after rebuild

**Possible causes:**
1. **Compiler optimization issue** - Release build may be optimizing out the assignment
2. **Wrong source location** - Verify you're building from the correct directory
3. **Cached CMake configuration** - Try full rebuild:

```batch
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq"
rmdir /s /q build
cmake -S . -B build
cmake --build build --config Release
```

### Problem: Service fails to start

**Check:**
1. Queue Manager is running: `dspmq`
2. All 16 queues exist: `cd Scripts && verify_all_queues.ps1`
3. SYSTEM has permissions: `cd Scripts && check_mqm_group.bat`
4. Test in console mode first: `cd Scripts && test_console_mode.bat`

## Next Steps After Successful Build

Once the rebuild fixes the ObjectType error:

1. ✅ **Verify all 8 tasks are running** without errors
2. ✅ **Test OpenSSL encryption** functionality (original goal):
   - Check logs for: `ReadPublicKey`, `ReadPrivatKey`, `funcAssinar`, `funcCript`
   - Verify message encryption/signing works correctly
3. ✅ **Monitor production** for any remaining issues

## Files Modified/Created

**Source Code** (already fixed on Feb 27):
- IFREQ.cpp, IFRSP.cpp, IFREP.cpp, IFSUP.cpp
- BacenREQ.cpp, BacenRSP.cpp, BacenRep.cpp, BacenSup.cpp

**New Scripts** (Mar 1):
- [Scripts/rebuild_and_deploy.bat](Scripts/rebuild_and_deploy.bat) - Automated rebuild
- [Scripts/test_console_mode.bat](Scripts/test_console_mode.bat) - Console testing
- [Scripts/enable_mq_trace.bat](Scripts/enable_mq_trace.bat) - Enable MQ API trace
- [Scripts/disable_mq_trace.bat](Scripts/disable_mq_trace.bat) - Disable MQ API trace
- [Scripts/verify_all_queues.ps1](Scripts/verify_all_queues.ps1) - Verify queue existence
- [Scripts/check_mqm_group.bat](Scripts/check_mqm_group.bat) - Check mqm group membership
- [Scripts/grant_permissions_each_queue.bat](Scripts/grant_permissions_each_queue.bat) - Grant MQ permissions

**Configuration** (fixed on Mar 1):
- [BCSrvSqlMq.ini](BCSrvSqlMq.ini) - Added 8 missing queue configurations

**Documentation**:
- This file: [REBUILD_INSTRUCTIONS.md](REBUILD_INSTRUCTIONS.md)

## Contact

If the rebuild doesn't fix the issue, we may need to:
- Check compiler optimization flags in CMakeLists.txt
- Build a Debug version for testing
- Add debug logging to verify ObjectType value before MQOPEN call
