# BCSrvSqlMq - PostgreSQL Code Review Report

**Date:** 2026-02-26
**Reviewed:** C++ source files for SQL Server-specific syntax
**Status:** ⚠️ **SQL Server-specific DDL found in 4 files** - Changes required

---

## Executive Summary

The application uses **MFC ODBC classes** (CRecordset, CDatabase) which abstract most database operations. This is good for portability. However, **DDL statements** (CREATE TABLE, ALTER TABLE, CREATE INDEX) contain **SQL Server-specific syntax** that must be updated for PostgreSQL compatibility.

### Impact Level: **MEDIUM**
- ✅ **No SQL Server functions** found (GETDATE, DATEADD, etc.)
- ✅ **No SELECT TOP** statements found
- ✅ **No ISNULL** functions found
- ⚠️ **SQL Server DDL syntax** found in 4 Recordset classes
- ✅ **CRUD operations** use MFC abstraction (portable)

---

## Files Requiring Changes

### 1. **STRLogRS.cpp** - Service Log Table DDL
**Lines:** 57-94
**Issue:** SQL Server-specific CREATE TABLE and ALTER TABLE syntax

### 2. **BacenAppRS.cpp** - Bacen Application Table DDL
**Lines:** 60-106
**Issue:** SQL Server-specific CREATE TABLE and ALTER TABLE syntax

### 3. **IFAppRS.cpp** - IF Application Table DDL
**Lines:** 81-143
**Issue:** SQL Server-specific CREATE TABLE and ALTER TABLE syntax

### 4. **ControleRS.cpp** - Control Table DDL
**Lines:** 74-101
**Issue:** SQL Server-specific CREATE TABLE and ALTER TABLE syntax

---

## SQL Server-Specific Syntax Found

### 1. **Data Type Syntax** ⚠️

#### SQL Server (current):
```cpp
m_sCreate += " MQ_MSG_ID [binary](24) NOT NULL,  ";
m_sCreate += " DB_DATETIME [datetime] NOT NULL, ";
m_sCreate += " STATUS_MSG [char] NOT NULL,      ";
m_sCreate += " MSG [text] NULL                  ";
```

#### PostgreSQL (required):
```cpp
m_sCreate += " MQ_MSG_ID BYTEA NOT NULL,        ";  // binary → BYTEA
m_sCreate += " DB_DATETIME TIMESTAMP NOT NULL,  ";  // datetime → TIMESTAMP
m_sCreate += " STATUS_MSG CHAR(1) NOT NULL,     ";  // remove brackets
m_sCreate += " MSG TEXT NULL                    ";  // remove brackets
```

**Changes needed:**
- `[binary](n)` → `BYTEA` (PostgreSQL binary type)
- `[datetime]` → `TIMESTAMP`
- `[char]` → `CHAR(n)` (specify length or use TEXT)
- `[text]` → `TEXT`
- Remove all `[brackets]` around data types

### 2. **Primary Key Constraints** ⚠️

#### SQL Server (current):
```cpp
m_sPriKey = " ALTER TABLE ";
m_sPriKey += GetDefaultSQL();
m_sPriKey += " WITH NOCHECK ADD ";              // ❌ SQL Server specific
m_sPriKey += " CONSTRAINT [PK_";
m_sPriKey += GetDefaultSQL();
m_sPriKey += "] PRIMARY KEY CLUSTERED ";        // ❌ CLUSTERED is SQL Server
m_sPriKey += " ( [DB_DATETIME], [MQ_MSG_ID] )";
m_sPriKey += " ON [PRIMARY] ";                  // ❌ Filegroup is SQL Server
```

#### PostgreSQL (required):
```cpp
m_sPriKey = " ALTER TABLE ";
m_sPriKey += GetDefaultSQL();
m_sPriKey += " ADD ";                           // ✅ Remove WITH NOCHECK
m_sPriKey += " CONSTRAINT \"PK_";               // ✅ Use double quotes
m_sPriKey += GetDefaultSQL();
m_sPriKey += "\" PRIMARY KEY ";                 // ✅ Remove CLUSTERED
m_sPriKey += " ( DB_DATETIME, MQ_MSG_ID )";     // ✅ Remove brackets
// Remove ON [PRIMARY] entirely
```

**Changes needed:**
- Remove `WITH NOCHECK` (SQL Server constraint validation option)
- Remove `CLUSTERED` (SQL Server index storage type)
- Remove `ON [PRIMARY]` (SQL Server filegroup specification)
- Replace `[identifier]` with `"identifier"` or no quotes (lowercase)

### 3. **Index Creation** ⚠️

#### SQL Server (current):
```cpp
m_sIndex1 = " CREATE INDEX [IX1_";
m_sIndex1 += GetDefaultSQL();
m_sIndex1 += "] ON [";
m_sIndex1 += GetDefaultSQL();
m_sIndex1 += "]( [NU_OPE] )";
m_sIndex1 += " ON [PRIMARY] ";                  // ❌ Filegroup is SQL Server
```

#### PostgreSQL (required):
```cpp
m_sIndex1 = " CREATE INDEX \"IX1_";             // ✅ Double quotes
m_sIndex1 += GetDefaultSQL();
m_sIndex1 += "\" ON ";                          // ✅ Remove brackets
m_sIndex1 += GetDefaultSQL();
m_sIndex1 += "( NU_OPE )";                      // ✅ Remove brackets
// Remove ON [PRIMARY] entirely
```

**Changes needed:**
- Remove `ON [PRIMARY]`
- Replace `[identifier]` with `"identifier"` or no quotes

### 4. **Identifier Quoting** ⚠️

| SQL Server | PostgreSQL | Note |
|------------|------------|------|
| `[TableName]` | `"TableName"` or `tablename` | Use lowercase for simplicity |
| `[ColumnName]` | `"ColumnName"` or `columnname` | Lowercase recommended |

**Recommendation:** Use **lowercase without quotes** for all identifiers to match PostgreSQL conventions and our configuration (`spb_log_bacen`, etc.).

---

## Detailed Changes Required

### File: **STRLogRS.cpp**

#### Location: Lines 63-74 (CREATE TABLE)

**BEFORE:**
```cpp
m_sCreate += " MQ_MSG_ID         [binary]   (24)    NOT NULL,  ";
m_sCreate += " MQ_CORREL_ID      [binary]   (24)    NOT NULL,  ";
m_sCreate += " DB_DATETIME       [datetime]         NOT NULL,  ";
m_sCreate += " STATUS_MSG        [char]             NOT NULL,  ";
m_sCreate += " MQ_QN_ORIGEM      [char]     (48)    NOT NULL,  ";
m_sCreate += " MQ_DATETIME       [datetime]         NOT NULL,  ";
m_sCreate += " MQ_HEADER         [binary]   (512)   NOT NULL,  ";
m_sCreate += " SECURITY_HEADER   [binary]   (332)   NULL,      ";
m_sCreate += " NU_OPE            [char]     (23)    NULL,      ";
m_sCreate += " COD_MSG           [char]     (09)    NULL,      ";
m_sCreate += " MSG               [text]             NULL       ";
```

**AFTER:**
```cpp
m_sCreate += " mq_msg_id         BYTEA              NOT NULL,  ";
m_sCreate += " mq_correl_id      BYTEA              NOT NULL,  ";
m_sCreate += " db_datetime       TIMESTAMP          NOT NULL,  ";
m_sCreate += " status_msg        CHAR(1)            NOT NULL,  ";
m_sCreate += " mq_qn_origem      VARCHAR(48)        NOT NULL,  ";
m_sCreate += " mq_datetime       TIMESTAMP          NOT NULL,  ";
m_sCreate += " mq_header         BYTEA              NOT NULL,  ";
m_sCreate += " security_header   BYTEA              NULL,      ";
m_sCreate += " nu_ope            VARCHAR(23)        NULL,      ";
m_sCreate += " cod_msg           VARCHAR(9)         NULL,      ";
m_sCreate += " msg               TEXT               NULL       ";
```

**Changes:**
- Column names: lowercase
- `[binary](n)` → `BYTEA` (PostgreSQL stores length automatically)
- `[datetime]` → `TIMESTAMP`
- `[char](n)` → `VARCHAR(n)` or `CHAR(n)`
- `[text]` → `TEXT`
- Remove all brackets

#### Location: Lines 77-86 (ALTER TABLE - Primary Key)

**BEFORE:**
```cpp
m_sPriKey = " ALTER TABLE ";
m_sPriKey += GetDefaultSQL();
m_sPriKey += " WITH NOCHECK ADD ";
m_sPriKey += " CONSTRAINT [PK_";
m_sPriKey += GetDefaultSQL();
m_sPriKey += "] PRIMARY KEY CLUSTERED ";
m_sPriKey += " ( [DB_DATETIME], [MQ_MSG_ID] )";
m_sPriKey += " ON [PRIMARY] ";
```

**AFTER:**
```cpp
m_sPriKey = " ALTER TABLE ";
m_sPriKey += GetDefaultSQL();
m_sPriKey += " ADD ";
m_sPriKey += " CONSTRAINT pk_";
m_sPriKey += GetDefaultSQL();
m_sPriKey += " PRIMARY KEY ";
m_sPriKey += " ( db_datetime, mq_msg_id )";
// Remove ON [PRIMARY]
```

**Changes:**
- Remove `WITH NOCHECK`
- Remove `CLUSTERED`
- Remove `ON [PRIMARY]`
- Lowercase constraint name and column names
- Remove brackets

#### Location: Lines 88-94 (CREATE INDEX)

**BEFORE:**
```cpp
m_sIndex1 = " CREATE INDEX [IX1_";
m_sIndex1 += GetDefaultSQL();
m_sIndex1 += "] ON [";
m_sIndex1 += GetDefaultSQL();
m_sIndex1 += "]( [NU_OPE] )";
m_sIndex1 += " ON [PRIMARY] ";
```

**AFTER:**
```cpp
m_sIndex1 = " CREATE INDEX ix1_";
m_sIndex1 += GetDefaultSQL();
m_sIndex1 += " ON ";
m_sIndex1 += GetDefaultSQL();
m_sIndex1 += "( nu_ope )";
// Remove ON [PRIMARY]
```

**Changes:**
- Lowercase index name
- Remove `ON [PRIMARY]`
- Remove brackets from identifiers

#### Location: Lines 121-131 (DoFieldExchange - RFX mapping)

**IMPACT:** Need to verify column name mapping

**BEFORE:**
```cpp
RFX_Binary(pFX, _T("[MQ_MSG_ID]"), m_MQ_MSG_ID, 24);
RFX_Date  (pFX, _T("[DB_DATETIME]"), m_DB_DATETIME);
RFX_Text  (pFX, _T("[NU_OPE]"), m_NU_OPE);
```

**AFTER (Option 1 - Lowercase):**
```cpp
RFX_Binary(pFX, _T("mq_msg_id"), m_MQ_MSG_ID, 24);
RFX_Date  (pFX, _T("db_datetime"), m_DB_DATETIME);
RFX_Text  (pFX, _T("nu_ope"), m_NU_OPE);
```

**AFTER (Option 2 - Quoted uppercase, if needed):**
```cpp
RFX_Binary(pFX, _T("\"MQ_MSG_ID\""), m_MQ_MSG_ID, 24);
RFX_Date  (pFX, _T("\"DB_DATETIME\""), m_DB_DATETIME);
RFX_Text  (pFX, _T("\"NU_OPE\""), m_NU_OPE);
```

**Recommendation:** Use **Option 1 (lowercase)** to match PostgreSQL conventions.

---

### Files: **BacenAppRS.cpp**, **IFAppRS.cpp**, **ControleRS.cpp**

**Same changes apply:**
1. Update CREATE TABLE column definitions
2. Update ALTER TABLE (remove WITH NOCHECK, CLUSTERED, ON [PRIMARY])
3. Update CREATE INDEX (remove ON [PRIMARY])
4. Update DoFieldExchange column names to lowercase
5. Convert data types: [binary]→BYTEA, [datetime]→TIMESTAMP, [char]→VARCHAR/CHAR, [text]→TEXT

---

## Additional Considerations

### 1. **MFC RFX Functions**
MFC's Record Field Exchange (RFX) functions should work with PostgreSQL ODBC driver, but data types need verification:

| MFC Function | SQL Server Type | PostgreSQL Type | Status |
|--------------|-----------------|-----------------|--------|
| `RFX_Binary` | `[binary](n)` | `BYTEA` | ✅ Should work |
| `RFX_Date` | `[datetime]` | `TIMESTAMP` | ✅ Should work |
| `RFX_Text` | `[char]`, `[text]` | `VARCHAR`, `TEXT` | ✅ Should work |
| `RFX_Long` | `[int]` | `INTEGER` | ✅ Should work |

### 2. **Table Name Case Sensitivity**
- `GetDefaultSQL()` returns table name from `m_sTblName`
- Verify that `m_sTblName` is set to **lowercase** in configuration:
  - `spb_log_bacen` (not `SPB_LOG_BACEN`)
  - `spb_bacen_to_local` (not `SPB_BACEN_TO_LOCAL`)
  - `spb_local_to_bacen` (not `SPB_LOCAL_TO_BACEN`)
  - `spb_controle` (not `SPB_CONTROLE`)

### 3. **Binary Data Handling**
- SQL Server: `[binary](n)` has fixed length
- PostgreSQL: `BYTEA` has variable length
- The ODBC driver should handle the conversion, but verify that:
  - MQ message IDs (24 bytes) are stored correctly
  - MQ headers (512 bytes) are stored correctly
  - Security headers (332 bytes) are stored correctly

---

## Testing Checklist

After making code changes:

- [ ] Compile the application (no syntax errors)
- [ ] Test DDL execution (CREATE TABLE, ALTER TABLE, CREATE INDEX)
- [ ] Verify table creation in PostgreSQL (`\d tablename` in psql)
- [ ] Test INSERT operations (AddNew + Update)
- [ ] Test SELECT operations (Open recordset, navigate)
- [ ] Test UPDATE operations (Edit + Update)
- [ ] Test DELETE operations
- [ ] Verify binary data storage (BYTEA columns)
- [ ] Verify timestamp handling (TIMESTAMP columns)
- [ ] Test with actual MQ messages

---

## Recommended Action Plan

### Phase 1: Backup
```bash
# Create backup of original files
cp STRLogRS.cpp STRLogRS.cpp.sql_server_backup
cp BacenAppRS.cpp BacenAppRS.cpp.sql_server_backup
cp IFAppRS.cpp IFAppRS.cpp.sql_server_backup
cp ControleRS.cpp ControleRS.cpp.sql_server_backup
```

### Phase 2: Update Code
1. Update **STRLogRS.cpp** (simplest file, test first)
2. Test table creation and basic operations
3. Update **ControleRS.cpp**
4. Update **BacenAppRS.cpp**
5. Update **IFAppRS.cpp**

### Phase 3: Test
1. Rebuild application
2. Run with test database
3. Verify all table operations
4. Load test with sample data

---

## Summary

**Total files needing changes:** 4
**Total lines affected:** ~80 lines across 4 files
**Complexity:** Low-Medium (mostly find/replace with validation)
**Risk:** Low (DDL only, not affecting runtime query logic)

**Estimated effort:** 2-3 hours (coding + testing)

---

## Next Steps

Would you like me to:
1. **Generate PostgreSQL-compatible versions** of the 4 recordset files?
2. **Create a patch file** showing exact changes?
3. **Update one file** as an example, then you apply to others?

---

**Code review completed:** 2026-02-26
**Reviewer:** Claude Code
**Status:** Ready for implementation
