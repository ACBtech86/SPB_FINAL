# PostgreSQL Setup Guide for BCSrvSqlMq

## Current Status

✅ **PostgreSQL 18.1** - Installed and running
✅ **PostgreSQL Service** - `postgresql-x64-18` is running
⏳ **psqlODBC 32-bit** - Installer downloaded, waiting for installation
⏳ **Database `bcspbstr`** - Needs to be created
⏳ **Database Tables** - Need to be created

---

## Step 1: Install psqlODBC 32-bit Driver ⏳

**Why 32-bit?** BCSrvSqlMq.exe is a 32-bit (x86) executable and MUST use the 32-bit ODBC driver.

### Installation Location
The installer is here: `C:\Users\AntonioBosco\Downloads\psqlodbc_x86.msi`

### Installation Methods

**Option A: Double-click installation (Recommended)**
1. Open File Explorer
2. Navigate to: `C:\Users\AntonioBosco\Downloads\`
3. Double-click `psqlodbc_x86.msi`
4. Click **Next** → **Install** → **Finish**

**Option B: Command line (Administrator required)**
```cmd
cd %USERPROFILE%\Downloads
msiexec /i psqlodbc_x86.msi /qb
```

### Verification
After installation, verify the 32-bit driver is registered:

```cmd
REM Open 32-bit ODBC Administrator
C:\Windows\SysWOW64\odbcad32.exe
```

You should see **PostgreSQL Unicode** in the Drivers tab.

---

## Step 2: Create PostgreSQL Database

### Using pgAdmin (GUI Method)

1. Open **pgAdmin 4** (Start Menu → PostgreSQL 18 → pgAdmin 4)
2. Connect to PostgreSQL (default user: `postgres`)
3. Right-click **Databases** → **Create** → **Database**
4. Enter:
   - **Database name:** `bcspbstr`
   - **Owner:** `postgres`
5. Click **Save**

### Using Command Line (psql)

```bash
# Connect to PostgreSQL
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres

# Create database
CREATE DATABASE bcspbstr;

# Connect to the new database
\c bcspbstr

# Verify
\l
```

**Note:** You'll be prompted for the `postgres` user password (set during PostgreSQL installation).

---

## Step 3: Create Database Tables

### Using psql

```bash
# Connect to the database
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d bcspbstr

# Run the schema file
\i 'C:/Users/AntonioBosco/OneDrive - Finvest/Área de Trabalho/BCSrvSqlMq/create_tables_postgresql.sql'

# Verify tables
\dt

# Exit
\q
```

### Using pgAdmin

1. In pgAdmin, select database `bcspbstr`
2. Click **Tools** → **Query Tool**
3. Open file: `create_tables_postgresql.sql`
4. Click **Execute** (F5)
5. Verify in **Schemas** → **public** → **Tables**

### Expected Tables

After running the script, you should have 4 tables:
- `spb_log_bacen` - Service activity log
- `spb_bacen_to_local` - Messages from Bacen to local (inbound)
- `spb_local_to_bacen` - Messages from local to Bacen (outbound)
- `spb_controle` - Control/configuration table

---

## Step 4: Configure BCSrvSqlMq.ini

Update the `[DataBase]` section in [BCSrvSqlMq.ini](BCSrvSqlMq.ini):

```ini
[DataBase]
; DSN-less ODBC Connection - No DSN configuration required!
DBAliasName=bcspbstr          ; ← Database name (NOT an ODBC DSN)
DBServer=localhost            ; ← PostgreSQL server
DBName=bcspbstr              ; ← Database name
DBPort=5432                  ; ← PostgreSQL port
; Database credentials - IMPORTANT: Update with your PostgreSQL credentials
DBUserName=postgres          ; ← PostgreSQL username
DBPassword=YOUR_PASSWORD     ; ← Replace with your postgres password
```

**IMPORTANT:** Replace `YOUR_PASSWORD` with the actual `postgres` user password.

---

## Step 5: Test the Connection

### Manual ODBC Test (optional, for verification)

```powershell
# Test DSN-less connection string
$connString = "DRIVER={PostgreSQL Unicode};SERVER=localhost;PORT=5432;DATABASE=bcspbstr;UID=postgres;PWD=YOUR_PASSWORD;"
$conn = New-Object System.Data.Odbc.OdbcConnection($connString)
$conn.Open()
Write-Host "Connection successful!"
$cmd = $conn.CreateCommand()
$cmd.CommandText = "SELECT version();"
$reader = $cmd.ExecuteReader()
while ($reader.Read()) { Write-Host $reader[0] }
$conn.Close()
```

### Test with BCSrvSqlMq

```cmd
# Run executable
cd "C:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\BCSrvSqlMq\build\Release"
BCSrvSqlMq.exe

# Check logs in
C:\BCSrvSqlMq\Traces\
```

---

## Troubleshooting

### Issue: "ODBC driver not found"
**Solution:** Ensure you installed the **32-bit** psqlODBC driver, not the 64-bit version.
- Verify in 32-bit ODBC Administrator: `C:\Windows\SysWOW64\odbcad32.exe`

### Issue: "Database does not exist"
**Solution:** Create the `bcspbstr` database (see Step 2)

### Issue: "Authentication failed"
**Solution:** Check the password in BCSrvSqlMq.ini matches your `postgres` user password

### Issue: "Connection timeout"
**Solution:**
- Verify PostgreSQL service is running: `Get-Service postgresql-x64-18`
- Check pg_hba.conf allows local connections
- Ensure port 5432 is not blocked by firewall

---

## Connection String Format

The service uses DSN-less ODBC connection strings (no ODBC DSN configuration needed):

```
DRIVER={PostgreSQL Unicode};
SERVER=localhost;
PORT=5432;
DATABASE=bcspbstr;
UID=postgres;
PWD=your_password;
```

This string is built automatically by the service from BCSrvSqlMq.ini parameters.

---

## Quick Reference

### PostgreSQL Service Management

```powershell
# Check status
Get-Service postgresql-x64-18

# Start service
Start-Service postgresql-x64-18

# Stop service
Stop-Service postgresql-x64-18

# Restart service
Restart-Service postgresql-x64-18
```

### PostgreSQL Tools Locations

- **PostgreSQL Server:** `C:\Program Files\PostgreSQL\18\`
- **psql (Command Line):** `C:\Program Files\PostgreSQL\18\bin\psql.exe`
- **pgAdmin 4 (GUI):** Start Menu → PostgreSQL 18 → pgAdmin 4
- **Configuration:** `C:\Program Files\PostgreSQL\18\data\postgresql.conf`
- **Client Authentication:** `C:\Program Files\PostgreSQL\18\data\pg_hba.conf`

### ODBC Tools

- **32-bit ODBC Administrator:** `C:\Windows\SysWOW64\odbcad32.exe` ← Use this for BCSrvSqlMq
- **64-bit ODBC Administrator:** `C:\Windows\System32\odbcad32.exe`

---

## Next Steps

After completing all steps above:

1. ✅ Install psqlODBC 32-bit driver
2. ✅ Create database `bcspbstr`
3. ✅ Run `create_tables_postgresql.sql` to create tables
4. ✅ Update `BCSrvSqlMq.ini` with correct password
5. ✅ Test the service executable
6. ✅ Install as Windows Service (see [CONFIG_GUIDE.md](CONFIG_GUIDE.md))

---

**Setup guide created:** 2026-02-26
**BCSrvSqlMq Version:** With DSN-less ODBC support
**PostgreSQL Version:** 18.1
**Target Architecture:** Win32 (x86 / 32-bit)
