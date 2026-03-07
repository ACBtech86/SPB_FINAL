# SPB Database Migration Guide

## Overview

This guide explains how to migrate the existing SPBSite database to use the new shared schema that matches BCSrvSqlMq.

## ⚠️ Important Changes

### 1. Primary Key Changes

**OLD Schema (SPBSite)**:
- All tables used autoincrement `id` as primary key
- Simple single-column primary keys

**NEW Schema (spb-shared)**:
- Message tables: Composite PK `(db_datetime, mq_msg_id)` or `(db_datetime, cod_msg, mq_qn_destino)`
- Control tables: PK is `ispb` (no autoincrement)
- Binary fields for MQ message IDs

### 2. New Fields Added

- `mq_msg_id`, `mq_correl_id` - Now BYTEA/LargeBinary (was String)
- `mq_header`, `security_header` - New BYTEA fields
- `msg_len` - Message length field
- `mq_msg_id_coa/cod/rep` - Acknowledgment tracking fields

### 3. Field Type Changes

- `status_msg`, `flag_proc` - Changed to CHAR(1)
- `mq_qn_origem`, `mq_qn_destino` - Changed to VARCHAR(48)
- `nu_ope` - Changed to VARCHAR(23)
- `cod_msg` - Changed to VARCHAR(9)

## Migration Options

### Option A: Fresh Start (Recommended for Development)

If you don't need to preserve existing data:

```bash
# 1. Backup existing database (just in case)
cp spbsite.db spbsite.db.backup

# 2. Remove old database
rm spbsite.db

# 3. Recreate with new schema
python -m app.seed

# 4. Verify
python -c "from app.database import engine; import asyncio; from spb_shared.database import Base; asyncio.run(Base.metadata.create_all(bind=engine.sync_engine))"
```

### Option B: Data Migration (For Production)

If you need to preserve existing data, follow these steps:

#### Step 1: Export Existing Data

```python
# export_data.py
import asyncio
import sqlite3
import json
from datetime import datetime

async def export_data():
    conn = sqlite3.connect('spbsite.db')
    cursor = conn.cursor()
    
    # Export users
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    with open('users_export.json', 'w') as f:
        json.dump(users, f, default=str)
    
    # Export SPB control
    cursor.execute('SELECT * FROM spb_controle')
    controle = cursor.fetchall()
    with open('controle_export.json', 'w') as f:
        json.dump(controle, f, default=str)
    
    # Add similar exports for other tables as needed
    
    conn.close()

if __name__ == '__main__':
    asyncio.run(export_data())
```

#### Step 2: Create New Database

```bash
# Rename old database
mv spbsite.db spbsite.db.old

# Create new schema
cd ../spb-shared
alembic upgrade head

cd ../spbsite
python -m app.seed
```

#### Step 3: Import Data

```python
# import_data.py
import asyncio
import json
from datetime import datetime
from app.database import async_session
from spb_shared.models import User, SPBControle
import hashlib

async def import_data():
    async with async_session() as session:
        # Import users
        with open('users_export.json', 'r') as f:
            users_data = json.load(f)
        
        for user_row in users_data:
            user = User(
                username=user_row[1],
                password_hash=user_row[2],
                is_active=bool(user_row[3]),
                created_at=datetime.fromisoformat(user_row[4])
            )
            session.add(user)
        
        # Import control data (with PK change: id → ispb)
        with open('controle_export.json', 'r') as f:
            controle_data = json.load(f)
        
        for ctrl_row in controle_data:
            ctrl = SPBControle(
                ispb=ctrl_row[1],  # Now PK instead of id
                nome_ispb=ctrl_row[2],
                msg_seq=ctrl_row[3],
                # ... map other fields
            )
            session.add(ctrl)
        
        await session.commit()

if __name__ == '__main__':
    asyncio.run(import_data())
```

#### Step 4: Verify Migration

```bash
# Check table schemas
sqlite3 spbsite.db ".schema"

# Test the application
uvicorn app.main:app --reload
```

## Testing After Migration

1. **Login** - Verify user authentication works
2. **Message Forms** - Test loading message forms from catalog
3. **Message Submission** - Try submitting a test message
4. **Monitoring** - Check control panel and message monitoring
5. **Logs** - Verify log viewing

## Rollback Procedure

If migration fails:

```bash
# Restore old database
mv spbsite.db.old spbsite.db

# Reinstall old models (if needed)
git checkout app/models/
```

## Notes for Production PostgreSQL

When migrating to PostgreSQL for production:

```bash
# 1. Update .env
DATABASE_URL=postgresql+asyncpg://postgres:Rama1248@localhost:5432/spbsite

# 2. Create database
createdb spbsite

# 3. Run migrations
cd ../spb-shared
alembic upgrade head

# 4. Seed initial data
cd ../spbsite
python -m app.seed
```

## Next Steps

After successful migration:

1. Delete backup files if no longer needed
2. Update BCSrvSqlMq to use spb-shared package
3. Test integration between both projects
4. Document any custom migration steps needed
