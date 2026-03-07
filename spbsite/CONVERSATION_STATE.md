# SPBSite Conversion — Conversation State

Saved: 2026-03-02

---

## Project Summary

Classic ASP (VBScript/JScript) application for Brazil's SPB (Sistema de Pagamentos Brasileiro) converted to Python/FastAPI.

**Original stack**: IIS + SQL Server + MSXML/XSL + IE 4/5
**New stack**: FastAPI + SQLAlchemy async + SQLite (dev) / PostgreSQL (prod) + Jinja2 + SessionMiddleware

**Original DB**: `BCSPBSTR` on `SRVCX077` (SQL Server, `SA`/`SQLADM`)

---

## What's Done

### Phase 1–9: Full conversion complete

- **48 files created** in `app/` and `tests/`
- **89 test cases** — all passing
- **10 message types** seeded with field definitions
- Original ASP code moved to `OLD/` folder

### Project Structure

```
spbsite/
├── OLD/                          ← original ASP code (spbsite_Local, .sln, .suo, .vic, .vip)
├── app/
│   ├── __init__.py
│   ├── main.py                   ← FastAPI app, SessionMiddleware, AuthRequired handler, routers
│   ├── config.py                 ← pydantic-settings (DATABASE_URL, SECRET_KEY, ISPB constants)
│   ├── database.py               ← async SQLAlchemy engine + get_db dependency
│   ├── dependencies.py           ← AuthRequired exception + get_current_user
│   ├── seed.py                   ← Creates tables, seeds admin user + message data
│   ├── models/
│   │   ├── auth.py               ← User (id, username, password_hash, is_active)
│   │   ├── control.py            ← SPBControle, BacenControle
│   │   ├── messages.py           ← SPBBacenToLocal, SPBSelicToLocal, SPBLocalToBacen, SPBLocalToSelic
│   │   ├── logs.py               ← SPBLogBacen, SPBLogSelic
│   │   ├── catalog.py            ← SPBMensagem, SPBMsgField, SPBDicionario, SPBXmlXsl
│   │   └── queue.py              ← Fila, Camaras
│   ├── routers/
│   │   ├── auth.py               ← GET/POST /login, GET /logout
│   │   ├── monitoring.py         ← GET /monitoring/control/{channel}, /messages/{direction}/{channel}
│   │   ├── logs.py               ← GET /logs/{channel}
│   │   ├── messages.py           ← GET /messages/select, /form/{msg_id}, POST /submit
│   │   ├── queue.py              ← GET /queue, POST /queue/process, GET /queue/message/{seq}
│   │   └── viewer.py             ← GET /viewer/{table}/{record_id} (ALLOWED_TABLES whitelist)
│   ├── services/
│   │   ├── monitoring.py         ← get_control_data(), get_messages(), get_logs()
│   │   ├── xml_builder.py        ← build_spb_xml(), submit_message(), _convert_date/time
│   │   ├── form_engine.py        ← load_form(), validate_form(), get_message_types()
│   │   ├── queue_manager.py      ← get_pending_messages(), process_selected()
│   │   ├── xml_utils.py          ← parse_xml(), xml_to_tree(), format_datetime_br(), format_currency_br()
│   │   └── operation_number.py   ← generate_operation_number() (thread-safe, 23 chars)
│   ├── templates/                ← Jinja2 templates (base, auth, monitoring, messages, queue)
│   └── static/                   ← CSS + JS (style.css, app.js)
├── tests/
│   ├── conftest.py               ← SQLite in-memory, 10+ fixtures
│   ├── test_auth.py              ← 14 tests (Section 1)
│   ├── test_monitoring.py        ← 27 tests (Sections 2 + 7.1 + 7.2)
│   ├── test_logs.py              ← 5 tests (Section 3)
│   ├── test_messages.py          ← 24 tests (Sections 4 + 7.3 + 7.4 + 7.5)
│   ├── test_queue.py             ← 10 tests (Section 5 + 7.5)
│   └── test_viewer.py            ← 9 tests (Section 6)
├── TEST_PLAN.md                  ← 89 test cases documented
├── .env                          ← DATABASE_URL=sqlite+aiosqlite:///./spbsite.db
├── .env.example
├── pyproject.toml                ← asyncio_mode = "auto"
└── requirements.txt
```

### Key Configuration

- `.env` uses **SQLite** for local dev: `DATABASE_URL=sqlite+aiosqlite:///./spbsite.db`
- For production PostgreSQL: `DATABASE_URL=postgresql+asyncpg://postgres:Rama1248@localhost:5432/spbsite`
- SECRET_KEY: `Rama8421$`
- ISPB: local=61377677, BACEN=00038166, SELIC=00038121
- Admin login: `admin` / `admin`

### Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Seed database (creates tables + admin user + sample data)
python -m app.seed

# Run server
uvicorn app.main:app --reload --port 8000

# Run tests (89 tests, all passing)
pytest tests/ -v
```

---

## Current Issue — PENDING

### Seed data is wrong for SPB_MENSAGEM, SPB_MSGFIELD, SPB_DICIONARIO

The user said: **"The message, fields and dictionary are wrong"**

**Root cause**: The actual message definitions, field definitions, and dictionary data live in the original SQL Server database (`BCSPBSTR` on server `SRVCX077`). The seed data I created was an approximation based on the SPBDOC.dtd file, but it doesn't match the real data.

**What needs to happen**: The correct data needs to be exported from the original SQL Server and imported into the seed script. The 3 tables are:

1. **SPB_MENSAGEM** — Message catalog (MSG_ID, MSG_DESCR)
2. **SPB_MSGFIELD** — Field definitions per message (COD_GRADE, MSG_ID, MSG_TAG, MSG_DESCR, MSG_EMISSOR, MSG_DESTINATARIO, MSG_SEQ, MSG_CPOTAG, MSG_CPONOME, MSG_CPOOBRIG)
3. **SPB_DICIONARIO** — Field type dictionary (MSG_CPOTAG, MSG_CPOTIPO, MSG_CPOTAM, MSG_CPOFORM)

**Options to fix**:
- Export from original SQL Server (`Provider=SQLOLEDB;Initial Catalog=BCSPBSTR;Data Source=SRVCX077;uid=SA;pwd=SQLADM`)
- User provides data files (CSV, SQL dump, Excel)
- Build an import script that reads from SQL Server and writes to SQLite

The SQL query used by the original ASP to load fields:
```sql
SELECT FLD.COD_GRADE, FLD.MSG_ID, FLD.MSG_TAG, FLD.MSG_DESCR, FLD.MSG_EMISSOR,
       FLD.MSG_DESTINATARIO, FLD.MSG_SEQ, FLD.MSG_CPOTAG, FLD.MSG_CPONOME,
       FLD.MSG_CPOOBRIG, DIC.MSG_CPOTIPO, DIC.MSG_CPOTAM, DIC.MSG_CPOFORM
FROM SPB_MSGFIELD AS FLD
LEFT JOIN SPB_DICIONARIO AS DIC ON FLD.MSG_CPOTAG=DIC.MSG_CPOTAG
WHERE FLD.MSG_ID = '[MessageID]'
ORDER BY FLD.MSG_ID, FLD.MSG_SEQ
```

---

## Bugs Fixed During Development

1. **`render_tree` macro missing** in `viewer.html` — added Jinja2 recursive macro
2. **`expire_all()` called with `await`** — it's sync on AsyncSession
3. **Lazy-load after expire** — captured seq IDs as plain `int` before expiring
4. **dependencies.py redirect** — created AuthRequired exception + handler in main.py
5. **No PostgreSQL for dev** — switched .env to SQLite

---

## Key Technical Details

- **COD_GRADE routing**: `SEL01` → SELIC (ISPB 00038121), anything else → BACEN (ISPB 00038166)
- **Operation number**: 23 chars = ISPB(8) + YYYYMMDD(8) + sequence(7)
- **MQ queue names**: `QR.REQ.{source}.{dest}.01` (requests) / `QR.RSP.{source}.{dest}.01` (responses)
- **Status colors**: N=green (#DDFFDD), I/P=yellow (#FFFFBB), E/R=red (#FFBBBB)
- **Date format**: Brazilian `dd/mm/yyyy.HH:MM:SS` from stored `AAAAMMDDHHMMSS`
- **Currency format**: Brazilian `X.XXX,XX`
- **Field types in form engine**: `Grupo_*` opens fieldset, `/Grupo_*` closes, `Repet_*` for repeating groups
- **ALLOWED_TABLES whitelist** in viewer.py: spb_bacen_to_local, spb_selic_to_local, spb_local_to_bacen, spb_local_to_selic, fila
