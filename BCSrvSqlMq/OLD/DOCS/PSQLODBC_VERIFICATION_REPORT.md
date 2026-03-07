# psqlODBC 32-bit Installation Verification Report

**Date:** 2026-02-26
**Project:** BCSrvSqlMq
**Architecture:** x86 (32-bit)

---

## ✅ Installation Status: VERIFIED AND WORKING

---

## 📦 Installed Components

### PostgreSQL ODBC Drivers (32-bit)

| Driver | Version | DLL Path | Size | Status |
|--------|---------|----------|------|--------|
| **PostgreSQL Unicode** | 16.00.0005 | `C:\Program Files (x86)\psqlODBC\1600\bin\psqlodbc35w.dll` | 568 KB | ✅ Installed |
| **PostgreSQL ANSI** | 16.00.0005 | `C:\Program Files (x86)\psqlODBC\1600\bin\psqlodbc30a.dll` | 556 KB | ✅ Installed |

### Supporting Libraries

```
✅ libpq.dll        290 KB  (PostgreSQL client library)
✅ libssl-3.dll     985 KB  (OpenSSL SSL/TLS support)
✅ libcrypto-3.dll  3.9 MB  (OpenSSL cryptography)
✅ vcruntime140.dll  89 KB  (Visual C++ 2015-2022 Runtime)
✅ msvcp140.dll     437 KB  (Visual C++ Standard Library)
```

---

## 🔍 Registry Configuration

### 32-bit ODBC Registry (WOW6432Node)

**PostgreSQL Unicode Driver:**
```
Registry Key: HKLM\SOFTWARE\WOW6432Node\ODBC\ODBCINST.INI\PostgreSQL Unicode
Driver:       C:\Program Files (x86)\psqlODBC\1600\bin\psqlodbc35w.dll
Setup:        C:\Program Files (x86)\psqlODBC\1600\bin\psqlodbc35w.dll
ODBC Version: 3.51
API Level:    1
SQL Level:    1
Status:       ✅ Registered
```

**PostgreSQL ANSI Driver:**
```
Registry Key: HKLM\SOFTWARE\WOW6432Node\ODBC\ODBCINST.INI\PostgreSQL ANSI
Driver:       C:\Program Files (x86)\psqlODBC\1600\bin\psqlodbc30a.dll
ODBC Version: 3.50
Status:       ✅ Registered
```

---

## 🧪 Connectivity Test Results

### Test Environment
- **PowerShell:** 32-bit (SysWOW64) ✅
- **Driver Used:** PostgreSQL Unicode
- **Target:** localhost:5432
- **Database:** postgres

### Test Results

| Test | Result | Details |
|------|--------|---------|
| Driver Loading | ✅ Pass | psqlodbc35w.dll loaded successfully |
| Server Connection | ✅ Pass | Connected to localhost:5432 |
| PostgreSQL Service | ✅ Pass | postgresql-x64-18 is running |
| Authentication | ⚠️ Password Required | Default password doesn't work |

### Connection Attempt Output

```
Connection String: DRIVER={PostgreSQL Unicode};SERVER=localhost;PORT=5432;DATABASE=postgres
Status: Connection reached server
Error: password authentication failed for user "postgres"
```

**Analysis:** The error message confirms that:
1. ✅ The ODBC driver is working correctly
2. ✅ PostgreSQL is accepting connections
3. ✅ The driver can communicate with the database
4. ℹ️ The correct password is needed for the 'postgres' user

---

## ✅ Compatibility Verification

### BCSrvSqlMq.exe Compatibility

| Component | Architecture | Compatible |
|-----------|--------------|------------|
| BCSrvSqlMq.exe | PE32 (x86) | ✅ |
| psqlodbc35w.dll | PE32 (x86) | ✅ |
| CL32.dll | PE32 (x86) | ✅ |
| pugixml.dll | PE32 (x86) | ✅ |

**All components are 32-bit and compatible.** ✅

---

## 🔧 Configuration for BCSrvSqlMq

### DSN-less ODBC Connection String

BCSrvSqlMq uses a **DSN-less connection** (no ODBC Data Source Name configuration required):

```ini
[DataBase]
; Connection parameters
DBServer=localhost              ; PostgreSQL server
DBPort=5432                     ; PostgreSQL port
DBName=bcspbstr                ; Database name
DBUserName=postgres            ; PostgreSQL username
DBPassword=YOUR_PASSWORD       ; ← UPDATE WITH ACTUAL PASSWORD
```

**Connection string format:**
```
DRIVER={PostgreSQL Unicode};
SERVER=localhost;
PORT=5432;
DATABASE=bcspbstr;
UID=postgres;
PWD=your_password;
```

---

## 🎯 Next Steps

### 1. ✅ **psqlODBC Installed** (Complete)
The 32-bit driver is installed and verified.

### 2. ⏳ **Get PostgreSQL Password** (Required)
You need the password for the 'postgres' user that was set during PostgreSQL installation.

**Options:**
- **Remember:** Try to recall the password from installation
- **Reset:** Use [reset_postgres_password.cmd](reset_postgres_password.cmd) to reset it

### 3. ⏳ **Create Database** (Pending)
```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -W -c "CREATE DATABASE bcspbstr;"
```

### 4. ⏳ **Create Tables** (Pending)
```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -W -d bcspbstr -f create_tables_postgresql.sql
```

### 5. ⏳ **Update BCSrvSqlMq.ini** (Pending)
Update the `DBPassword` field with the correct password.

### 6. ⏳ **Test BCSrvSqlMq** (Pending)
Run the executable to verify database connectivity.

---

## 📞 Troubleshooting

### Issue: "Driver not found" (64-bit vs 32-bit)

**Symptoms:**
- PowerShell 64-bit cannot find the driver
- Error: "Data source name not found"

**Solution:**
- BCSrvSqlMq.exe is **32-bit**, it will automatically use the 32-bit driver
- For manual testing, use **32-bit PowerShell**:
  ```
  C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe
  ```

### Issue: "Password authentication failed"

**Solution:**
1. Verify PostgreSQL password
2. Use [reset_postgres_password.cmd](reset_postgres_password.cmd) if forgotten
3. Update password in BCSrvSqlMq.ini

### Issue: "Connection refused"

**Solution:**
```powershell
# Check if PostgreSQL is running
Get-Service postgresql-x64-18

# Start if stopped
Start-Service postgresql-x64-18
```

---

## 📋 Verification Checklist

- [x] psqlODBC 32-bit driver installed
- [x] Driver registered in 32-bit ODBC registry
- [x] Driver DLL files present
- [x] Driver architecture matches BCSrvSqlMq.exe (x86)
- [x] PostgreSQL service running
- [x] ODBC driver can reach PostgreSQL server
- [ ] PostgreSQL password known/configured
- [ ] Database `bcspbstr` created
- [ ] Database tables created
- [ ] BCSrvSqlMq.ini configured with password
- [ ] BCSrvSqlMq.exe tested with database connection

---

## 🎉 Conclusion

**psqlODBC 32-bit is FULLY INSTALLED and WORKING CORRECTLY.**

The driver successfully connects to PostgreSQL, and all components are compatible with BCSrvSqlMq.exe (x86). The only remaining requirement is the PostgreSQL password to complete database setup.

---

**Verification performed:** 2026-02-26
**Next action:** Obtain PostgreSQL password and create database `bcspbstr`
