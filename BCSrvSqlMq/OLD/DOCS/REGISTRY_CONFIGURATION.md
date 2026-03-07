# BCSrvSqlMq - Registry Configuration Guide

**Date:** 2026-02-26
**Status:** Solution for IBM MQ Error 2043

---

## 🎯 Problem Identified

The service was installed and running, but all IBM MQ queues were failing with:
```
8019 E RmtReq MQOPEN ended with reason code 2043
```

**Error 2043 = MQRC_OBJECT_NOT_FOUND** - Queue Manager or queue names not found.

---

## 🔍 Root Cause

BCSrvSqlMq has **two different configuration modes**:

### 1. Debug/Console Mode (`BCSrvSqlMq.exe -d`)
- ✅ Reads configuration from **BCSrvSqlMq.ini** file
- ✅ Works directly with INI file settings
- ⚠️ Not suitable for production (no auto-start, no service recovery)

### 2. Windows Service Mode (`BCSrvSqlMq.exe -i`)
- ❌ Does **NOT** read from BCSrvSqlMq.ini (except ServiceName)
- ✅ Reads all configuration from **Windows Registry**
- ✅ Production-ready (auto-start, service management, recovery)

**The Issue:**
When you install the service, the registry is **empty** by default. The service starts but can't find MQ configuration, causing error 2043.

---

## 📂 Registry Structure

The service reads configuration from:
```
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\BCSrvSqlMq\Parameters\
```

Under this path, it expects these sections:

### **DataBase Section**
```
HKLM:\...\Parameters\DataBase\
├── DBAliasName      = BCSPBSTR
├── DBServer         = localhost
├── DBName           = bcspbstr
├── DBPort           = 5432
├── DBUserName       = postgres
├── DBPassword       = Rama1248
├── DbTbControle     = spb_controle
├── DbTbStrLog       = spb_log_bacen
├── DbTbBacenCidadeApp = spb_bacen_to_local
└── DbTbCidadeBacenApp = spb_local_to_bacen
```

### **MQSeries Section** (Critical for Error 2043)
```
HKLM:\...\Parameters\MQSeries\
├── MQServer              = localhost
├── QueueManager          = QM.61377677.01
├── QueueTimeout          = 60000
├── QLBacenCidadeReq      = QL.61377677.01.ENTRADA.BACEN
├── QLBacenCidadeRsp      = QL.61377677.01.SAIDA.BACEN
├── QLBacenCidadeRep      = QL.61377677.01.REPORT.BACEN
├── QLBacenCidadeSup      = QL.61377677.01.SUPORTE.BACEN
├── QRCidadeBacenReq      = QR.61377677.01.ENTRADA.IF
├── QRCidadeBacenRsp      = QR.61377677.01.SAIDA.IF
├── QRCidadeBacenRep      = QR.61377677.01.REPORT.IF
└── QRCidadeBacenSup      = QR.61377677.01.SUPORTE.IF
```

### **Diretorios Section**
```
HKLM:\...\Parameters\Diretorios\
├── DirTraces     = C:\BCSrvSqlMq\Traces
└── DirAudFile    = C:\BCSrvSqlMq\Auditorias
```

### **Servico Section**
```
HKLM:\...\Parameters\Servico\
├── MonitorPort   = 14499
├── Trace         = S
├── SrvTimeout    = 300000
└── MaxLenMsg     = 8192
```

### **E-Mail Section** (Optional)
```
HKLM:\...\Parameters\E-Mail\
├── ServerEmail   = (empty)
├── SenderEmail   = (empty)
├── SenderName    = (empty)
├── DestEmail     = (empty)
└── DestName      = (empty)
```

### **Security Section**
```
HKLM:\...\Parameters\Security\
├── UnicodeEnable      = S
├── SecurityEnable     = N
├── SecurityDB         = (empty)
├── PrivateKeyFile     = (empty)
├── PublicKeyLabel     = (empty)
├── PrivateKeyLabel    = (empty)
└── KeyPassword        = (empty)
```

---

## 🛠️ Solution

We created two scripts to automatically configure the registry:

### **Script 1: configure_registry.ps1** (PowerShell)
- Reads configuration from BCSrvSqlMq.ini
- Creates all registry sections and keys
- Writes configuration values to registry
- Optionally restarts the service

### **Script 2: configure_registry.bat** (Batch wrapper)
- Checks for Administrator privileges
- Runs the PowerShell script
- Easier to use (just right-click and "Run as administrator")

---

## 🚀 How to Use

### **Method 1: Batch File (Easiest)**

1. Navigate to `build\Release` directory
2. **Right-click** on `configure_registry.bat`
3. Select **"Run as administrator"**
4. Press Enter to confirm
5. Choose "Y" when asked to restart the service
6. Check logs for successful MQ connection

### **Method 2: PowerShell Script**

```powershell
# Open PowerShell as Administrator
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release"

# Run script
powershell.exe -ExecutionPolicy Bypass -File .\configure_registry.ps1
```

### **Method 3: Manual Registry Configuration**

If you prefer manual configuration:

1. Open **Registry Editor** (`regedit.exe`) as Administrator
2. Navigate to: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\BCSrvSqlMq\Parameters`
3. Create sections (keys): DataBase, MQSeries, Diretorios, Servico, E-Mail, Security
4. Under each section, create String values (REG_SZ) for each configuration item
5. Set values according to BCSrvSqlMq.ini
6. Restart the service: `net stop BCSrvSqlMq && net start BCSrvSqlMq`

---

## ✅ Verification

After running the configuration script:

### **1. Check Registry (Optional)**
```powershell
# View registry configuration
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\BCSrvSqlMq\Parameters\MQSeries"
```

### **2. Check Service Status**
```cmd
sc query BCSrvSqlMq
# Should show: STATE: RUNNING
```

### **3. Check Logs**
```cmd
# View latest log file
type C:\BCSrvSqlMq\Traces\TRACE_SPB_*.log | findstr /i "mqopen"
```

Look for:
- ✅ **Success:** No error 2043 messages
- ✅ **Success:** "Task [name] Iniciada" for all 8 threads
- ❌ **Still failing:** "MQOPEN ended with reason code 2043"

### **4. Verify MQ Queues**
```cmd
# List all queues
runmqsc QM.61377677.01
  DISPLAY QLOCAL(*)
  END
```

Ensure these queues exist:
- QL.61377677.01.ENTRADA.BACEN
- QL.61377677.01.SAIDA.BACEN
- QL.61377677.01.REPORT.BACEN
- QL.61377677.01.SUPORTE.BACEN
- QR.61377677.01.ENTRADA.IF
- QR.61377677.01.SAIDA.IF
- QR.61377677.01.REPORT.IF
- QR.61377677.01.SUPORTE.IF

---

## 🔄 When to Reconfigure

You need to run `configure_registry.bat` again when:

✅ After installing the service for the first time
✅ After changing any setting in BCSrvSqlMq.ini
✅ After reinstalling the service
✅ When moving to a different Queue Manager
✅ When changing database connection details
✅ If you get MQ error 2043 after service restart

---

## 📝 Code References

The registry configuration logic is implemented in:

### **[InitSrv.h](InitSrv.h)** (Lines 14-72)
Defines all registry key constants:
```cpp
const char SES_MQSERIES[] = "MQSeries";
const char KEY_MQQUEUEMGR[] = "QueueManager";
const char KEY_MQQLBACENCIDADEREQ[] = "QLBacenCidadeReq";
// ... etc
```

### **[InitSrv.cpp](InitSrv.cpp)** (Lines 368-1019)
Implements registry read/write functions:
- `GetKeyRegistryValue()` - Reads string values from registry
- `SetKeyRegistryValue()` - Writes string values to registry
- `GetKeyAll()` - Reads all configuration from registry during service startup

### **[ntservapp.cpp](ntservapp.cpp)** (Lines 12-30)
Entry point that reads ServiceName from INI:
```cpp
GetPrivateProfileString("Servico", "ServiceName", "BCSrvSqlMQ", m_ServiceName, MAX_PATH, m_ARQINI);
```

---

## 🎯 Summary

| Mode | Configuration Source | Use Case |
|------|---------------------|----------|
| **Debug Mode** (`-d`) | BCSrvSqlMq.ini | Testing, development |
| **Service Mode** (`-i`) | Windows Registry | Production, auto-start |

**Key Takeaway:**
After installing the service, **always run `configure_registry.bat`** to populate the Windows Registry with your configuration from BCSrvSqlMq.ini.

---

## 📞 Troubleshooting

### Script fails with "Access Denied"
- **Fix:** Right-click and select "Run as administrator"
- **Or:** Open CMD/PowerShell as Administrator first

### Script runs but error 2043 persists
- **Check:** MQ Queue Manager is running (`dspmq`)
- **Check:** Queues exist (`runmqsc QM.61377677.01` → `DISPLAY QLOCAL(*)`)
- **Check:** Queue names match exactly (case-sensitive)
- **Check:** Service was restarted after registry update

### Registry keys not created
- **Check:** Script completed without errors
- **Verify:** Check registry manually with `regedit.exe`
- **Fix:** Run script again as Administrator

---

**Last Updated:** 2026-02-26
**Scripts Created:**
- `build\Release\configure_registry.ps1`
- `build\Release\configure_registry.bat`

**Next Step:**
Run `configure_registry.bat` as Administrator and verify the service connects to IBM MQ successfully!
