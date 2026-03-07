# BCSrvSqlMq - PostgreSQL Migration Guide

## Overview

This document outlines the migration from **Microsoft SQL Server** to **PostgreSQL** for the BCSrvSqlMq service.

---

## Configuration Changes

### ✅ Completed

1. **[BCSrvSqlMq.ini](BCSrvSqlMq.ini)** - Updated [DataBase] section:
   - Added `DBPort=5432` for PostgreSQL
   - Changed table names to lowercase (PostgreSQL convention)
   - Updated comments to reference PostgreSQL ODBC driver

2. **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** - Updated documentation:
   - PostgreSQL ODBC driver installation instructions
   - ODBC DSN configuration for PostgreSQL
   - Connection testing with `psql` and PowerShell
   - Updated pre-flight checklist

3. **[create_tables_postgresql.sql](create_tables_postgresql.sql)** - Created:
   - Table schemas for PostgreSQL
   - Indexes for performance
   - Triggers for auto-updating timestamps
   - Sample control data

---

## Key Differences: SQL Server vs PostgreSQL

### 1. ODBC Driver

| SQL Server | PostgreSQL |
|------------|------------|
| SQL Server Native Client | **PostgreSQL Unicode (psqlODBC)** |
| SQLSRV32.DLL | PSQLODBC35W.DLL (or newer) |
| Default Port: 1433 | **Default Port: 5432** |

**Installation:**
- Download: https://www.postgresql.org/ftp/odbc/versions/msi/
- Install: `psqlodbc_x86.msi` (32-bit for x86 executable)

### 2. Naming Conventions

| Aspect | SQL Server | PostgreSQL |
|--------|------------|------------|
| **Case Sensitivity** | Case-insensitive | **Lowercase by default** (unless quoted) |
| **Table Names** | `SPB_LOG_BACEN` | `spb_log_bacen` |
| **Column Names** | `MsgID`, `LogMessage` | `msg_id`, `log_message` |
| **Identifiers** | Can be mixed case | **Use lowercase or quote: `"MixedCase"`** |

### 3. Data Types

| SQL Server | PostgreSQL | Notes |
|------------|------------|-------|
| `INT IDENTITY(1,1)` | `SERIAL` or `GENERATED ALWAYS AS IDENTITY` | Auto-increment |
| `DATETIME` | `TIMESTAMP` | Date/time storage |
| `NVARCHAR(MAX)` | `TEXT` | Variable-length text |
| `NVARCHAR(n)` | `VARCHAR(n)` | UTF-8 by default |
| `BIT` | `BOOLEAN` | True/false values |
| `UNIQUEIDENTIFIER` | `UUID` | GUIDs |
| `IMAGE`, `VARBINARY(MAX)` | `BYTEA` | Binary data |

### 4. SQL Syntax Differences

#### Date/Time Functions
```sql
-- SQL Server
SELECT GETDATE()           -- Current timestamp
SELECT DATEADD(day, 1, GETDATE())
SELECT DATEDIFF(day, start, end)

-- PostgreSQL
SELECT CURRENT_TIMESTAMP   -- Current timestamp
SELECT CURRENT_TIMESTAMP + INTERVAL '1 day'
SELECT EXTRACT(DAY FROM end - start)
```

#### String Functions
```sql
-- SQL Server
SELECT LEN(column_name)
SELECT SUBSTRING(str, 1, 10)

-- PostgreSQL
SELECT LENGTH(column_name)
SELECT SUBSTRING(str, 1, 10)  -- Same, but also: SUBSTR(str, 1, 10)
```

#### TOP vs LIMIT
```sql
-- SQL Server
SELECT TOP 10 * FROM table_name

-- PostgreSQL
SELECT * FROM table_name LIMIT 10
```

#### ISNULL vs COALESCE
```sql
-- SQL Server
SELECT ISNULL(column_name, 'default')

-- PostgreSQL (COALESCE works in both)
SELECT COALESCE(column_name, 'default')
```

### 5. Auto-Update Timestamps

#### SQL Server
```sql
CREATE TABLE table_name (
    id INT IDENTITY(1,1),
    updated_at DATETIME DEFAULT GETDATE()
);

-- Trigger for auto-update
CREATE TRIGGER trg_update
ON table_name
AFTER UPDATE AS
BEGIN
    UPDATE table_name
    SET updated_at = GETDATE()
    WHERE id IN (SELECT id FROM INSERTED)
END
```

#### PostgreSQL
```sql
CREATE TABLE table_name (
    id SERIAL PRIMARY KEY,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger for auto-update
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update
    BEFORE UPDATE ON table_name
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();
```

---

## Application Code Considerations

### 1. ODBC Connection String

If the application builds connection strings programmatically:

```cpp
// SQL Server ODBC
"Driver={SQL Server};Server=localhost;Database=BCSPBSTR;UID=user;PWD=pass"

// PostgreSQL ODBC (32-bit)
"Driver={PostgreSQL Unicode};Server=localhost;Port=5432;Database=bcspbstr;UID=user;PWD=pass"

// Or use DSN
"DSN=BCSPBSTR;UID=user;PWD=pass"
```

### 2. SQL Query Review

**Search for and update:**
- `GETDATE()` → `CURRENT_TIMESTAMP`
- `TOP n` → `LIMIT n`
- `ISNULL()` → `COALESCE()`
- Table/column names (if case-sensitive)
- Date arithmetic
- String concatenation (`+` → `||`)

**Example code search:**
```bash
# Search for SQL Server-specific syntax in .cpp files
grep -r "GETDATE()" *.cpp
grep -r "TOP [0-9]" *.cpp
grep -r "ISNULL(" *.cpp
grep -r "DATEADD" *.cpp
```

### 3. Error Handling

PostgreSQL error codes differ from SQL Server:
- SQL Server: Error numbers (e.g., 2627 = unique constraint violation)
- PostgreSQL: SQLSTATE codes (e.g., '23505' = unique violation)

Update error handling code accordingly.

### 4. Transactions

Both support transactions, but syntax may differ slightly:

```sql
-- Both support
BEGIN TRANSACTION;  -- or BEGIN;
COMMIT;
ROLLBACK;

-- PostgreSQL also supports
BEGIN;
SAVEPOINT sp1;
ROLLBACK TO SAVEPOINT sp1;
COMMIT;
```

---

## Migration Steps

### Phase 1: Database Setup ✅
- [x] Install PostgreSQL server
- [x] Install PostgreSQL ODBC driver (32-bit)
- [x] Create database `bcspbstr`
- [x] Run [create_tables_postgresql.sql](create_tables_postgresql.sql)
- [x] Configure ODBC DSN
- [x] Test connection

### Phase 2: Configuration ✅
- [x] Update [BCSrvSqlMq.ini](BCSrvSqlMq.ini) with PostgreSQL settings
- [x] Update [CONFIG_GUIDE.md](CONFIG_GUIDE.md) documentation

### Phase 3: Code Review (Pending)
- [ ] Search C++ source code for SQL Server-specific syntax
- [ ] Review SQL queries in `.cpp` files
- [ ] Update date/time functions
- [ ] Update string functions
- [ ] Update TOP to LIMIT
- [ ] Check transaction handling
- [ ] Review error code handling

### Phase 4: Testing (Pending)
- [ ] Unit test database operations
- [ ] Integration test with PostgreSQL
- [ ] Test ODBC connectivity
- [ ] Test message processing (MQGET → DB → MQPUT)
- [ ] Verify logging functionality
- [ ] Load testing

### Phase 5: Data Migration (If Needed)
- [ ] Export data from SQL Server
- [ ] Transform data if necessary
- [ ] Import to PostgreSQL
- [ ] Verify data integrity

---

## Code Review Checklist

If the application contains embedded SQL, review these files:

```bash
# Find files with SQL queries
grep -r "SELECT\|INSERT\|UPDATE\|DELETE" *.cpp *.h
```

### Files to Check:
- Database connection/initialization code
- Message logging functions
- Queue processing functions
- Error handling routines
- Any files with SQL statements

### Common Patterns to Replace:

1. **Identity Columns**
   ```sql
   -- Old (SQL Server)
   INSERT INTO table (col1, col2) OUTPUT INSERTED.id VALUES ('a', 'b')

   -- New (PostgreSQL)
   INSERT INTO table (col1, col2) VALUES ('a', 'b') RETURNING id
   ```

2. **Schema Qualification**
   ```sql
   -- SQL Server (with schema)
   SELECT * FROM dbo.table_name

   -- PostgreSQL (default schema is 'public')
   SELECT * FROM table_name
   -- Or explicitly: SELECT * FROM public.table_name
   ```

3. **Variable Declaration (Stored Procedures)**
   ```sql
   -- SQL Server
   DECLARE @var INT

   -- PostgreSQL (in functions)
   DECLARE var INTEGER;
   ```

---

## PostgreSQL Advantages

1. **Open Source** - No licensing costs
2. **Cross-Platform** - Runs on Windows, Linux, macOS
3. **Standards Compliant** - Better SQL standard compliance
4. **Advanced Features**:
   - JSON/JSONB support (native JSON handling)
   - Full-text search
   - Array data types
   - Window functions
   - CTEs (Common Table Expressions)
5. **Active Development** - Regular updates and improvements
6. **Community Support** - Large, active community

---

## Tools & Resources

### PostgreSQL Tools
- **pgAdmin 4** - GUI administration tool (https://www.pgadmin.org/)
- **DBeaver** - Universal database tool (supports PostgreSQL)
- **psql** - Command-line interface (included with PostgreSQL)
- **pg_dump/pg_restore** - Backup/restore utilities

### Migration Tools
- **pgloader** - Migrate from SQL Server to PostgreSQL automatically
- **ora2pg** - Oracle/SQL Server to PostgreSQL migration
- **Full Convert** - Commercial migration tool

### Documentation
- PostgreSQL Official Docs: https://www.postgresql.org/docs/
- ODBC Driver Docs: https://odbc.postgresql.org/
- SQL Server to PostgreSQL: https://wiki.postgresql.org/wiki/Converting_from_other_Databases_to_PostgreSQL

---

## Troubleshooting

### Issue: "Driver not found"
**Solution:** Install 32-bit PostgreSQL ODBC driver, configure using `C:\Windows\SysWOW64\odbcad32.exe`

### Issue: "Connection refused"
**Solution:** Check PostgreSQL is running, port 5432 is open, `pg_hba.conf` allows connections

### Issue: "Table does not exist"
**Solution:** PostgreSQL uses lowercase by default. Use lowercase table names or quote identifiers.

### Issue: "Syntax error near TOP"
**Solution:** Replace `SELECT TOP n` with `SELECT ... LIMIT n`

### Issue: "Function GETDATE() does not exist"
**Solution:** Replace `GETDATE()` with `CURRENT_TIMESTAMP` or `NOW()`

---

## Next Steps

1. **Review source code** - Search for SQL Server-specific syntax
2. **Update queries** - Modify SQL statements for PostgreSQL compatibility
3. **Test locally** - Verify application works with PostgreSQL
4. **Performance tuning** - Create indexes, analyze queries
5. **Documentation** - Update any SQL Server references in docs

---

**Migration guide created:** 2026-02-26
**Status:** Configuration complete, code review pending
**Database:** PostgreSQL (replacing SQL Server)
