# Database Setup Complete

**Last Updated:** 2026-03-09
**Status:** Updated for unified catalog architecture

---

## Architecture

BCSrvSqlMq now uses **two databases**:

| Database | Purpose | Managed by |
|----------|---------|------------|
| **BCSPB** | Operational tables (runtime data) | `setup_database.py` |
| **spb_catalog** | Catalog tables (message definitions) | Carga_Mensageria |

---

## Operational Database: BCSPB

| Table | Purpose |
|-------|---------|
| **SPB_LOG_BACEN** | Transaction log |
| **SPB_BACEN_TO_LOCAL** | Messages from BACEN to local system |
| **SPB_LOCAL_TO_BACEN** | Messages from local system to BACEN |
| **SPB_CONTROLE** | Control/coordination table |

**Control Record:**
- ISPB: 36266751
- Name: FINVEST
- Status: A (Active)

## Catalog Database: spb_catalog (Unified)

Catalog tables are now in the **unified catalog database** (`spb_catalog`),
shared across all SPB projects. Managed by Carga_Mensageria.

| Table | Records | Purpose |
|-------|---------|---------|
| **SPB_MENSAGEM** | ~1,093 | SPB message definitions |
| **SPB_DICIONARIO** | ~2,363 | Field type definitions |
| **SPB_MSGFIELD** | ~14,489 | Message field structures |

---

## Setup Scripts

### 1. setup_database.py
Creates the **operational database** (BCSPB) with 4 tables.

```bash
python setup_database.py
```

### 2. verify_db_config.py
Verifies both operational and catalog database connectivity.

```bash
python verify_db_config.py
```

### 3. load_catalog_from_xsd.py (standalone alternative)
Populates catalog tables directly into `spb_catalog`.
Prefer using Carga_Mensageria instead.

```bash
python load_catalog_from_xsd.py
```

---

## Configuration

### BCSrvSqlMq.ini

```ini
[DataBase]
dbaliasname = BCSPBSTR
dbserver = localhost
dbname = BCSPB
dbport = 5432
dbusername = postgres
dbpassword = Rama1248
dbcatalogname = spb_catalog
dbtbstrlog = spb_log_bacen
dbtbbacencidadeapp = spb_bacen_to_local
dbtbcidadebacenapp = spb_local_to_bacen
dbtbcontrole = spb_controle
```

### Connection Details
- **Host:** localhost:5432
- **Operational DB:** BCSPB
- **Catalog DB:** spb_catalog
- **User:** postgres

---

## Query Examples

### Operational queries (on BCSPB)
```sql
SELECT * FROM SPB_CONTROLE;
SELECT COUNT(*) FROM SPB_LOG_BACEN;
```

### Catalog queries (on spb_catalog)
```sql
-- Use quoted identifiers (uppercase preserved)
SELECT "MSG_ID", "MSG_DESCR" FROM "SPB_MENSAGEM" WHERE "MSG_ID" = 'GEN0001';
SELECT "MSG_CPOTAG", "MSG_CPOFORM", "MSG_CPOTAM" FROM "SPB_DICIONARIO";
```

---

## Maintenance

### Backup
```bash
pg_dump -U postgres -h localhost BCSPB > bcspb_backup.sql
pg_dump -U postgres -h localhost spb_catalog > spb_catalog_backup.sql
```

---

**Setup completed by:** Claude Code
**Last Updated:** 2026-03-09
**Database Version:** PostgreSQL
