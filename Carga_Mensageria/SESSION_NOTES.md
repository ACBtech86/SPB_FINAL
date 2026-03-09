# SPB Database Consolidation - Session Notes
**Date:** 2026-03-09
**Status:** ALL COMPLETE - Single database `banuxSPB`

## CURRENT STATE

**Database:** `banuxSPB` on PostgreSQL (single database for everything)
**Total catalog rows:** 17,897

| Table | Rows | Type |
|-------|------|------|
| SPB_MENSAGEM | 1,093 | Catalog |
| SPB_DICIONARIO | 2,363 | Catalog |
| SPB_MSGFIELD | 14,489 | Catalog |
| SPB_XMLXSL | 0 | Catalog (generate via Etapa A) |
| PLAN_MENSAGEM | 1,093 | Catalog |
| PLAN_EVENTO | 1,093 | Catalog |
| PLAN_Mensagem_Dados | 14,489 | Catalog |
| PLAN_DADOS | 2,363 | Catalog |
| PLAN_TIPOLOGIA | 1,128 | Catalog |
| spb_log_bacen | 0 | Operational |
| spb_bacen_to_local | 0 | Operational |
| spb_local_to_bacen | 0 | Operational |
| spb_controle | 1 | Operational |

**Views:** `spb_mensagem_view`, `spb_msgfield_view`, `spb_dicionario_view`
(lowercase aliases over quoted uppercase catalog tables, used by SPBSite SQLAlchemy models)

---

## Git Commits (All pushed to origin/main)

```
3f739ff feat: Create unified SPB catalog database (spb_catalog)
d6cac88 feat: Point BCSrvSqlMq and SPBSite to unified spb_catalog database
6b72d59 fix: Add catalog compatibility views and fix cross-database JOIN
b5aca7f feat: Consolidate to single banuxSPB database
```

---

## Database Architecture (Final)

```
+-----------------------------------------------+
|                  banuxSPB                      |
|                                                |
|  CATALOG TABLES (quoted uppercase):            |
|    "SPB_MENSAGEM"    "SPB_DICIONARIO"          |
|    "SPB_MSGFIELD"    "SPB_XMLXSL"              |
|    "PLAN_MENSAGEM"   "PLAN_DADOS"              |
|    "PLAN_EVENTO"     "PLAN_TIPOLOGIA"          |
|    "PLAN_Mensagem_Dados"  etc.                 |
|                                                |
|  COMPATIBILITY VIEWS (lowercase):              |
|    spb_mensagem_view  spb_dicionario_view      |
|    spb_msgfield_view                           |
|                                                |
|  OPERATIONAL TABLES (lowercase):               |
|    spb_log_bacen      spb_bacen_to_local       |
|    spb_local_to_bacen spb_controle             |
+-----------------------------------------------+
            |
    Used by all 3 projects:
            |
    +-------+--------+-----------+
    |                |           |
+---v-----+  +------v--+  +----v---+
| Carga   |  | BCSrvSql|  | SPBSite|
| Mensag. |  | Mq      |  |        |
|         |  |         |  |        |
| WRITE   |  | READ+   |  | READ   |
| catalog |  | WRITE   |  |        |
+---------+  | operat. |  +--------+
             +---------+
```

## Connection Details

```python
# Single connection for all projects
postgresql://postgres:Rama1248@localhost:5432/banuxSPB

# Async (for SPBSite)
postgresql+asyncpg://postgres:Rama1248@localhost:5432/banuxSPB
```

## Key Files Reference

### Carga_Mensageria
- `config.py` - `database = "banuxSPB"`
- `init_database.py` - Creates catalog tables + compatibility views
- `import_from_xsd.py` - Populates catalog from BCB XSD schemas
- `main.py` - Tkinter GUI

### BCSrvSqlMq
- `BCSrvSqlMq.ini` - `dbname = banuxSPB` (no separate catalog DB)
- `setup_database.py` - Creates operational tables in banuxSPB
- `python/bcsrvsqlmq/init_srv.py` - Single DB config
- `verify_db_config.py` - Checks all tables in banuxSPB

### SPBSite
- `app/config.py` - Single `database_url` -> banuxSPB
- `.env` - `DATABASE_URL=postgresql+asyncpg://postgres:Rama1248@localhost:5432/banuxSPB`
- `app/database.py` - Single engine, single `get_db()` (no catalog_db)
- `app/routers/queue.py` - Simple JOIN (single DB session)
- `app/routers/messages.py` - Uses `db` for both catalog and operational queries

## How to Set Up on a New Machine

```bash
# 1. Create database
psql -U postgres -c 'CREATE DATABASE "banuxSPB";'

# 2. Create operational tables
cd BCSrvSqlMq
PYTHONIOENCODING=utf-8 python setup_database.py

# 3. Create catalog tables + views
cd Carga_Mensageria
pip install psycopg psycopg-binary
python init_database.py

# 4. Populate catalog data
python import_from_xsd.py spb_schemas.zip

# 5. (Optional) Generate XML/XSL forms
python main.py  # Click "Etapa A"
```

## Known Issues

### SPB_XMLXSL generation warning
`import_from_xsd.py` Etapa A uses unquoted `SPB_XMLXSL` table name.
PostgreSQL lowercases it to `spb_xmlxsl` which doesn't match the quoted `"SPB_XMLXSL"`.
**Workaround:** Generate via `main.py` GUI (Etapa A button) instead.

### Windows console emoji encoding
`setup_database.py` prints emoji characters that fail on Windows cp1252 console.
**Workaround:** Run with `PYTHONIOENCODING=utf-8 python setup_database.py`

### PostgreSQL case sensitivity
Catalog tables use quoted uppercase identifiers (`"SPB_MENSAGEM"`, `"MSG_ID"`).
Operational tables use lowercase (`spb_controle`, `spb_log_bacen`).
Compatibility views bridge the gap for SPBSite SQLAlchemy models.

## Troubleshooting

### Case Sensitivity Errors
```
ERROR: relation "SPB_MENSAGEM" does not exist
```
**Solution:** Use quoted identifiers: `SELECT "MSG_ID" FROM "SPB_MENSAGEM"`

### Module Not Found
```
ERROR: No module named 'psycopg'
```
**Solution:** `pip install psycopg psycopg-binary`

### Database Does Not Exist
```
ERROR: database "banuxSPB" does not exist
```
**Solution:** `psql -U postgres -c 'CREATE DATABASE "banuxSPB";'`

---

## Session History

**Session 1 (2026-03-09):**
- Created spb_catalog, migrated Carga_Mensageria to PostgreSQL
- Populated 17,897 rows

**Session 2 (2026-03-09):**
- Updated BCSrvSqlMq and SPBSite to use spb_catalog
- Committed and pushed

**Session 3 (2026-03-09):**
- Added compatibility views for SPBSite models
- Fixed cross-database JOIN in queue_manager.py

**Session 4 (2026-03-09):**
- Consolidated everything into single database `banuxSPB`
- Removed separate catalog_database_url, catalog_engine, get_catalog_db
- Reverted queue_manager.py to simple JOIN (single DB)
- Created banuxSPB, ran setup_database.py + init_database.py + import_from_xsd.py
- All 22 tables/views created, 17,897 catalog rows populated

**Status:** ALL COMPLETE
**Git:** 4 commits pushed to origin/main
