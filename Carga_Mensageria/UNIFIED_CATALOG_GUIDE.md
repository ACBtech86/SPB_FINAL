# Unified SPB Catalog Database Guide

## Overview

The **spb_catalog** database is a single source of truth for all SPB message definitions, replacing duplicated catalog tables across multiple projects.

## Architecture

```
┌─────────────────────────┐
│   spb_catalog (NEW)     │  ← Single Source of Truth
│   Unified Catalog DB    │
│                         │
│  Tables:                │
│  • SPB_MENSAGEM         │  Full message definitions
│  • SPB_DICIONARIO       │  Field type dictionary
│  • SPB_MSGFIELD         │  Message field structures
│  • SPB_XMLXSL           │  XML/XSL forms
│  • SPB_DOMINIOS         │  Domain value lists
│  • SPB_ISPB             │  Institution registry
│                         │
│  Views (compatibility): │
│  • spb_mensagem_view    │  Lowercase for SPBSite
│  • spb_dicionario_view  │  Lowercase for SPBSite
│  • spb_msgfield_view    │  Lowercase for SPBSite
│  • spb_mensagem_simple  │  Simplified for BCSrvSqlMq
└────────┬────────────────┘
         │ Used by all projects:
         │
         ├──────────────────┬──────────────────┬────────────────────┐
         ▼                  ▼                  ▼                    ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│ Carga_Mensageria │ │  BCSrvSqlMq  │ │   SPBSite    │ │ Future Projects  │
│                  │ │              │ │              │ │                  │
│ Writes catalog   │ │ Reads catalog│ │ Reads catalog│ │ Read catalog     │
│ via ETL          │ │              │ │              │ │                  │
└──────────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘
```

## Benefits

1. **Single Source of Truth** - No data duplication
2. **Consistency** - All projects use same catalog version
3. **Easier Maintenance** - Update once, affects all projects
4. **Data Integrity** - Foreign keys enforce relationships
5. **Audit Trail** - Automatic timestamps track changes

## Database Schema

### Core Tables

| Table | Rows | Purpose | Writer | Readers |
|-------|------|---------|--------|---------|
| `SPB_MENSAGEM` | ~1,093 | Message definitions | Carga_Mensageria | All |
| `SPB_DICIONARIO` | ~2,363 | Field type dictionary | Carga_Mensageria | All |
| `SPB_MSGFIELD` | ~14,489 | Message field structures | Carga_Mensageria | All |
| `SPB_XMLXSL` | ~1,093 | XML/XSL forms | Carga_Mensageria | SPBSite |
| `SPB_DOMINIOS` | Variable | Domain value lists | Manual/Import | All |
| `SPB_ISPB` | ~2,335 | Institution registry | Import | All |

### Key Features

- **Foreign Keys** - Enforce referential integrity
- **Indexes** - Optimize common queries
- **Triggers** - Auto-update `updated_at` timestamps
- **Views** - Backward compatibility with existing code

## Setup Instructions

### 1. Create Unified Catalog

```bash
cd Carga_Mensageria
python create_unified_catalog.py
```

This creates the `spb_catalog` database with:
- 6 core tables
- 4 compatibility views
- Indexes and constraints
- Audit triggers

### 2. Migrate Existing Data

```bash
python migrate_to_unified_catalog.py
```

This migrates data from `spb_mensageria` → `spb_catalog`

### 3. Update Project Configurations

#### **Carga_Mensageria** (ETL Tool - Writes Catalog)

Edit `config.py`:
```python
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "spb_catalog",  # Changed from spb_mensageria
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD", ""),
}
```

#### **BCSrvSqlMq** (Message Processor - Reads Catalog)

Edit connection in `setup_database.py` or config:
```python
CATALOG_DB = 'spb_catalog'  # Changed from bcspbstr
```

Use simple view for backward compatibility:
```python
# Query message catalog
cur.execute("SELECT * FROM spb_mensagem_simple")
```

#### **SPBSite** (Web Interface - Reads Catalog)

Edit `app/config.py`:
```python
class Settings(BaseSettings):
    # Main operational database
    database_url: str = "postgresql+asyncpg://user:pass@localhost/bcspbstr"

    # Catalog database (NEW - unified catalog)
    catalog_database_url: str = "postgresql+asyncpg://user:pass@localhost/spb_catalog"
```

No code changes needed - views maintain compatibility!

## Connection URLs

### PostgreSQL (psycopg)
```python
postgresql://user:password@localhost:5432/spb_catalog
```

### Async PostgreSQL (asyncpg)
```python
postgresql+asyncpg://user:password@localhost:5432/spb_catalog
```

## Access Patterns

### Read-Only Access (BCSrvSqlMq, SPBSite)

```sql
-- Get all messages
SELECT * FROM spb_mensagem_view;

-- Get message fields
SELECT * FROM spb_msgfield_view WHERE msg_id = 'GEN0001';

-- Get field type info
SELECT * FROM spb_dicionario_view WHERE msg_cpotag = 'CodMsg';
```

### Write Access (Carga_Mensageria Only)

```python
# Import XSD data
python import_from_xsd.py

# Run ETL steps via GUI
python main.py
```

## Migration Checklist

- [ ] Create unified catalog database
- [ ] Migrate existing data
- [ ] Update Carga_Mensageria config
- [ ] Update BCSrvSqlMq config
- [ ] Update SPBSite config
- [ ] Test Carga_Mensageria ETL
- [ ] Test BCSrvSqlMq message processing
- [ ] Test SPBSite web interface
- [ ] Verify all projects use spb_catalog
- [ ] Remove old catalog tables from operational databases
- [ ] Update deployment documentation

## Database Permissions

### Recommended PostgreSQL Roles

```sql
-- Read-only role for BCSrvSqlMq and SPBSite
CREATE ROLE spb_catalog_reader;
GRANT CONNECT ON DATABASE spb_catalog TO spb_catalog_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO spb_catalog_reader;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO spb_catalog_reader;

-- Read-write role for Carga_Mensageria
CREATE ROLE spb_catalog_writer;
GRANT CONNECT ON DATABASE spb_catalog TO spb_catalog_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO spb_catalog_writer;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO spb_catalog_writer;

-- Create users
CREATE USER bcspbstr_user WITH PASSWORD 'password';
GRANT spb_catalog_reader TO bcspbstr_user;

CREATE USER carga_user WITH PASSWORD 'password';
GRANT spb_catalog_writer TO carga_user;
```

## Backup Strategy

```bash
# Backup unified catalog
pg_dump -h localhost -U postgres -F c -b -v -f spb_catalog_backup.dump spb_catalog

# Restore
pg_restore -h localhost -U postgres -d spb_catalog -v spb_catalog_backup.dump
```

## Troubleshooting

### "Database spb_catalog does not exist"
```bash
python create_unified_catalog.py
```

### "No data in tables"
```bash
python migrate_to_unified_catalog.py
```

### "Permission denied for table"
```sql
-- Grant appropriate permissions (see Database Permissions above)
```

### "Foreign key violation"
Ensure migration order:
1. SPB_ISPB
2. SPB_DOMINIOS
3. SPB_MENSAGEM
4. SPB_DICIONARIO
5. SPB_MSGFIELD
6. SPB_XMLXSL

## Maintenance

### Updating Catalog Data

1. Run Carga_Mensageria import:
   ```bash
   python import_from_xsd.py
   ```

2. Run ETL steps via GUI or command line

3. Changes automatically visible to all projects

### Monitoring

```sql
-- Check last update times
SELECT
    'SPB_MENSAGEM' as table_name,
    COUNT(*) as rows,
    MAX(updated_at) as last_update
FROM SPB_MENSAGEM
UNION ALL
SELECT
    'SPB_DICIONARIO',
    COUNT(*),
    MAX(updated_at)
FROM SPB_DICIONARIO;

-- Check view data
SELECT COUNT(*) FROM spb_mensagem_view;
SELECT COUNT(*) FROM spb_dicionario_view;
SELECT COUNT(*) FROM spb_msgfield_view;
```

## Future Enhancements

- [ ] Versioning support (track catalog changes over time)
- [ ] API for catalog queries
- [ ] Automated synchronization across environments
- [ ] Data validation rules
- [ ] Change notifications
