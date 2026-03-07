# PostgreSQL Password Reset Guide

**Date:** 2026-02-26
**Project:** BCSrvSqlMq
**Purpose:** Reset postgres user password for database access

---

## 🎯 Quick Start

You have **3 options** to reset the PostgreSQL password:

---

## **Option 1: Easy Automated Script** ⭐ **RECOMMENDED**

This is the easiest and safest method.

### Steps:

1. **Right-click** [`reset_password_easy.bat`](reset_password_easy.bat)
2. Select **"Run as administrator"**
3. Press **Enter** to continue
4. When prompted, enter your **new password**
5. Done! ✅

**What it does:**
- Temporarily enables trust authentication
- Resets the password
- Restores secure authentication
- Restarts PostgreSQL automatically

**Safe and automatic!** ✅

---

## **Option 2: Using pgAdmin 4** (GUI Method)

If you prefer a graphical interface:

### Steps:

1. **Double-click** [`open_pgadmin.bat`](open_pgadmin.bat) to launch pgAdmin 4

2. When pgAdmin opens, you'll be asked for a **master password**
   - This is pgAdmin's own password (set during first launch)
   - If first time: create a master password

3. In the left panel, right-click **Servers** → **Register** → **Server**

4. Configure the connection:
   - **General Tab:**
     - Name: `Local PostgreSQL 18`
   - **Connection Tab:**
     - Host: `localhost`
     - Port: `5432`
     - Database: `postgres`
     - Username: `postgres`
     - Password: `<leave empty for now>`
     - Save password: ✅ Check

5. Click **Save** (it will fail - that's OK!)

6. To reset password, you need to **temporarily enable trust authentication**:
   - Use **Option 1** (automated script) instead, or
   - Follow **Option 3** (manual method) below

---

## **Option 3: Manual Command Line** (Advanced)

For advanced users who want full control:

### Step 1: Backup Configuration

```cmd
copy "C:\Program Files\PostgreSQL\18\data\pg_hba.conf" "C:\Program Files\PostgreSQL\18\data\pg_hba.conf.backup"
```

### Step 2: Edit pg_hba.conf

Open in Notepad as Administrator:
```cmd
notepad "C:\Program Files\PostgreSQL\18\data\pg_hba.conf"
```

Find these lines:
```
host    all    all    127.0.0.1/32    scram-sha-256
host    all    all    ::1/128         scram-sha-256
```

Change `scram-sha-256` to `trust`:
```
host    all    all    127.0.0.1/32    trust
host    all    all    ::1/128         trust
```

Save and close.

### Step 3: Restart PostgreSQL

```powershell
Restart-Service postgresql-x64-18
```

### Step 4: Reset Password

```cmd
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "ALTER USER postgres WITH PASSWORD 'your_new_password';"
```

### Step 5: Restore Secure Authentication

```cmd
copy "C:\Program Files\PostgreSQL\18\data\pg_hba.conf.backup" "C:\Program Files\PostgreSQL\18\data\pg_hba.conf"
```

### Step 6: Restart PostgreSQL Again

```powershell
Restart-Service postgresql-x64-18
```

---

## 🧪 Test Your New Password

After resetting, test the password:

### Method A: Using test script
```cmd
test_password.bat
```

### Method B: Using psql directly
```cmd
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -W -c "SELECT version();"
```

Enter your password when prompted. If it connects, you're good! ✅

### Method C: Using ODBC test script (32-bit PowerShell)
```cmd
C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy Bypass -File test_odbc.ps1
```

Edit `test_odbc.ps1` first and replace the password in the connection string.

---

## 📝 Update BCSrvSqlMq.ini

After successfully resetting the password, update the configuration:

1. Open [`BCSrvSqlMq.ini`](BCSrvSqlMq.ini)

2. Find the `[DataBase]` section

3. Update the password:
   ```ini
   [DataBase]
   DBServer=localhost
   DBPort=5432
   DBName=bcspbstr
   DBUserName=postgres
   DBPassword=your_new_password    ; ← UPDATE THIS
   ```

4. Save the file

---

## ✅ Verification Checklist

After password reset:

- [ ] Password reset completed successfully
- [ ] Tested connection with psql (`test_password.bat`)
- [ ] Tested ODBC connection (`test_odbc.ps1`)
- [ ] Updated `BCSrvSqlMq.ini` with new password
- [ ] Created database `bcspbstr`
- [ ] Created tables (run `create_tables_postgresql.sql`)
- [ ] Tested BCSrvSqlMq.exe

---

## 🔒 Security Notes

### Password Requirements

- **Minimum length:** 8 characters (recommended: 12+)
- **Complexity:** Use mix of letters, numbers, and symbols
- **Avoid:** Common words, personal information, simple patterns

### Example Strong Passwords
```
BcSrv$ql2026!Pg    (Good - 15 chars, mixed case, symbols)
P0stgr3$@2026      (Good - 13 chars, mixed case, symbols)
postgres           (Bad - too common)
12345678           (Bad - too simple)
```

### Important
- **Don't share** the password
- **Don't commit** BCSrvSqlMq.ini to source control with the password
- **Use environment variables** in production (optional enhancement)

---

## 🆘 Troubleshooting

### Issue: "Access denied" when running script

**Solution:** Right-click the .bat file and select **"Run as administrator"**

### Issue: "PostgreSQL service won't start"

**Solution:**
```powershell
# Check service status
Get-Service postgresql-x64-18

# Try to start manually
Start-Service postgresql-x64-18

# Check Windows Event Viewer if it fails
eventvwr.msc
# Navigate to: Windows Logs → Application
```

### Issue: "psql command not found"

**Solution:** The full path is:
```
"C:\Program Files\PostgreSQL\18\bin\psql.exe"
```

### Issue: Still can't connect after password reset

**Solution:**
1. Verify PostgreSQL is running:
   ```powershell
   Get-Service postgresql-x64-18
   ```

2. Check pg_hba.conf was restored:
   ```cmd
   notepad "C:\Program Files\PostgreSQL\18\data\pg_hba.conf"
   ```
   Should show `scram-sha-256`, not `trust`

3. Try restarting PostgreSQL:
   ```powershell
   Restart-Service postgresql-x64-18
   ```

---

## 📞 Support Files

Helper scripts created for you:

| File | Purpose |
|------|---------|
| [`reset_password_easy.bat`](reset_password_easy.bat) | ⭐ Automated password reset (recommended) |
| [`test_password.bat`](test_password.bat) | Test if password works |
| [`test_odbc.ps1`](test_odbc.ps1) | Test ODBC connectivity |
| [`open_pgadmin.bat`](open_pgadmin.bat) | Launch pgAdmin 4 |
| [`PASSWORD_RESET_GUIDE.md`](PASSWORD_RESET_GUIDE.md) | This guide |

---

## ⏭️ Next Steps After Password Reset

1. ✅ **Password reset** (you are here)
2. ⏳ **Create database** `bcspbstr`
   ```cmd
   "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -W -c "CREATE DATABASE bcspbstr;"
   ```

3. ⏳ **Create tables**
   ```cmd
   "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -W -d bcspbstr -f create_tables_postgresql.sql
   ```

4. ⏳ **Update BCSrvSqlMq.ini** with password

5. ⏳ **Test BCSrvSqlMq.exe**
   ```cmd
   cd build\Release
   BCSrvSqlMq.exe
   ```

---

**Guide created:** 2026-02-26
**For:** BCSrvSqlMq PostgreSQL setup
