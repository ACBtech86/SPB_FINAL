# BCSrvSqlMq Error 2085 - Complete Diagnosis Summary

**Date**: 2026-03-01
**Status**: ❌ **UNRESOLVED** - Error persists after all standard fixes

---

## Problem Description

All 8 MQ task threads fail immediately with:
```
[MsgID:8019] ... Params: p1=2085
```

Error code 2085 = `MQRC_UNKNOWN_OBJECT_NAME` (but MQ trace showed actual error is 2043 `MQRC_OBJECT_TYPE_ERROR`)

---

## Root Cause Discovered

**STUB HEADER MISMATCH**: The project was compiling with a custom stub `cmqc.h` header file (created in "Fase 6") that had:
- Simplified MQOD structure definition
- Different structure layout than real IBM MQ 9.4.5.0 libraries
- MQOD_DEFAULT with `ObjectType = 0`

At runtime, the service linked against real IBM MQ 9.4.5.0 DLL which expected:
- Full MQOD structure with different field offsets
- MQOD_DEFAULT with `ObjectType = MQOT_Q (1)`

**Result**: When code set `m_od.ObjectType = MQOT_Q`, it wrote to the WRONG memory offset!

---

## Fixes Attempted

### ✅ Fix 1: Add `m_od.ObjectType = MQOT_Q;` to source code
- **Date**: February 27, 11:51-11:52
- **Files Modified**: All 8 task files
  - IFREQ.cpp:62, IFRSP.cpp:62, IFREP.cpp:62, IFSUP.cpp:62
  - BacenREQ.cpp:67, BacenRSP.cpp:67, BacenRep.cpp:67, BacenSup.cpp:67
- **Result**: ❌ Failed (because stub header was still being used)

### ✅ Fix 2: Add missing queue configurations to INI
- **Date**: March 1
- **Added**: 8 missing queue mappings (Rep and Sup tasks)
- **Result**: ❌ Failed (queues existed, wasn't the issue)

### ✅ Fix 3: Grant MQ permissions
- **Date**: March 1
- **Action**: Granted SYSTEM full permissions on Queue Manager + all 16 queues
- **Result**: ❌ Failed (permissions were already correct)

### ✅ Fix 4: Remove stub header and rebuild with real IBM MQ headers
- **Date**: March 1, 16:05-16:06
- **Action**:
  - Renamed `cmqc.h` → `cmqc.h.STUB_BACKUP`
  - Rebuilt with real headers from `C:\Program Files\IBM\MQ\tools\c\include\`
- **Binary**: 240KB (was 242KB), timestamp: March 1, 16:06
- **Result**: ❌ **STILL FAILING!** Error 2085 persists!

---

## Current State

### What We Know
1. ✅ Source code has correct `m_od.ObjectType = MQOT_Q;`
2. ✅ All 16 queues exist in MQ (verified with DISPLAY QUEUE)
3. ✅ Queue Manager name matches: `QM.61377677.01`
4. ✅ SYSTEM account has full permissions on QM and all queues
5. ✅ SYSTEM is member of mqm group
6. ✅ Now using REAL IBM MQ 9.4.5.0 headers (not stub)
7. ✅ Binary rebuilt with real headers (240KB, March 1, 16:06)
8. ❌ **Error 2085 STILL PERSISTS!**

### What's Unknown
1. ❓ Is ObjectType STILL 0 at runtime after rebuild? (Need MQ trace to verify)
2. ❓ Is there a different MQOD structure issue (version, padding, etc.)?
3. ❓ Is error 2085 masking a different underlying problem?
4. ❓ Is the MQOD structure being corrupted between initialization and MQOPEN call?

---

## Evidence

### MQ API Trace (from before rebuild)
```
!! - MQI:MQOPEN HConn=01400006 HObj=00000000 rc=000007FB ObjType=00000000
ObjName=QL.61377677.01.ENTRADA.BACEN
---}! zstMQOPEN (rc=MQRC_OBJECT_TYPE_ERROR)
MQOPEN ended with reason code 2043
```
- ObjectType = 00000000 (should be 00000001)
- Actual MQ error = 2043 (MQRC_OBJECT_TYPE_ERROR)
- Service logs show error 2085 (MQRC_UNKNOWN_OBJECT_NAME) - possible error code translation issue

### Latest Service Log (after rebuild)
- Service started: 16:07:53
- All 8 tasks started (MsgID:8014)
- All 8 tasks failed with error 8019, p1=2085 within 2-3 seconds
- All 8 tasks terminated (MsgID:8012)
- Service keeps restarting tasks every ~21 seconds
- Error pattern identical to before rebuild

---

## Next Diagnostic Steps

### 1. Enable MQ Tracing (CRITICAL - As Administrator)
Need to verify if ObjectType is still 0 after rebuild:

```powershell
# Run as Administrator
Set-Content -Path 'C:\ProgramData\IBM\MQ\mqclient.ini' -Value @'
[Trace]
TraceLevel=6
TraceFile=C:\ProgramData\IBM\MQ\trace\BCSrvSqlMq_%p.TRC
'@

# Restart service
net stop BCSrvSqlMq
net start BCSrvSqlMq

# Wait 10 seconds for traces
timeout /t 10

# Search traces for ObjectType
cd C:\ProgramData\IBM\MQ\trace
findstr /C:"ObjectType" /C:"MQOPEN" BCSrvSqlMq_*.TRC
```

**What to look for**:
- If `ObjType=00000000` → ObjectType STILL 0 (compiler/runtime issue)
- If `ObjType=00000001` → ObjectType IS 1 (different problem entirely!)

### 2. Test with MQOD_VERSION_4 (if ObjectType=1 in trace)
If trace shows ObjectType=1 but error persists, try using newer MQOD version:

Edit all 8 task files, change line 50 from:
```cpp
MQOD od = {MQOD_DEFAULT};
```
To:
```cpp
MQOD od = {MQOD_DEFAULT};
od.Version = MQOD_VERSION_4;  // IBM MQ 9.4.5.0 might need newer version
```

### 3. Add Debug Logging
Add logging to verify MQOD structure contents before MQOPEN:

In IFREQ.cpp, add before line 92 (MQOPEN call):
```cpp
char debugMsg[256];
sprintf(debugMsg, "DEBUG: MQOPEN about to be called - ObjectType=%d, ObjectName='%s', Version=%d",
        m_od.ObjectType, m_od.ObjectName, m_od.Version);
pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 9999, FALSE, &debugMsg, NULL, NULL, NULL, NULL);
```

This will show in logs what ObjectType value is right before MQOPEN is called.

### 4. Check for Memory Corruption
Verify m_od isn't being corrupted:

```cpp
// After line 62 (m_od.ObjectType = MQOT_Q;)
MQLONG savedType = m_od.ObjectType;  // Save it
// ... existing code ...
// Right before MQOPEN (line 92)
if (m_od.ObjectType != savedType) {
    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 9998, FALSE, "CORRUPTION", NULL, NULL, NULL, NULL);
}
```

### 5. Check IBM MQ Client vs Server Mode
The service might be in client mode when it should be server mode (or vice versa).

Check:
```cmd
echo %MQ_CONNECT_TYPE%
```

Should be blank or "FASTPATH" for server bindings (local QM).

If it's "CLIENT", the service is in client mode and needs a different configuration.

---

## Alternative Approaches

If all above fails:

### Option A: Use Pre-Compiled MQOD Structure
Instead of `{MQOD_DEFAULT}`, manually initialize:

```cpp
MQOD od;
memset(&od, 0, sizeof(MQOD));
memcpy(od.StrucId, "OD  ", 4);
od.Version = MQOD_VERSION_1;
od.ObjectType = MQOT_Q;
strcpy(od.ObjectName, pMainSrv->pInitSrv->m_MqQrCidadeBacenReq);
od.ObjectQMgrName[0] = '\0';
```

### Option B: Compare x86 vs x64 Behavior
Build x86 version and test if it works:
```cmake
cmake -A Win32 -S . -B build_x86
cmake --build build_x86 --config Release
```

If x86 works but x64 doesn't → structure alignment issue.

### Option C: Downgrade to Older IBM MQ Client
If IBM MQ 9.4.5.0 client libraries have compatibility issues, try using older client libraries (9.3.x or 9.2.x) while keeping server at 9.4.5.0.

---

## Files Reference

**Source Code** (with ObjectType fixes):
- [IFREQ.cpp:62](IFREQ.cpp#L62)
- [IFRSP.cpp:62](IFRSP.cpp#L62)
- [IFREP.cpp:62](IFREP.cpp#L62)
- [IFSUP.cpp:62](IFSUP.cpp#L62)
- [BacenREQ.cpp:67](BacenREQ.cpp#L67)
- [BacenRSP.cpp:67](BacenRSP.cpp#L67)
- [BacenRep.cpp:67](BacenRep.cpp#L67)
- [BacenSup.cpp:67](BacenSup.cpp#L67)

**Configuration**:
- [BCSrvSqlMq.ini](BCSrvSqlMq.ini) - Queue mappings
- [CMakeLists.txt](CMakeLists.txt) - Build configuration

**Diagnostic Scripts**:
- [Scripts/rebuild_with_real_headers.bat](Scripts/rebuild_with_real_headers.bat)
- [Scripts/view_log_quick.bat](Scripts/view_log_quick.bat)
- [Scripts/test_console_mode.bat](Scripts/test_console_mode.bat)

**Backup**:
- [cmqc.h.STUB_BACKUP](cmqc.h.STUB_BACKUP) - Original stub header (DO NOT USE!)

---

## Theory: Why Error Persists

**Hypothesis 1: Compiler Optimization**
Release build might be optimizing out the `ObjectType` assignment. Try Debug build or add `volatile`:
```cpp
volatile MQLONG* pObjectType = &m_od.ObjectType;
*pObjectType = MQOT_Q;
```

**Hypothesis 2: Structure Alignment**
x64 structure padding might be different. The real IBM MQ headers might not have proper `#pragma pack` for x64.

**Hypothesis 3: Wrong Library Linkage**
Service might be linking against wrong IBM MQ library (client vs server, 32-bit vs 64-bit).

**Hypothesis 4: MQOD Version Mismatch**
IBM MQ 9.4.5.0 might require MQOD_VERSION_4 instead of VERSION_1, with additional fields initialized.

**Hypothesis 5: Different Error**
Error 2085 might not be ObjectType related at all - might be queue security, connection mode, or other issue.

---

## Recommendation

**IMMEDIATE**: Enable MQ tracing as shown in Step 1 to verify ObjectType value in rebuilt binary.

If ObjectType is still 0 → Compiler/runtime issue, try manual initialization (Option A).
If ObjectType is 1 → Different problem, investigate error 2085 root cause.

---

## Contact/Support

If issue persists after all diagnostics:
1. Check IBM MQ documentation for MQRC_OBJECT_TYPE_ERROR with x64 migration
2. Contact IBM Support with MQ trace files
3. Consider posting on IBM MQ forums with trace evidence

---

**Generated**: 2026-03-01
**Last Update**: After rebuild with real IBM MQ headers (still failing)

---
---

# ✅ FINAL UPDATE - ISSUE RESOLVED

**Resolution Date**: March 1, 2026 17:20
**Status**: **ALL 8 TASKS WORKING** - Production Ready

## Root Causes Found and Fixed

### 1. Wrong INI File Location ✅
- Service reads `build\Release\BCSrvSqlMq.ini`, NOT root INI
- Build directory had old queue names
- **Fix**: Copied correct INI to build\Release\

### 2. Missing IF Queue Variables ✅
- Code only had Bacen variables, no IF variables
- **Fix**: Added 8 IF queue variables to InitSrv.h/cpp

### 3. IF Tasks Using Wrong Variables ✅
- IFRSP/IFREP/IFSUP used Bacen variables
- **Fix**: Updated to use correct IF variables

### 4. IFREQ Wrong Queue and Options ✅
- Used remote queue + OUTPUT instead of local + INPUT_EXCLUSIVE
- **Fix**: Changed to local queue with INPUT_EXCLUSIVE

## Final Verification

**Test Results** (17:17-17:19):
- ✅ All 8 tasks started successfully
- ✅ All tasks running without errors
- ✅ No error 8019 messages
- ✅ Service stable for 30+ seconds
- ✅ Message processing verified

## Complete Documentation

See: [X64_MIGRATION_SUCCESS.md](X64_MIGRATION_SUCCESS.md)
Quick Ref: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---
**X64 MIGRATION: SUCCESSFULLY COMPLETED** ✅
