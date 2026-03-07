# BCSrvSqlMq Integration with spb-shared

## Overview

This guide explains how to integrate the BCSrvSqlMq project with the new spb-shared package to ensure database schema synchronization.

## Current BCSrvSqlMq Structure

BCSrvSqlMq uses:
- **psycopg2** for database connectivity
- **Custom recordset classes** (CBacenAppRS, CIFAppRS, CControleRS, CSTRLogRS)
- **Direct SQL in Python** for table creation and operations

## Integration Options

### Option 1: Migrate to SQLAlchemy ORM (Recommended)

Replace the custom recordset classes with SQLAlchemy models from spb-shared.

#### Benefits:
- Automatic schema synchronization
- Better type safety and IDE support
- Easier to maintain and test
- Alembic migrations for schema changes

#### Implementation Steps:

1. **Install spb-shared package**

```bash
cd BCSrvSqlMq/python
pip install -e ../../spb-shared
```

2. **Update requirements.txt**

```txt
# Add to BCSrvSqlMq/python/requirements.txt
spb-shared>=0.1.0
```

3. **Replace recordset classes**

Before (old approach):
```python
from bcsrvsqlmq.db.bacen_app_rs import CBacenAppRS
from bcsrvsqlmq.db.bc_database import CBCDatabase

db = CBCDatabase(db_name='spbdb', db_server='localhost', ...)
db.open()

rs = CBacenAppRS(db, 'bacen_req')
rs.open()
while not rs.is_eof():
    print(rs.m_NU_OPE)
    rs.move_next()
```

After (new approach with spb-shared):
```python
from spb_shared import get_async_engine, get_async_session
from spb_shared.models import SPBBacenToLocal

# Initialize database
engine = get_async_engine("postgresql+asyncpg://user:pass@localhost/spbdb")
SessionLocal = get_async_session(engine)

# Query data
async with SessionLocal() as session:
    result = await session.execute(
        select(SPBBacenToLocal).where(SPBBacenToLocal.nu_ope == '12345')
    )
    messages = result.scalars().all()
    for msg in messages:
        print(msg.nu_ope)
```

4. **Update table creation logic**

Before:
```python
# In bacen_req.py
rs = CBacenAppRS(db, 'bacen_req')
rs.create_table()
```

After:
```python
from spb_shared.database import Base

# Create all tables
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

5. **Refactor service modules**

| Old Module | New Approach |
|------------|-------------|
| `bacen_req.py` | Use `SPBBacenToLocal` from spb-shared |
| `if_req.py` | Use `SPBLocalToBacen` from spb-shared |
| `controle_rs.py` | Use `SPBControle` from spb-shared |
| `str_log_rs.py` | Use `SPBLogBacen` from spb-shared |

### Option 2: Keep Existing Code, Sync Schema Manually

If you prefer to keep the existing psycopg2 recordset pattern:

1. **Keep custom recordsets** but update CREATE TABLE statements to match spb-shared models
2. **Use spb-shared as reference** for schema changes
3. **Manually sync** when schema changes in spb-shared

#### Update recordset CREATE TABLE statements:

```python
# In bacen_app_rs.py - update m_sCreate to match spb-shared
class CBacenAppRS:
    def __init__(self, database, table_name):
        # ... existing code ...
        
        # Updated to match spb-shared/models/messages.py
        self.m_sCreate = f'''CREATE TABLE {tbl} (
            mq_msg_id       BYTEA               NOT NULL,
            mq_correl_id    BYTEA               NOT NULL,
            db_datetime     TIMESTAMP            NOT NULL,
            status_msg      CHAR(1)              NOT NULL,
            flag_proc       CHAR(1)              NOT NULL,
            mq_qn_origem    VARCHAR(48)          NOT NULL,
            mq_datetime     TIMESTAMP            NOT NULL,
            mq_header       BYTEA               NOT NULL,
            security_header BYTEA               NOT NULL,
            nu_ope          VARCHAR(23)              NULL,
            cod_msg         VARCHAR(9)               NULL,
            msg             TEXT                     NULL,
            PRIMARY KEY (db_datetime, mq_msg_id)
        )'''
```

## Testing Integration

### 1. Verify Both Projects Use Same Schema

```bash
# In SPBSite
sqlite3 spbsite.db ".schema spb_bacen_to_local"

# In BCSrvSqlMq
psql -d spbdb -c "\d bacen_req"
```

Compare output to ensure schemas match.

### 2. Cross-Project Data Test

```python
# Write data in BCSrvSqlMq, read in SPBSite (or vice versa)
# This confirms schema compatibility

# In BCSrvSqlMq: Insert message
# ... your insert code ...

# In SPBSite: Read same message
from spb_shared.models import SPBBacenToLocal
# ... query by nu_ope or other field ...
```

### 3. Migration Test

```bash
# Create test migration in spb-shared
cd spb-shared
alembic revision --autogenerate -m "Add test field"

# Verify both projects can apply it
cd ../BCSrvSqlMq/python
alembic upgrade head

cd ../../spbsite
alembic upgrade head
```

## Maintenance Workflow

### When Schema Changes Are Needed:

1. **Make changes in spb-shared models**
```bash
cd spb-shared
vim spb_shared/models/messages.py  # Edit model
```

2. **Create migration**
```bash
alembic revision --autogenerate -m "Add new field"
alembic upgrade head
```

3. **Update both projects**
```bash
# SPBSite
cd ../spbsite
alembic upgrade head

# BCSrvSqlMq  
cd ../BCSrvSqlMq
alembic upgrade head
```

4. **Test both projects** to ensure compatibility

## Rollback Plan

If integration causes issues:

```bash
# Revert BCSrvSqlMq to original code
git checkout BCSrvSqlMq/python/bcsrvsqlmq/

# Keep spb-shared for SPBSite
# BCSrvSqlMq can continue using old approach temporarily
```

## Next Steps After Integration

1. ✅ Both projects now share same schema
2. ✅ Schema changes managed in one place (spb-shared)
3. ✅ Alembic migrations ensure consistency
4. ✅ Can share data between SPBSite and BCSrvSqlMq databases

## Support

For issues:
1. Check `spb-shared/README.md` for model documentation
2. Review `MIGRATION_GUIDE.md` for database migration steps
3. Compare table schemas between projects if data sync issues occur
