# IBM MQ 9.4.5.0 - Installation Complete ✓

**Date:** 2026-02-25
**Project:** BCSrvSqlMq

---

## Installation Summary

✅ **IBM MQ 9.4.5.0 Advanced for Developers** installed successfully!

| Component | Status | Location |
|-----------|--------|----------|
| **IBM MQ Server** | ✅ Installed | `C:\Program Files\IBM\MQ` |
| **Development Toolkit** | ✅ Installed | `C:\Program Files\IBM\MQ\tools` |
| **MQ Explorer** | ✅ Installed | `C:\Program Files\IBM\MQ\bin` |
| **Queue Manager** | ✅ Running | `QM.61377677.01` |
| **Local Queues** | ✅ Created (4) | QL.61377677.01.* |
| **Remote Queues** | ✅ Created (4) | QR.61377677.01.* |

---

## Version Information

```
Name:        IBM MQ
Version:     9.4.5.0
Level:       p945-L260121.DE
BuildType:   IKAP - (Production)
Platform:    IBM MQ for Windows (x64 platform)
Mode:        64-bit
InstName:    FinvestDTVM
InstPath:    C:\Program Files\IBM\MQ
DataPath:    C:\ProgramData\IBM\MQ
MaxCmdLevel: 945
LicenseType: Developer
ReleaseType: Continuous Delivery (CD)
```

---

## Key Files Located

### Headers (C/C++ Include Files)
- **Path:** `C:\Program Files\IBM\MQ\tools\c\include\`
- **Main Header:** `cmqc.h` (259 KB - official IBM MQ C API)
- **Other Headers:** `cmqcfc.h`, `cmqxc.h`, `cmqstrc.h`, etc.

### Library Files
- **Path:** `C:\Program Files\IBM\MQ\tools\lib\`
- **Server Library:** `mqm.lib` (for MQCONN/local bindings)
- **Client Library:** Available in `tools\lib64\` if needed

---

## Queue Manager: QM.61377677.01

### Status
```
QMNAME:  QM.61377677.01
STATUS:  Em execução (Running)
```

### Local Queues (4)

| Queue Name | Type | Description |
|------------|------|-------------|
| **QL.61377677.01.ENTRADA.BACEN** | QLOCAL | Entrada de mensagens do Bacen |
| **QL.61377677.01.SAIDA.BACEN** | QLOCAL | Saída de mensagens para o Bacen |
| **QL.61377677.01.ENTRADA.IF** | QLOCAL | Entrada de mensagens da IF |
| **QL.61377677.01.SAIDA.IF** | QLOCAL | Saída de mensagens para a IF |

**Properties:**
- `DEFPSIST(YES)` - Persistent messages
- `MAXDEPTH(5000)` - Maximum 5000 messages per queue

### Remote Queues (4)

| Queue Name | Type | Remote Name | Remote QM | Transmission Queue |
|------------|------|-------------|-----------|-------------------|
| **QR.61377677.01.ENTRADA.BACEN** | QREMOTE | BACEN.ENTRADA | QM.BACEN | QL.61377677.01.SAIDA.BACEN |
| **QR.61377677.01.SAIDA.BACEN** | QREMOTE | BACEN.SAIDA | QM.BACEN | QL.61377677.01.SAIDA.BACEN |
| **QR.61377677.01.ENTRADA.IF** | QREMOTE | IF.ENTRADA | QM.IF | QL.61377677.01.SAIDA.IF |
| **QR.61377677.01.SAIDA.IF** | QREMOTE | IF.SAIDA | QM.IF | QL.61377677.01.SAIDA.IF |

---

## CMakeLists.txt Updated

The build configuration has been updated with the correct IBM MQ paths:

```cmake
# IBM MQ 9.4.5.0 instalado em C:/Program Files/IBM/MQ
if(EXISTS "C:/Program Files/IBM/MQ/tools/c/include")
    include_directories("C:/Program Files/IBM/MQ/tools/c/include")
    link_directories("C:/Program Files/IBM/MQ/tools/lib")
    set(MQ_FOUND TRUE)
    message(STATUS "IBM MQ Found: C:/Program Files/IBM/MQ")
endif()

# Link MQ Server library
target_link_libraries(BCSrvSqlMq mqm.lib)
```

---

## Management Commands

### Queue Manager Commands
```bash
# Display Queue Managers
dspmq

# Start Queue Manager
strmqm QM.61377677.01

# Stop Queue Manager
endmqm QM.61377677.01

# Delete Queue Manager (if needed)
dltmqm QM.61377677.01
```

### Queue Commands (using runmqsc)
```bash
# Enter MQSC console
runmqsc QM.61377677.01

# Display all local queues
DISPLAY QLOCAL(*)

# Display all remote queues
DISPLAY QREMOTE(*)

# Display specific queue
DISPLAY QLOCAL(QL.61377677.01.ENTRADA.BACEN) ALL

# Check queue depth
DISPLAY QLOCAL(QL.61377677.01.ENTRADA.BACEN) CURDEPTH

# Clear queue
CLEAR QLOCAL(QL.61377677.01.ENTRADA.BACEN)

# Exit MQSC
END
```

### MQ Explorer (GUI)
Launch from Start Menu: **IBM MQ Explorer**
- Visual queue management
- Message browsing
- Queue Manager configuration

---

## Next Steps

1. **Obtain CL32.lib** (CryptLib)
   - Place in project root: `BCSrvSqlMq\CL32.lib`

2. **Rebuild Project**
   ```bash
   cd build
   cmake --build . --config Release
   ```

3. **Test MQ Connectivity**
   - Run BCSrvSqlMq.exe
   - Verify MQCONN to QM.61377677.01
   - Test MQPUT/MQGET operations

4. **Configure Service**
   - Install as Windows NT Service
   - Set startup type to Automatic
   - Configure BCSrvSqlMq.ini with queue names

---

## Files Created

- ✅ [setup_mq_queues.cmd](setup_mq_queues.cmd) - MQ setup script (can be re-run if needed)

---

## Troubleshooting

### Permission Denied (AMQ7077E)
- Run commands as Administrator
- Ensure user is in **mqm** Windows group

### Queue Manager Won't Start
```bash
# Check logs
C:\ProgramData\IBM\MQ\qmgrs\QM.61377677.01\errors\AMQERR01.LOG

# Reset Queue Manager (if needed - USE WITH CAUTION)
endmqm -i QM.61377677.01
strmqm QM.61377677.01
```

### MQ Library Not Found During Build
- Verify path in CMakeLists.txt line 76-77
- Ensure `mqm.lib` exists in `C:\Program Files\IBM\MQ\tools\lib\`

---

**Installation Status:** ✅ **COMPLETE**

**Ready for:** Build & Link with mqm.lib

**Pending:** CL32.lib (CryptLib)

---

*Generated on 2026-02-25*
