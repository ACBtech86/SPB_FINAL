# BCSrvSqlMq - Test Plan

## Overview

Test plan for the BCSrvSqlMq Windows NT Service — SPB financial message broker between Bacen and IF/Cidade.

---

## 1. Pre-Requisites

Before running any tests, ensure:

| Requirement | Expected State |
|-------------|----------------|
| `BCSrvSqlMq.exe` | Built (223 KB, PE32 x86) in `build\Release\` |
| IBM MQ 9.4.5.0 | Installed at `C:\Program Files\IBM\MQ` |
| Queue Manager | `QM.61377677.01` running (`dspmq` shows "Em execucao") |
| 8 Queues | 4 local (QL.*) + 4 remote (QR.*) created |
| CL32.dll | Copied to exe directory or System32 |
| pugixml.dll | Present in exe directory (auto-built) |
| SQL Server | ODBC DSN configured, database accessible |
| BCSrvSqlMq.ini | Configured with correct DB, MQ, and path settings |
| CryptLib keys | Private key file + Public key in ODBC keyset (if Security=S) |
| BCMsgSqlMq.dll | Logging DLL in system PATH or exe directory |

---

## 2. Test Categories

### Level 1: Infrastructure Tests (No business logic)
### Level 2: Component Tests (Individual subsystems)
### Level 3: Integration Tests (End-to-end message flow)
### Level 4: Stress & Error Recovery Tests

---

## 3. Level 1 — Infrastructure Tests

### T1.1 — Service Installation

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run `BCSrvSqlMq.exe -v` | Displays service version |
| 2 | Run `BCSrvSqlMq.exe -i` (as Admin) | Service registered in Windows SCM |
| 3 | Open `services.msc` | "BCSrvSqlMq" listed, Startup=Manual |
| 4 | Run `BCSrvSqlMq.exe -u` (as Admin) | Service removed from SCM |

### T1.2 — Service Debug Mode

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Configure `BCSrvSqlMq.ini` with valid settings | File saved |
| 2 | Run `BCSrvSqlMq.exe -d` (console/debug mode) | Service starts in console, shows initialization log |
| 3 | Press Ctrl+C | Service performs orderly shutdown |
| 4 | Check trace files in `DirTraces` | Trace log created with startup/shutdown entries |

### T1.3 — IBM MQ Connectivity

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run `dspmq` | Shows `QM.61377677.01 STATUS(Em execucao)` |
| 2 | Run `runmqsc QM.61377677.01` then `DISPLAY QLOCAL(QL.61377677.01.*)` | All 4 local queues displayed |
| 3 | Run `DISPLAY QREMOTE(QR.61377677.01.*)` | All 4 remote queues displayed |
| 4 | Put a test message: `amqsput QL.61377677.01.ENTRADA.BACEN QM.61377677.01` | Message accepted |
| 5 | Get the test message: `amqsget QL.61377677.01.ENTRADA.BACEN QM.61377677.01` | Message retrieved, matches input |

### T1.4 — SQL Server / ODBC Connectivity

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open ODBC Data Source Administrator (32-bit: `%windir%\SysWOW64\odbcad32.exe`) | DSN tool opens |
| 2 | Verify System DSN configured for the database | DSN listed and connection test passes |
| 3 | Start service in debug mode (-d) | Service auto-creates tables if missing |
| 4 | Check database | Tables `BACEN_TO_BCIDADE_APP`, `BCIDADE_TO_BACEN_APP`, `CONTROLE`, `BCIDADE_STR_LOG` exist with correct schema |

### T1.5 — TCP Monitor Port

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start service in debug mode | Service running |
| 2 | `netstat -an | findstr 14499` | Port 14499 LISTENING on 0.0.0.0 |
| 3 | `telnet localhost 14499` | Connection accepted |
| 4 | Stop service | Port 14499 no longer LISTENING |

---

## 4. Level 2 — Component Tests

### T2.1 — MQ Queue Operations (MQGET/MQPUT)

**Purpose:** Verify the service can read from and write to MQ queues.

| Test | Queue | Action | Expected Result |
|------|-------|--------|-----------------|
| T2.1.1 | QL.ENTRADA.BACEN | PUT test message via `amqsput`, start BacenREQ thread | Message consumed from queue (CURDEPTH returns to 0) |
| T2.1.2 | QL.SAIDA.BACEN | Start BacenRSP thread, PUT response message | Message consumed |
| T2.1.3 | QL.ENTRADA.IF | PUT test message | Message consumed by IFRSP thread |
| T2.1.4 | QL.SAIDA.IF | PUT test message | Message consumed by IFSup thread |
| T2.1.5 | Empty queue | Start service with empty queues | No errors, threads idle, MQRC_NO_MSG_AVAILABLE handled silently |
| T2.1.6 | Queue timeout | Set `QueueTimeout=5`, empty queue | Thread waits 5s, returns, re-polls |

**Verification:** `runmqsc QM.61377677.01` → `DISPLAY QLOCAL(QL.61377677.01.*) CURDEPTH`

### T2.2 — Database Record Operations

**Purpose:** Verify correct INSERT/UPDATE/SELECT on all 4 tables.

| Test | Table | Action | Expected Result |
|------|-------|--------|-----------------|
| T2.2.1 | BACEN_TO_BCIDADE_APP | BacenREQ processes a message | New row inserted with MQ_MSG_ID, XML in MSG field, FLAG_PROC set |
| T2.2.2 | BCIDADE_TO_BACEN_APP | Insert row with FLAG_PROC='N' via SQL | IFReq picks it up, updates FLAG_PROC='S', fills MQ_MSG_ID |
| T2.2.3 | CONTROLE | BacenREQ processes a message | CONTROLE row updated with DTHR_ULTMSG, ULTMSG, STATUS_GERAL |
| T2.2.4 | BCIDADE_STR_LOG | Any message processed | New log row inserted with full MQ_HEADER and SECURITY_HEADER |
| T2.2.5 | Auto-DDL | DROP table, restart service | Table recreated automatically with correct schema and indexes |

### T2.3 — Audit File Operations

**Purpose:** Verify binary audit file creation and rotation.

| Test | Action | Expected Result |
|------|--------|-----------------|
| T2.3.1 | Process first message of the day | New audit file created in `DirAudFile` with date suffix (YYYYMMDD) |
| T2.3.2 | Process multiple messages | Records appended to same audit file, each with STAUDITFILE header |
| T2.3.3 | Run across midnight (or mock date change) | New audit file created for new date, old file closed |
| T2.3.4 | Make `DirAudFile` read-only | Error logged, service continues operating (audit write fails gracefully) |

### T2.4 — Monitor (TCP Management Interface)

**Purpose:** Verify the TCP monitor accepts connections and dispatches commands.

| Test | Action | Expected Result |
|------|--------|-----------------|
| T2.4.1 | Connect to port 14499, send FUNC_NOP (0xFF) | Connection kept alive, timeout reset |
| T2.4.2 | Connect, send FUNC_POST (0x01) with valid queue name | Matching thread receives THREAD_EVENT_POST, processes queue |
| T2.4.3 | Connect, send malformed COMHDR (wrong length fields) | Connection rejected/closed, no crash |
| T2.4.4 | Open 50 simultaneous connections | All accepted (max capacity) |
| T2.4.5 | Open 51st connection | Connection refused or queued |
| T2.4.6 | Client disconnects mid-transfer | WSAECONNRESET handled, client removed from list |
| T2.4.7 | Client idle beyond timeout | Connection force-closed by CheckTimeout() |

---

## 5. Level 3 — Integration Tests (End-to-End)

### T3.1 — Bacen → Cidade (Inbound Message Flow)

**Purpose:** Full pipeline test for receiving a message from Bacen.

```
amqsput → QL.ENTRADA.BACEN → CBacenReq → DB (BACEN_TO_BCIDADE_APP) + AuditFile
```

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start service in debug mode (-d) | All 8 threads initialized |
| 2 | Prepare test MQ message with valid SECHDR + XML body | Message buffer ready |
| 3 | PUT message to `QL.61377677.01.ENTRADA.BACEN` via `amqsput` | Message placed in queue |
| 4 | Wait 5-10 seconds | CBacenReq thread picks up message |
| 5 | Check queue depth | CURDEPTH = 0 (message consumed) |
| 6 | Query `BACEN_TO_BCIDADE_APP` | New row with correct MQ_MSG_ID, NU_OPE, COD_MSG, MSG (XML) |
| 7 | Query `CONTROLE` | Institution row updated with timestamp |
| 8 | Query `BCIDADE_STR_LOG` | Log entry created |
| 9 | Check audit file | Binary record written with MQMD + SECHDR + XML |
| 10 | Check trace log | No errors, processing steps logged |

### T3.2 — Cidade → Bacen (Outbound Message Flow)

**Purpose:** Full pipeline test for sending a message to Bacen.

```
DB INSERT (FLAG_PROC='N') → Monitor FUNC_POST → CIFReq → MQPUT → QR.REQ.*
```

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start service in debug mode | All threads ready |
| 2 | INSERT into `BCIDADE_TO_BACEN_APP` with FLAG_PROC='N', valid XML in MSG | Row inserted |
| 3 | Send FUNC_POST to Monitor port 14499 for IFReq queue | Thread wakes up |
| 4 | Wait 5-10 seconds | CIFReq processes the record |
| 5 | Query `BCIDADE_TO_BACEN_APP` | FLAG_PROC changed to 'S', MQ_MSG_ID populated |
| 6 | Query `BCIDADE_STR_LOG` | Log entry created |
| 7 | Check MQ (if possible via remote QM) | Message delivered to remote queue |

### T3.3 — Round-Trip (Request → Response)

**Purpose:** Simulate complete SPB transaction cycle.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Send REQ message to QL.ENTRADA.BACEN | Received and stored in DB |
| 2 | Application processes and inserts RSP in BCIDADE_TO_BACEN_APP | RSP row with FLAG_PROC='N' |
| 3 | Trigger IFRsp via FUNC_POST | RSP message sent to QR.RSP.* |
| 4 | Verify RSP has correct MQ_CORREL_ID linking to original REQ | Correlation matches |

### T3.4 — Security Pipeline (if SecurityEnable=S)

**Purpose:** Verify encryption and digital signature end-to-end.

| Test | Action | Expected Result |
|------|--------|-----------------|
| T3.4.1 | Inbound message with Versao=0x01 (encrypted) | BacenREQ decrypts (3DES) + verifies signature (RSA) |
| T3.4.2 | Inbound message with wrong certificate serial | CodErro=0x10, message rejected |
| T3.4.3 | Inbound message with tampered signature | CodErro=0x05, signature verification fails |
| T3.4.4 | Outbound message with SecurityEnable=S | IFReq signs (RSA) + encrypts (3DES) before MQPUT |
| T3.4.5 | Private key file missing or wrong password | cryptStatusError logged, thread stops gracefully |
| T3.4.6 | Public key not found in ODBC keyset | Error logged, key load fails |

---

## 6. Level 4 — Stress & Error Recovery Tests

### T4.1 — High Volume

| Test | Action | Expected Result |
|------|--------|-----------------|
| T4.1.1 | PUT 1000 messages to QL.ENTRADA.BACEN in rapid succession | All messages consumed and stored in DB, no data loss |
| T4.1.2 | INSERT 1000 rows with FLAG_PROC='N' | All rows processed by IFReq, all FLAG_PROC='S' |
| T4.1.3 | PUT messages to all 4 local queues simultaneously | All 4 Bacen threads process concurrently |
| T4.1.4 | Sustained 10 msg/sec for 1 hour | No memory leak, no handle leak, stable performance |

### T4.2 — Queue Full

| Test | Action | Expected Result |
|------|--------|-----------------|
| T4.2.1 | Fill queue to MAXDEPTH (5000) | MQRC_Q_FULL (2053) returned on next PUT |
| T4.2.2 | IFReq tries to PUT to full remote queue | Error logged, thread does NOT stop, retries on next cycle |
| T4.2.3 | Drain some messages from full queue | IFReq resumes normal operation on next FUNC_POST |

### T4.3 — Database Failures

| Test | Action | Expected Result |
|------|--------|-----------------|
| T4.3.1 | Stop SQL Server while service is running | CDBException caught, thread signals STOP, orderly shutdown |
| T4.3.2 | Restart SQL Server | Service must be restarted (no auto-reconnect) |
| T4.3.3 | Lock a DB table with `BEGIN TRAN; SELECT * FROM ... WITH (TABLOCKX)` | Thread waits for lock, may timeout |
| T4.3.4 | INSERT duplicate primary key (same DB_DATETIME + MQ_MSG_ID) | CDBException caught, MQBACK rolls back MQ transaction |

### T4.4 — MQ Failures

| Test | Action | Expected Result |
|------|--------|-----------------|
| T4.4.1 | Stop Queue Manager: `endmqm QM.61377677.01` | MQCONN fails, threads signal STOP |
| T4.4.2 | Restart Queue Manager: `strmqm QM.61377677.01` | Service must be restarted |
| T4.4.3 | Delete a queue while service is running | MQOPEN fails, thread signals STOP |
| T4.4.4 | Put message larger than MaxLenMsg | MQRC_MSG_TOO_BIG_FOR_Q, error logged |

### T4.5 — Network Failures

| Test | Action | Expected Result |
|------|--------|-----------------|
| T4.5.1 | Disconnect TCP monitor client mid-transfer | WSAECONNRESET handled, client removed |
| T4.5.2 | Firewall port 14499 | No new monitor connections, service continues |
| T4.5.3 | Multiple connect/disconnect cycles on Monitor | No socket leaks, client list stays clean |

### T4.6 — Transaction Consistency (MQ + DB)

**Most critical test — ensures no message duplication or loss.**

| Test | Scenario | Expected Result |
|------|----------|-----------------|
| T4.6.1 | MQGET succeeds, DB INSERT fails | MQBACK called, message returns to queue for retry |
| T4.6.2 | MQGET succeeds, DB INSERT succeeds, MQCMIT fails | Message may be redelivered (at-least-once), DB entry exists |
| T4.6.3 | DB SELECT succeeds, MQPUT fails | No FLAG_PROC update, record stays 'N' for retry |
| T4.6.4 | DB SELECT succeeds, MQPUT succeeds, DB UPDATE fails | MQ committed but DB not updated — requires manual reconciliation |
| T4.6.5 | Kill service process (taskkill) mid-transaction | On restart: MQ rolls back uncommitted, DB rolls back uncommitted |

---

## 7. Service Lifecycle Tests

### T7.1 — Start/Stop/Pause/Continue

| Test | Action | Expected Result |
|------|--------|-----------------|
| T7.1.1 | `net start BCSrvSqlMq` | Service starts, all threads initialized |
| T7.1.2 | `net stop BCSrvSqlMq` | Service stops, all threads terminate, MQ disconnected, audit files closed |
| T7.1.3 | `sc pause BCSrvSqlMq` | Service enters PAUSED state, threads stop processing |
| T7.1.4 | `sc continue BCSrvSqlMq` | Service resumes, threads restart processing |
| T7.1.5 | Stop/Start 10 times rapidly | No resource leaks (handles, connections, memory) |

### T7.2 — Configuration Changes

| Test | Action | Expected Result |
|------|--------|-----------------|
| T7.2.1 | Change `SrvTrace=S`, restart | Detailed trace output in DirTraces |
| T7.2.2 | Change `SrvTrace=D`, restart | Debug-level trace with MQ header dumps |
| T7.2.3 | Change `MonitorPort`, restart | Monitor listens on new port |
| T7.2.4 | Invalid DB connection in .ini | Service fails to start, error in Event Log |
| T7.2.5 | Invalid Queue Manager name in .ini | MQCONN fails, error logged |

---

## 8. Test Message Templates

### Minimal Test Message (Security Disabled)

```
Security Header: 332 bytes, Versao=0x00 (clear), all zeros
XML Body:
<?xml version="1.0" encoding="ISO-8859-1"?>
<BCMSG>
  <ESSION>
    <NUOPE>SPB20260225000001234</NUOPE>
    <CODMSG>SPB001</CODMSG>
    <ISPB>61377677</ISPB>
  </ESSION>
  <DADOS>
    <VALOR>1000.00</VALOR>
    <TEXTO>Teste de mensagem</TEXTO>
  </DADOS>
</BCMSG>
```

### Test Message with Security (SecurityEnable=S)

```
Security Header (332 bytes):
  TamSecHeader = 332
  Versao = 0x01 (encrypted)
  AlgAssymKey = 0x01 (RSA-1024)
  AlgSymKey = 0x01 (3DES-168)
  AlgHash = 0x02 (SHA-1)
  CADest = 0x01 (Certsign)
  NumSerieCertDest = [certificate serial number]
  SymKeyCifr = [128 bytes RSA-encrypted 3DES key]
  HashCifrSign = [128 bytes RSA signature]

Body: 3DES-CBC encrypted XML (same structure as above)
```

---

## 9. Test Execution Checklist

### Quick Smoke Test (10 minutes)

- [ ] `dspmq` shows QM running
- [ ] `BCSrvSqlMq.exe -d` starts without errors
- [ ] Port 14499 is listening
- [ ] DB tables exist (auto-created)
- [ ] PUT test message to QL.ENTRADA.BACEN → consumed
- [ ] Row appears in BACEN_TO_BCIDADE_APP
- [ ] Ctrl+C stops service cleanly

### Full Regression (2-4 hours)

- [ ] All Level 1 tests (T1.1 — T1.5)
- [ ] All Level 2 tests (T2.1 — T2.4)
- [ ] All Level 3 tests (T3.1 — T3.4)
- [ ] Selected Level 4 tests (T4.6 transaction consistency is mandatory)
- [ ] All Level 7 tests (T7.1 — T7.2)

---

## 10. Tools Required

| Tool | Purpose | Location |
|------|---------|----------|
| `amqsput` / `amqsget` | MQ sample programs for PUT/GET | `C:\Program Files\IBM\MQ\tools\c\Samples\Bin\` |
| `runmqsc` | MQ admin console | `C:\Program Files\IBM\MQ\bin\` |
| `dspmq` | Queue Manager status | `C:\Program Files\IBM\MQ\bin\` |
| `odbcad32.exe` (32-bit) | ODBC DSN management | `%windir%\SysWOW64\` |
| SQL Server Management Studio | DB queries and monitoring | Installed separately |
| `telnet` or `ncat` | TCP Monitor testing | Windows Feature or nmap.org |
| `netstat` | Port verification | Built-in Windows |
| Process Explorer / Handle | Resource leak detection | Sysinternals |
| Event Viewer | Windows Event Log | Built-in Windows |

---

## 11. Known Limitations

1. **No auto-reconnect**: If MQ or DB goes down, the service must be restarted manually.
2. **32-bit only**: Built as Win32 x86 due to CL32.lib dependency.
3. **Single Queue Manager**: Hardcoded to `MQCONN()` (local bindings), cannot connect to remote QMs.
4. **No message retry**: Failed messages are rolled back to the queue but require thread restart.
5. **BCMsgSqlMq.dll required**: External logging DLL must be present for the service to start.

---

*Generated by Claude Code on 2026-02-25*
