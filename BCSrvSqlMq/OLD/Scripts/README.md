# BCSrvSqlMq Scripts Directory

**Last Updated**: March 1, 2026
**Status**: Production Ready - x64 Migration Complete

---

## Essential Scripts (Keep These)

### 🚀 Service Management

#### **INSTALAR.bat**
- **Purpose**: Install BCSrvSqlMq as Windows Service
- **Requires**: Administrator privileges
- **Usage**: Right-click → Run as Administrator
- **Note**: Registers service in Windows Services

#### **InstalarSimples.bat**
- **Purpose**: Simple installation without complex tests
- **Requires**: Administrator privileges
- **When to use**: First-time installation or clean reinstall

#### **INICIAR.bat**
- **Purpose**: Start BCSrvSqlMq Windows Service
- **Requires**: Administrator privileges
- **Alternative**: `net start BCSrvSqlMq`

#### **INICIAR-RAPIDO.bat**
- **Purpose**: Quick start with timeout
- **Requires**: Administrator privileges
- **When to use**: Testing service startup

---

### 📋 Monitoring & Logs

#### **VER-LOG.bat**
- **Purpose**: View current service log
- **Shows**: Last 50 lines of TRACE_SPB log
- **Location**: Reads from `C:\BCSrvSqlMq\Traces\`
- **When to use**: Check if service is running correctly

---

### 🔨 Build & Deploy

#### **rebuild_and_deploy.bat**
- **Purpose**: Rebuild service and restart
- **Requires**: Administrator privileges
- **Steps**:
  1. Stops service
  2. Cleans build directory
  3. Rebuilds with CMake
  4. Restarts service
- **When to use**: After code changes

---

### 🧪 Testing

#### **test_console_mode.bat**
- **Purpose**: Run service in console mode (not as Windows Service)
- **Requires**: Administrator privileges
- **Usage**: For debugging and testing
- **Note**: Shows real-time output, press Ctrl+C to stop

#### **TESTAR-CRYPTO.bat** / **TESTAR-CRYPTO.ps1**
- **Purpose**: Test OpenSSL 3.6.1 encryption
- **Tests**:
  - OpenSSL library loading
  - RSA encryption/decryption
  - AES encryption/decryption
  - Certificate operations
- **When to use**: Verify OpenSSL integration

#### **send_test_message.bat** / **send_test_message.ps1**
- **Purpose**: Send test message to MQ queue
- **Triggers**: Service message processing
- **Queue**: QL.61377677.01.ENTRADA.BACEN
- **When to use**: Verify message processing works

---

### ⚙️ Setup

#### **setup_database.bat**
- **Purpose**: Initialize PostgreSQL database
- **Creates**: Required tables and schemas
- **Database**: bcspbstr on localhost:5432
- **When to use**: First-time setup or database reset

#### **setup_mq_queues.bat**
- **Purpose**: Create all 16 MQ queues
- **Requires**: IBM MQ admin privileges
- **Creates**:
  - 8 Local queues (QL.*)
  - 8 Remote queues (QR.*)
- **When to use**: First-time setup or queue recreation

---

### 🔍 Verification

#### **verify_complete_setup.ps1**
- **Purpose**: Complete system verification
- **Checks**:
  - Service binary exists
  - IBM MQ installed
  - PostgreSQL accessible
  - All 16 queues exist
  - Service can start
- **When to use**: After installation or migration

---

## Cleanup

### **CLEANUP_SCRIPTS.bat** ⚠️
- **Purpose**: Organize scripts after troubleshooting
- **Actions**:
  - Moves troubleshooting scripts to Archive/
  - Deletes redundant scripts
  - Keeps essential operational scripts
- **When to use**: After completing x64 migration (already done)

---

## Script Usage Guide

### Daily Operations
```batch
REM View logs
VER-LOG.bat

REM Start service
INICIAR.bat

REM Stop service (as Admin)
net stop BCSrvSqlMq
```

### After Code Changes
```batch
REM Rebuild and deploy
rebuild_and_deploy.bat
```

### Testing
```batch
REM Console mode (debugging)
test_console_mode.bat

REM Test OpenSSL
TESTAR-CRYPTO.bat

REM Send test message
send_test_message.bat
```

### First-Time Setup
```batch
REM 1. Setup MQ queues
setup_mq_queues.bat

REM 2. Setup database
setup_database.bat

REM 3. Install service
INSTALAR.bat

REM 4. Verify everything
verify_complete_setup.ps1
```

---

## Archive Directory

**Location**: `Scripts/Archive/Troubleshooting/`

Contains scripts used during x64 migration troubleshooting:
- Queue diagnostics (error 2085 resolved)
- Permission scripts (issues resolved)
- MQ tracing scripts (migration complete)
- Error-specific diagnostics (no longer needed)

**Status**: Archived for reference, not needed for normal operation

---

## Important Notes

⚠️ **Administrator Required**: Most scripts need admin privileges
⚠️ **IBM MQ**: Must be installed and running
⚠️ **PostgreSQL**: Required for database operations
⚠️ **Build Tools**: Visual Studio 2022 and CMake required for rebuild scripts

✅ **All Issues Resolved**: Service is production ready
✅ **All 8 Tasks Working**: Bacen and IF systems operational
✅ **Message Processing Verified**: OpenSSL encryption ready

---

## Quick Command Reference

```batch
REM Service Management
net start BCSrvSqlMq
net stop BCSrvSqlMq
sc query BCSrvSqlMq

REM View Logs
tail -50 C:\BCSrvSqlMq\Traces\TRACE_SPB__*.log
findstr "8019" C:\BCSrvSqlMq\Traces\TRACE_SPB__*.log

REM Console Mode
cd build\Release
BCSrvSqlMq.exe -d

REM Rebuild
cd "%~dp0.."
cmake --build build --config Release
```

---

## See Also

- [X64_MIGRATION_SUCCESS.md](../X64_MIGRATION_SUCCESS.md) - Complete migration documentation
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Quick reference guide
- [DIAGNOSIS_SUMMARY.md](../DIAGNOSIS_SUMMARY.md) - Troubleshooting history

---

*Scripts Directory - BCSrvSqlMq x64*
*Last Cleanup: March 1, 2026*
