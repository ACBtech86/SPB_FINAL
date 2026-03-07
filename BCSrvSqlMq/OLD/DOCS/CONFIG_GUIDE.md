# BCSrvSqlMq - Configuration Guide

## Overview

This guide explains how to configure BCSrvSqlMq.ini for your environment.

---

## Configuration File: BCSrvSqlMq.ini

### 📋 Required Customizations

Before running the service, you **MUST** update these settings:

#### 1. [DataBase] Section - PostgreSQL Configuration

```ini
DBAliasName=BCSPBSTR        ; ← Change to your ODBC DSN name
DBServer=localhost          ; ← Change to your PostgreSQL server hostname/IP
DBName=bcspbstr            ; ← Change to your database name (lowercase recommended)
DBPort=5432                ; ← PostgreSQL default port (5432)
```

**How to create PostgreSQL ODBC DSN:**

**Prerequisites:**
1. Install **PostgreSQL ODBC Driver (psqlODBC)**
   - Download from: https://www.postgresql.org/ftp/odbc/versions/msi/
   - Install **32-bit version** (e.g., `psqlodbc_x86.msi`) for x86 executable
   - Recommended: psqlODBC 16.x or later (Unicode version)

**Configure ODBC DSN:**
1. Open **ODBC Data Source Administrator (32-bit)** (important: must be 32-bit for x86 executable)
   - Windows search: "ODBC Data Sources (32-bit)"
   - Or run: `C:\Windows\SysWOW64\odbcad32.exe`
2. Go to **System DSN** tab
3. Click **Add**
4. Select **PostgreSQL Unicode** or **PostgreSQL Unicode(x86)**
5. Configure:
   - **Data Source:** `BCSPBSTR` (or your chosen DSN name)
   - **Database:** `bcspbstr` (your database name)
   - **Server:** `localhost` (or your PostgreSQL server IP)
   - **Port:** `5432` (default PostgreSQL port)
   - **User Name:** Your PostgreSQL username (e.g., `postgres` or app user)
   - **Password:** Your PostgreSQL password
   - **SSL Mode:** `prefer` or `require` (if using SSL/TLS)
6. Click **Test** to verify connection
7. Click **Save**

#### 2. [MQSeries] Section

**Already configured for the Queue Manager created on 2026-02-25:**

```ini
QueueManager=QM.61377677.01    ; ✅ Configured
MQServer=localhost             ; ← Change if MQ is on another server
```

**Queues configured:**
- ✅ `QL.61377677.01.ENTRADA.BACEN`
- ✅ `QL.61377677.01.SAIDA.BACEN`
- ✅ `QL.61377677.01.ENTRADA.IF`
- ✅ `QL.61377677.01.SAIDA.IF`
- ✅ Remote queues: `QR.61377677.01.*`

#### 3. [E-Mail] Section

```ini
ServerEmail=smtp.yourserver.com           ; ← Your SMTP server
SenderEmail=bcsrvsqlmq@yourcompany.com   ; ← Sender email
DestEmail=admin@yourcompany.com          ; ← Alert recipient
```

#### 4. [Security] Section

```ini
SecurityEnable=N                          ; ← Set to 'S' to enable encryption
PrivateKeyFile=C:\BCSrvSqlMq\certificates\private.key
KeyPassword=changeme                      ; ← Change the password!
```

---

## 📁 Directory Structure

The service expects these directories (will be created automatically on first run):

```
C:\BCSrvSqlMq\
├── Traces\          - Trace/log files
├── AuditFiles\      - Audit trail files
└── certificates\    - Security certificates (if SecurityEnable=S)
```

---

## 🔧 Service Configuration

### Service Name
- **Default:** `BCSrvSqlMq`
- Change in `[Servico]` section: `ServiceName=BCSrvSqlMq`

### Monitor Port
- **Default:** `14499`
- Used for service monitoring/health checks
- Ensure this port is available (not used by other services)

### Trace Level
- **Current:** `Trace=D` (Debug - verbose logging)
- Options:
  - `D` = Debug (most verbose)
  - `I` = Info
  - `W` = Warning
  - `E` = Error (least verbose)

---

## 📊 Database Tables - PostgreSQL

The service expects these tables in your PostgreSQL database:

| Table Name (PostgreSQL) | Purpose |
|------------------------|---------|
| `spb_log_bacen` | Service activity log |
| `spb_bacen_to_local` | Messages from Bacen to local system |
| `spb_local_to_bacen` | Messages from local to Bacen |
| `spb_controle` | Control/status table |

**PostgreSQL Naming Conventions:**
- PostgreSQL uses **lowercase** table/column names by default (unless quoted with `"TableName"`)
- Configuration file updated to use lowercase table names
- If you need uppercase/mixed-case, use quoted identifiers in DDL and application code

**Note:** Table schemas must match the application's expectations. Check the old SPB database for reference schemas.

### Creating Tables in PostgreSQL

See [create_tables_postgresql.sql](create_tables_postgresql.sql) for table creation scripts (to be created based on original SQL Server schema).

---

## ✅ Pre-Flight Checklist

Before installing/starting the service:

- [ ] **PostgreSQL ODBC Driver** installed (32-bit psqlODBC)
- [ ] **ODBC DSN** configured (32-bit ODBC Administrator - use `odbcad32.exe` in SysWOW64)
- [ ] **PostgreSQL** server accessible (test with `psql` or `isql`)
- [ ] **Database** `bcspbstr` exists
- [ ] **Database tables** created with correct schemas (lowercase names)
- [ ] **IBM MQ Queue Manager** `QM.61377677.01` is running (`dspmq`)
- [ ] **All 8 queues** created and accessible
- [ ] **SMTP server** configured (if email alerts needed)
- [ ] **Directories** created: `C:\BCSrvSqlMq\Traces`, `C:\BCSrvSqlMq\AuditFiles`
- [ ] **Monitor port** 14499 is available
- [ ] **Service account** has permissions to:
  - Read/write to C:\BCSrvSqlMq directories
  - Connect to PostgreSQL (user/role with appropriate privileges)
  - Connect to IBM MQ
  - Send emails (if configured)

---

## 🧪 Testing Connectivity

### Test IBM MQ Connection

```cmd
# Check Queue Manager status
dspmq

# Should show:
# QMNAME(QM.61377677.01)  STATUS(Running)

# Test queue access
runmqsc QM.61377677.01
  DISPLAY QLOCAL(QL.61377677.01.ENTRADA.BACEN)
  END
```

### Test PostgreSQL Connection

```bash
# Using psql (PostgreSQL command-line client)
psql -h localhost -p 5432 -U postgres -d bcspbstr -c "SELECT version();"

# Test ODBC connection via PowerShell
$conn = New-Object System.Data.Odbc.OdbcConnection("DSN=BCSPBSTR")
$conn.Open()
$cmd = $conn.CreateCommand()
$cmd.CommandText = "SELECT version();"
$reader = $cmd.ExecuteReader()
while ($reader.Read()) { Write-Host $reader[0] }
$conn.Close()

# Or use isql (unixODBC/Windows ODBC test utility)
isql -v BCSPBSTR username password
```

---

## 🚀 Next Steps

After configuration:

1. **Test run** - Run `BCSrvSqlMq.exe` manually first to verify configuration
2. **Check logs** - Look in `C:\BCSrvSqlMq\Traces` for any errors
3. **Install service** - `BCSrvSqlMq.exe -install`
4. **Start service** - `net start BCSrvSqlMq`
5. **Monitor** - Check Windows Event Viewer and trace files

---

## 📞 Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| "Cannot connect to QM" | Verify Queue Manager is running: `dspmq` |
| "ODBC DSN not found" | Use 32-bit ODBC Administrator, not 64-bit |
| "Access denied to MQ" | Check Windows user permissions for MQ |
| "Cannot write to Traces" | Check directory permissions for service account |
| "Port 14499 in use" | Change `MonitorPort` in BCSrvSqlMq.ini |

---

**Configuration guide created:** 2026-02-26
**For:** BCSrvSqlMq with IBM MQ 9.4.5.0 and Queue Manager QM.61377677.01
