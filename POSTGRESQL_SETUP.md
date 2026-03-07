# PostgreSQL Setup Guide

This guide shows how to set up PostgreSQL databases for the SPB system.

---

## Prerequisites

- PostgreSQL 15+ installed
- psql command-line tool
- Administrator access to PostgreSQL

---

## Step 1: Install PostgreSQL

### Windows

1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer
3. Set a password for the `postgres` user (remember this!)
4. Default port: 5432
5. Add PostgreSQL to PATH (installer option)

### Verify Installation

```bash
psql --version
# Should show: psql (PostgreSQL) 15.x or later
```

---

## Step 2: Create Databases

### Connect to PostgreSQL

```bash
# Windows
psql -U postgres -h localhost

# You'll be prompted for the postgres password
```

### Create SPB Databases

```sql
-- Main operational database
CREATE DATABASE "BCSPB"
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Catalog database (message definitions)
CREATE DATABASE "BCSPBSTR"
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Verify databases were created
\l

-- Exit psql
\q
```

---

## Step 3: Configure Connection Settings

### SPBSite Configuration

Edit `spbsite/.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/BCSPB
CATALOG_DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/BCSPBSTR

# Replace YOUR_PASSWORD with your actual postgres password
```

### BCSrvSqlMq Configuration

Edit `BCSrvSqlMq/python/BCSrvSqlMq.ini`:

```ini
[Database]
DBServer=localhost
DBAliasName=BCSPBSTR
DBName=BCSPB
DBPort=5432
DBUserName=postgres
DBPassword=YOUR_PASSWORD
```

---

## Step 4: Initialize Database Schema

### For SPBSite

```bash
cd spbsite

# Run migrations to create tables
alembic upgrade head

# Seed initial data (creates admin user, message catalog)
python -m app.seed
```

### For BCSrvSqlMq

The database schema is shared via `spb-shared` models, so running SPBSite migrations creates all necessary tables.

---

## Step 5: Verify Database Setup

### Check Tables

```bash
# Connect to main database
psql -U postgres -d BCSPB

# List tables
\dt

# Should show:
# - spb_local_to_bacen
# - spb_local_to_selic
# - spb_bacen_to_local
# - spb_selic_to_local
# - spb_controle
# - spb_log_bacen
# - spb_log_selic
# - bacen_controle
# - users
# - fila
# - camaras

# Check catalog database
\c BCSPBSTR
\dt

# Should show:
# - spb_mensagem
# - spb_msg_field
# - spb_dicionario

# Exit
\q
```

---

## Step 6: Test Connection

### Test from Python

```python
import psycopg2

# Test main database
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='BCSPB',
    user='postgres',
    password='YOUR_PASSWORD'
)
print("Connected to BCSPB!")
conn.close()

# Test catalog database
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='BCSPBSTR',
    user='postgres',
    password='YOUR_PASSWORD'
)
print("Connected to BCSPBSTR!")
conn.close()
```

---

## Database Schema Overview

### BCSPB (Main Database)

**Message Tables:**
- `spb_local_to_bacen` - Outbound messages to BACEN
- `spb_local_to_selic` - Outbound messages to SELIC
- `spb_bacen_to_local` - Inbound messages from BACEN
- `spb_selic_to_local` - Inbound messages from SELIC

**Control Tables:**
- `spb_controle` - SPB system control
- `bacen_controle` - BACEN integration control

**Log Tables:**
- `spb_log_bacen` - BACEN transaction logs
- `spb_log_selic` - SELIC transaction logs

**Queue Tables:**
- `fila` - Queue definitions
- `camaras` - Clearing house definitions

**Auth Tables:**
- `users` - System users

### BCSPBSTR (Catalog Database)

**Message Catalog:**
- `spb_mensagem` - Message type definitions
- `spb_msg_field` - Message field definitions
- `spb_dicionario` - Data dictionary

---

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
# Windows:
sc query postgresql-x64-15

# Start if stopped:
net start postgresql-x64-15
```

### Password Authentication Failed

1. Verify password in `.env` and `BCSrvSqlMq.ini`
2. Check `pg_hba.conf` allows password authentication:
   ```
   # TYPE  DATABASE        USER            ADDRESS                 METHOD
   host    all             all             127.0.0.1/32            md5
   ```
3. Restart PostgreSQL after changes

### Database Does Not Exist

```bash
# List all databases
psql -U postgres -l

# Recreate if needed
psql -U postgres -c 'CREATE DATABASE "BCSPB";'
psql -U postgres -c 'CREATE DATABASE "BCSPBSTR";'
```

### Tables Not Created

```bash
# Run migrations
cd spbsite
alembic upgrade head

# Check for errors in output
```

---

## Backup and Restore

### Backup

```bash
# Backup BCSPB
pg_dump -U postgres -F c -f BCSPB_backup.dump BCSPB

# Backup BCSPBSTR
pg_dump -U postgres -F c -f BCSPBSTR_backup.dump BCSPBSTR
```

### Restore

```bash
# Restore BCSPB
pg_restore -U postgres -d BCSPB -c BCSPB_backup.dump

# Restore BCSPBSTR
pg_restore -U postgres -d BCSPBSTR -c BCSPBSTR_backup.dump
```

---

## Performance Tuning

### Create Indexes (if not auto-created by migrations)

```sql
-- Connect to BCSPB
\c BCSPB

-- Indexes for spb_local_to_bacen
CREATE INDEX IF NOT EXISTS ix1_spb_local_to_bacen ON spb_local_to_bacen(mq_msg_id);
CREATE INDEX IF NOT EXISTS ix2_spb_local_to_bacen ON spb_local_to_bacen(mq_qn_destino, flag_proc);
CREATE INDEX IF NOT EXISTS ix3_spb_local_to_bacen ON spb_local_to_bacen(nu_ope);

-- Indexes for spb_bacen_to_local
CREATE INDEX IF NOT EXISTS ix1_spb_bacen_to_local ON spb_bacen_to_local(nu_ope);
CREATE INDEX IF NOT EXISTS ix2_spb_bacen_to_local ON spb_bacen_to_local(flag_proc, mq_qn_origem);
```

---

## Migration from SQLite

If you have existing SQLite databases (`spbsite.db`, `spb_messages.db`), you need to migrate data:

### Export Data from SQLite

```bash
# Export tables to CSV
sqlite3 spbsite/spbsite.db <<EOF
.headers on
.mode csv
.output users.csv
SELECT * FROM users;
.output spb_local_to_bacen.csv
SELECT * FROM spb_local_to_bacen;
-- Repeat for other tables
EOF
```

### Import to PostgreSQL

```sql
-- Connect to BCSPB
\c BCSPB

-- Import users
COPY users FROM '/path/to/users.csv' CSV HEADER;

-- Import messages
COPY spb_local_to_bacen FROM '/path/to/spb_local_to_bacen.csv' CSV HEADER;
```

---

## Summary

1. Install PostgreSQL 15+
2. Create `BCSPB` and `BCSPBSTR` databases
3. Update `.env` and `BCSrvSqlMq.ini` with connection details
4. Run migrations: `alembic upgrade head`
5. Seed data: `python -m app.seed`
6. Test connection

Your SPB system is now running on PostgreSQL!
