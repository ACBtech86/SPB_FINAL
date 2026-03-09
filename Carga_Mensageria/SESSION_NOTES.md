# Unified Catalog Migration - Session Notes
**Date:** 2026-03-09
**Status:** ALL TASKS COMPLETED - All projects using unified spb_catalog

## FINAL RESULT

**Database:** `spb_catalog` on PostgreSQL
**Total rows imported:** 17,897

| Table | Rows | Status |
|-------|------|--------|
| SPB_MENSAGEM | 1,093 | Populated |
| SPB_DICIONARIO | 2,363 | Populated |
| SPB_MSGFIELD | 14,489 | Populated |
| SPB_XMLXSL | 0 | Generate via Etapa A |
| PLAN_MENSAGEM | 1,093 | Populated |
| PLAN_EVENTO | 1,093 | Populated |
| PLAN_Mensagem_Dados | 14,489 | Populated |
| PLAN_DADOS | 2,363 | Populated |
| PLAN_TIPOLOGIA | 1,128 | Populated |

**Resolution:** Updated schema to use quoted uppercase identifiers to preserve PostgreSQL case sensitivity.

---

## Git Commits (Pushed to origin)

```
3f739ff feat: Create unified SPB catalog database (spb_catalog)
d6cac88 feat: Point BCSrvSqlMq and SPBSite to unified spb_catalog database
```

---

## What We Accomplished

### Phase 1: Project Analysis
- Analyzed Carga_Mensageria project structure
- Identified duplicate catalog tables across 3 projects:
  - **Carga_Mensageria** (ETL tool - 15 tables including PLAN_* and SPB_*)
  - **BCSrvSqlMq** (Message processor - simplified catalog)
  - **SPBSite** (Web interface - views only)

### Phase 2: Cleaned Up Obsolete Code
- **Removed:** `import_from_mdb.py` (obsolete Access database import)
- **Reason:** XSD import from BCB is the current, maintained approach
- **Updated:** README.md to reflect only XSD import method

### Phase 3: PostgreSQL Migration
- **Migrated FROM:** SQLite (BCSPBSTR.db)
- **Migrated TO:** PostgreSQL
- **Updated Files:**
  - `config.py` - Now uses PostgreSQL connection
  - `db_connection.py` - Uses psycopg (PostgreSQL driver)
  - `init_database.py` - PostgreSQL schema
  - `main.py` - Shows PostgreSQL connection info
  - All SQL queries updated for PostgreSQL

### Phase 4: Unified Catalog Design
- **Created Files:**
  - `create_unified_catalog.py` - Creates spb_catalog database
  - `migrate_to_unified_catalog.py` - Migrates data between databases
  - `UNIFIED_CATALOG_GUIDE.md` - Complete documentation
  - `requirements.txt` - Python dependencies (psycopg)
  - `.env.example` - Configuration template

- **Database Created:** `spb_catalog`
  - 6 core tables (spb_mensagem, spb_dicionario, spb_msgfield, spb_xmlxsl, spb_dominios, spb_ispb)
  - 4 compatibility views (for SPBSite/BCSrvSqlMq)
  - Foreign keys, indexes, audit timestamps

### Phase 5: Configuration Updates
- `config.py` now points to `spb_catalog`
- Database: `spb_catalog` (unified catalog)

### Phase 6: BCSrvSqlMq Updated (Session 2)
- **INI config:** Added `dbcatalogname = spb_catalog`
- **setup_database.py:** Changed to `DB_NAME = 'BCSPB'`, removed catalog tables (now in spb_catalog)
- **init_srv.py:** Added `m_DBCatalogName` config property
- **load_catalog_from_xsd.py:** Points to `spb_catalog`
- **verify_db_config.py:** Rewritten to check both BCSPB and spb_catalog
- **Tests:** Updated all DB references from `bcspbstr` to `BCSPB`

### Phase 7: SPBSite Updated (Session 2)
- **config.py:** `catalog_database_url` default changed to `spb_catalog`
- **.env:** `CATALOG_DATABASE_URL` changed from `BCSPBSTR` to `spb_catalog`
- **.env.example:** PostgreSQL examples updated
- **database.py:** Comment updated

## RESOLVED: PostgreSQL Case Sensitivity

### Original Problem
PostgreSQL automatically lowercases unquoted identifiers:
- **Code expects:** `SPB_MENSAGEM`, `MSG_ID` (uppercase)
- **PostgreSQL created:** `spb_mensagem`, `msg_id` (lowercase)

### Resolution Applied
**Chose Option 1:** Updated schema to use quoted uppercase identifiers

**Actions Taken:**
1. Dropped and recreated `spb_catalog` database
2. Ran `init_database.py` with quoted identifiers
3. Verified uppercase preservation in PostgreSQL
4. Ran `import_from_xsd.py` successfully
5. Imported 17,897 rows from spb_schemas.zip

## Database Architecture (Final)

```
+-----------------------+     +------------------+
|   spb_catalog         |     |   BCSPB          |
|   (Unified Catalog)   |     |   (Operational)  |
|                       |     |                  |
|  "SPB_MENSAGEM"       |     | SPB_LOG_BACEN    |
|  "SPB_DICIONARIO"     |     | SPB_BACEN_TO_LOCAL|
|  "SPB_MSGFIELD"       |     | SPB_LOCAL_TO_BACEN|
|  "SPB_XMLXSL"         |     | SPB_CONTROLE     |
|  "PLAN_MENSAGEM"      |     +--------+---------+
|  "PLAN_DADOS"         |              |
|  "PLAN_EVENTO"        |     Used by BCSrvSqlMq
|  "PLAN_TIPOLOGIA"     |     runtime only
|  "PLAN_Mensagem_Dados"|
+-----------+-----------+
            |
   Shared by all projects:
            |
    +-------+--------+-----------+
    |                |           |
+---v-----+  +------v--+  +----v---+
| Carga   |  | BCSrvSql|  | SPBSite|
| Mensag. |  | Mq      |  |        |
|         |  |         |  |        |
| WRITE   |  | READ    |  | READ   |
+---------+  +---------+  +--------+
```

## Connection Details

```python
# PostgreSQL Connection (Catalog)
postgresql://postgres:Rama1248@localhost:5432/spb_catalog

# Async (for SPBSite)
postgresql+asyncpg://postgres:Rama1248@localhost:5432/spb_catalog

# Operational DB (BCSrvSqlMq runtime)
postgresql://postgres:Rama1248@localhost:5432/BCSPB
```

## Key Files Reference

### Carga_Mensageria
- `config.py` - Database connection (spb_catalog)
- `init_database.py` - Create schema
- `import_from_xsd.py` - Import from BCB XSD files
- `main.py` - Tkinter GUI
- `etapas.py` - ETL business logic (12 steps)

### BCSrvSqlMq
- `BCSrvSqlMq.ini` - Config with `dbcatalogname = spb_catalog`
- `setup_database.py` - Creates BCSPB (operational only)
- `python/bcsrvsqlmq/init_srv.py` - Reads `m_DBCatalogName`
- `verify_db_config.py` - Checks both databases

### SPBSite
- `app/config.py` - `catalog_database_url` -> spb_catalog
- `.env` - Runtime config
- `app/database.py` - Catalog engine connection

## Remaining Optional Tasks

1. **Generate SPB_XMLXSL** (Optional - can be done later)
   ```bash
   python main.py
   # Click "Etapa A" to generate XML/XSL forms
   ```

2. **Test All Applications End-to-End**
   - Carga_Mensageria: `python main.py` (data imported successfully)
   - BCSrvSqlMq: Test message processing with `verify_db_config.py`
   - SPBSite: Test web interface

## Troubleshooting

### Case Sensitivity Errors
```
ERROR: column "MSG_ID" does not exist
ERROR: relation "SPB_MENSAGEM" does not exist
```
**Solution:** Use quoted identifiers: `SELECT "MSG_ID" FROM "SPB_MENSAGEM"`

### Import Fails
```
ERROR: No module named 'psycopg'
```
**Solution:** `pip install -r requirements.txt`

### Connection Fails
```
ERROR: database "spb_catalog" does not exist
```
**Solution:** `python create_unified_catalog.py`

---

## Session Summary

**Session 1 Date:** 2026-03-09
- Created spb_catalog, migrated Carga_Mensageria to PostgreSQL
- Populated 17,897 rows

**Session 2 Date:** 2026-03-09
- Updated BCSrvSqlMq: operational DB = BCSPB, catalog = spb_catalog
- Updated SPBSite: catalog_database_url -> spb_catalog
- Committed and pushed both commits to origin

**Session 3 Date:** 2026-03-09
- Fixed SPBSite compatibility issues with spb_catalog:
  1. Added compatibility views to `init_database.py`: `spb_mensagem_view`, `spb_msgfield_view`, `spb_dicionario_view`
     - Map quoted uppercase table columns to lowercase aliases expected by spb-shared SQLAlchemy models
     - `spb_msgfield_view` includes synthetic `id` (ROW_NUMBER) and NULL `cod_grade` columns
     - `spb_dicionario_view` maps `MSG_CPOFORMATO` -> `msg_cpoform`
  2. Fixed cross-database JOIN in `spbsite/app/services/queue_manager.py`
     - `Fila` (BCSPB) cannot JOIN with `SPBMensagem` (spb_catalog) in a single session
     - Split into two queries: fetch Fila rows from BCSPB, then batch-lookup descriptions from spb_catalog
     - Updated `get_pending_messages()` signature to accept both `db` and `catalog_db` sessions
  3. Updated `spbsite/app/routers/queue.py` to inject `catalog_db` dependency

**Status:** ALL COMPLETE
**Blocker:** None
**Git:** 2 commits pushed to origin/main (session 3 changes pending commit)
