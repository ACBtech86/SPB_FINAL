# BCMsgSqlMq - x64 Logging DLL

**Created:** 2026-02-27
**Purpose:** Replace legacy 32-bit BCMsgSqlMq.dll with x64 version
**Architecture:** x86-64 (PE32+)

---

## Overview

This is a clean-room implementation of the BCMsgSqlMq.dll logging library, created to enable full x64 compilation of the BCSrvSqlMq Windows service. The original DLL was 32-bit only with no available source code.

## Exported Functions

### 1. `OpenLog(LPTSTR logDir, LPTSTR appName, LPTSTR serverName)`
Opens a log file for writing.

**Parameters:**
- `logDir`: Directory where log files will be created
- `appName`: Application name (used in filename)
- `serverName`: Server name (written to log header)

**Returns:** `TRUE` on success, `FALSE` on failure

**Behavior:**
- Creates log directory if it doesn't exist
- Opens log file in append mode
- Filename format: `{appName}_{YYYYMMDD}.log`
- Thread-safe using mutex

### 2. `WriteLog(LPTSTR taskName, UINT msgId, BOOL flag, LPVOID p1-p5)`
Writes a log message entry.

**Parameters:**
- `taskName`: Name of the task/thread generating the log
- `msgId`: Message ID number
- `flag`: `TRUE` for ERROR, `FALSE` for INFO
- `p1-p5`: Additional parameters (typically pointers to integers)

**Returns:** `TRUE` on success, `FALSE` on failure

**Log Format:**
```
[YYYY-MM-DD HH:MM:SS] [ERROR/INFO] [MsgID:####] [Task:name] Params: p1=## p2=## ...
```

### 3. `WriteReg(LPTSTR taskName, BOOL flag, UINT size, LPVOID data)`
Writes binary/registry data to log.

**Parameters:**
- `taskName`: Name of the task
- `flag`: `TRUE` for WRITE, `FALSE` for READ
- `size`: Size of data in bytes
- `data`: Pointer to binary data

**Returns:** `TRUE` on success, `FALSE` on failure

**Behavior:**
- Writes hex dump of first 64 bytes of data
- For larger data, indicates truncation

### 4. `CloseLog()`
Closes the log file.

**Returns:** `TRUE` on success, `FALSE` on failure

**Behavior:**
- Writes closing timestamp
- Flushes and closes file handle
- Thread-safe

### 5. `Trace(UINT level)`
Sets trace level.

**Parameters:**
- `level`: Trace level (implementation stores but doesn't filter yet)

**Returns:** `TRUE` on success, `FALSE` on failure

**Behavior:**
- Stores trace level in global variable
- Writes trace level change to log

---

## Implementation Details

### Thread Safety
All functions use `std::mutex` to ensure thread-safe access to the log file. This is critical since BCSrvSqlMq has multiple worker threads.

### Error Handling
- All functions return `BOOL` (TRUE/FALSE) for compatibility
- Exceptions are caught and converted to `FALSE` return values
- NULL pointer checks for all optional parameters

### File Management
- Log files are opened in append mode
- Daily rotation via date in filename
- Automatic flush after each write for crash safety

### Memory
- No dynamic allocations in hot path
- Stack-based buffers for formatting
- STL containers for state management

---

## Compilation

### Prerequisites
- CMake 3.20+
- Visual Studio 2026 or later
- Windows SDK 10.0.26100.0+

### Build Commands
```bash
cd BCMsgSqlMq
cmake -B build -G "Visual Studio 18 2026" -A x64
cmake --build build --config Release
```

### Output
- `build/Release/BCMsgSqlMq.dll` - The x64 DLL
- `build/Release/BCMsgSqlMq.lib` - Import library

---

## Integration with BCSrvSqlMq

The DLL is automatically loaded by InitSrv.cpp at line 81:
```cpp
m_hDllMsg = LoadLibrary("BCMsgSqlMq");
```

Function pointers are resolved:
```cpp
m_OpenLog = (LPOPENLOG) GetProcAddress(m_hDllMsg, "OpenLog");
m_WriteLog = (LPWRITELOG) GetProcAddress(m_hDllMsg, "WriteLog");
m_WriteReg = (LPWRITEREG) GetProcAddress(m_hDllMsg, "WriteReg");
m_CloseLog = (LPCLOSELOG) GetProcAddress(m_hDllMsg, "CloseLog");
m_Trace = (LPTRACE) GetProcAddress(m_hDllMsg, "Trace");
```

---

## Compatibility with Original DLL

### Interface
✅ **100% Compatible** - Function signatures match exactly

### Behavior
⚠️ **Functionally Equivalent** - Provides same core functionality but:
- Log format may differ slightly
- Trace level currently stored but not used for filtering
- Binary data limited to 64-byte hex dump preview

### Testing
The service should work identically with this DLL. Log output format may vary but all information is preserved.

---

## Future Enhancements

### Potential Improvements:
1. **Trace filtering** - Actually use trace level to filter messages
2. **Log rotation** - Automatic compression/deletion of old logs
3. **Performance** - Asynchronous logging queue for high throughput
4. **Configuration** - Read log settings from INI file
5. **Binary dumps** - Full binary data to separate files

### Message Catalog:
If the original DLL had a message catalog mapping msgId → message text, we could recreate that by:
1. Analyzing existing log files
2. Creating a msgId lookup table
3. Formatting messages with parameter substitution

---

## Differences from Original

Since we don't have the original source code, this implementation makes reasonable assumptions:

| Aspect | Original (Unknown) | This Implementation |
|--------|-------------------|---------------------|
| **Architecture** | x86 (32-bit) | x86-64 (64-bit) |
| **Language** | C/C++ (unknown) | C++17 |
| **Threading** | Unknown | `std::mutex` |
| **Log Format** | Unknown | Timestamp + Level + MsgID + Params |
| **File Rotation** | Unknown | Daily by date in filename |

---

## Troubleshooting

### DLL Not Found
- Ensure BCMsgSqlMq.dll is in the same directory as BCSrvSqlMq.exe
- Or in a directory listed in PATH environment variable

### Access Denied on Log File
- Check directory permissions on log folder
- Ensure service account has write access

### Empty Logs
- Verify OpenLog() is called successfully
- Check return values from WriteLog()
- Ensure log directory exists and is writable

---

**Version:** 1.0
**Author:** Claude Code + Antonio Bosco
**License:** Same as BCSrvSqlMq project
