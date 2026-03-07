# SQLite Removal - Changes Summary

This document summarizes all changes made to remove SQLite support and use PostgreSQL exclusively.

---

## Overview

**Date:** March 7, 2026
**Reason:** Standardize on PostgreSQL for both SPBSite and BCSrvSqlMq to share the same database
**Impact:** All projects now use PostgreSQL only

---

## Files Modified

### 1. Configuration Files

#### `spbsite/.env`
**Before:**
```env
DATABASE_URL=sqlite+aiosqlite:///./spbsite.db
CATALOG_DATABASE_URL=sqlite+aiosqlite:///./spb_messages.db
```

**After:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:@localhost:5432/BCSPB
CATALOG_DATABASE_URL=postgresql+asyncpg://postgres:@localhost:5432/BCSPBSTR
```

---

### 2. Dependencies

#### `spb-shared/setup.py`
**Removed:**
- `aiosqlite>=0.19.0`

**Added:**
- `psycopg2-binary>=2.9.9`

#### `spb-shared/requirements.txt`
**Removed:**
- `aiosqlite>=0.19.0`

**Kept:**
- `asyncpg>=0.29.0`
- `psycopg2-binary>=2.9.9`

#### `spbsite/requirements.txt`
**Removed:**
- `aiosqlite>=0.20`

**Added:**
- `psycopg2-binary>=2.9`

**Kept:**
- `asyncpg>=0.30.0`

---

### 3. Code Files

#### `spb-shared/spb_shared/database.py`
**Changed:**
```python
# Before
database_url: Database connection URL (postgresql+asyncpg:// or sqlite+aiosqlite://)

# After
database_url: Database connection URL (postgresql+asyncpg://)
```

#### `test_scripts/simple_db_test.py`
**Before:**
```python
import sqlite3
DB_PATH = 'spbsite/spbsite.db'
conn = sqlite3.connect(DB_PATH)
cursor.execute('... VALUES (?, ?, ...)', ...)
```

**After:**
```python
import psycopg2
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'BCSPB',
    'user': 'postgres',
    'password': ''
}
conn = psycopg2.connect(**DB_PARAMS)
cursor.execute('... VALUES (%s, %s, ...)', ...)
```

---

### 4. Documentation

#### `README.md`
**Changes:**
- Removed "Supports PostgreSQL and SQLite" → "PostgreSQL database support"
- Removed "SQLite (development)" from prerequisites
- Removed "Development (SQLite)" database configuration section
- Updated architecture diagram to show single PostgreSQL database
- Updated Technology Stack table: "PostgreSQL / SQLite" → "PostgreSQL"
- Updated environment variable examples to use PostgreSQL URLs

#### New Files Created:
- `POSTGRESQL_SETUP.md` - Complete PostgreSQL setup guide

---

## Database Architecture Change

### Before (Separate Databases)
```
SPBSite          BCSrvSqlMq
   ↓                  ↓
SQLite           PostgreSQL
spbsite.db          BCSPB
```

**Problem:** Messages created in SPBSite (SQLite) were not visible to BCSrvSqlMq (PostgreSQL)

### After (Shared Database)
```
SPBSite ─────┐
             ├──→ PostgreSQL (BCSPB)
BCSrvSqlMq ──┘
```

**Solution:** Both services connect to the same PostgreSQL database

---

## Migration Steps Required

### 1. Install PostgreSQL
```bash
# Download from postgresql.org
# Install with default settings
# Remember postgres password
```

### 2. Create Databases
```sql
CREATE DATABASE "BCSPB";
CREATE DATABASE "BCSPBSTR";
```

### 3. Update Configuration
```bash
# Edit spbsite/.env
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@localhost:5432/BCSPB
CATALOG_DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@localhost:5432/BCSPBSTR

# Edit BCSrvSqlMq/python/BCSrvSqlMq.ini
[Database]
DBName=BCSPB
DBAliasName=BCSPBSTR
DBUserName=postgres
DBPassword=PASSWORD
```

### 4. Reinstall Dependencies
```bash
cd spb-shared
pip install -e .

cd ../spbsite
pip install -r requirements.txt

cd ../BCSrvSqlMq/python
pip install -r requirements.txt
```

### 5. Initialize Database
```bash
cd spbsite
alembic upgrade head
python -m app.seed
```

---

## Testing Changes

### Test Database Connection
```bash
cd ..
python test_scripts/simple_db_test.py
```

**Expected Output:**
```
Creating Test Message
Operation Number: 20260307XXXXXX
[OK] Message inserted into database
```

### Test SPBSite
```bash
cd spbsite
uvicorn app.main:app --reload --port 8000
```

Visit: http://localhost:8000
Login: admin / admin

### Test BCSrvSqlMq
```bash
cd ../BCSrvSqlMq/python
python -m bcsrvsqlmq.main_srv
```

---

## Rollback (If Needed)

To revert to SQLite:

1. Restore files from git:
   ```bash
   git checkout HEAD -- spbsite/.env
   git checkout HEAD -- spb-shared/setup.py
   git checkout HEAD -- spbsite/requirements.txt
   git checkout HEAD -- test_scripts/simple_db_test.py
   ```

2. Reinstall dependencies:
   ```bash
   pip install aiosqlite
   ```

3. Run migrations:
   ```bash
   cd spbsite
   alembic upgrade head
   ```

---

## Benefits

1. **Shared Data:** SPBSite and BCSrvSqlMq now access the same messages
2. **Production Ready:** PostgreSQL is enterprise-grade
3. **Better Performance:** PostgreSQL handles concurrent connections better
4. **Simpler Architecture:** One database system instead of two
5. **Feature Parity:** Both services use the same database features

---

## Breaking Changes

1. **SQLite databases no longer used:**
   - `spbsite/spbsite.db` - replaced by PostgreSQL BCSPB
   - `spbsite/spb_messages.db` - replaced by PostgreSQL BCSPBSTR

2. **Connection strings changed:**
   - Must use `postgresql+asyncpg://` instead of `sqlite+aiosqlite://`

3. **Password required:**
   - PostgreSQL requires authentication (SQLite didn't)

4. **PostgreSQL service must be running:**
   - Unlike SQLite, PostgreSQL is a server process

---

## Next Steps

1. Follow [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) to set up databases
2. Update all `.env` and `.ini` files with PostgreSQL credentials
3. Run migrations to create schema
4. Test E2E flow: SPBSite → BCSrvSqlMq → PostgreSQL
5. Verify message sharing between services

---

## Support

For issues:
1. Check PostgreSQL is running: `sc query postgresql-x64-15`
2. Verify connection settings in `.env` and `.ini` files
3. Check PostgreSQL logs: `C:\Program Files\PostgreSQL\15\data\log\`
4. Test connection: `psql -U postgres -d BCSPB`

---

**Summary:** All SQLite code removed. System now uses PostgreSQL exclusively for both SPBSite and BCSrvSqlMq, enabling proper message sharing and E2E testing.
