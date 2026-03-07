# SPB System Monorepo - Projects Overview

Complete Brazilian Payment System (SPB) integration system for **Finvest DTVM** (ISPB 36266751).

---

## Repository Structure

```
Novo_SPB/
├── spb-shared/          # Shared database models package
├── spbsite/             # Web interface (FastAPI)
├── BCSrvSqlMq/          # Backend server (IBM MQ integration)
├── Carga_Mensageria/    # Message catalog ETL tool
├── MIGRATION_GUIDE.md
├── BCSRVSQLMQ_INTEGRATION.md
└── README.md
```

---

## Project 1: spb-shared - Shared Models Package

**Location:** `spb-shared/`
**Purpose:** Centralized SQLAlchemy models - single source of truth for database schema
**Technology:** Python 3.10+, SQLAlchemy 2.0, Alembic

### Key Features
- Single source of truth for database schema
- Supports PostgreSQL (production) and SQLite (development)
- Automatic migrations via Alembic
- Type-safe async ORM models

### Models Structure
```
spb_shared/models/
├── auth.py         # User authentication
├── catalog.py      # SPBMensagem, SPBMsgField, SPBDicionario
├── control.py      # SPBControle, BacenControle
├── logs.py         # SPBLogBacen, SPBLogSelic
├── messages.py     # SPBBacenToLocal, SPBSelicToLocal, etc.
└── queue.py        # Fila, Camaras
```

### Available Models
- **Messages:** `SPBBacenToLocal`, `SPBSelicToLocal`, `SPBLocalToBacen`, `SPBLocalToSelic`
- **Control:** `SPBControle`, `BacenControle`
- **Logs:** `SPBLogBacen`, `SPBLogSelic`
- **Catalog:** `SPBMensagem`, `SPBMsgField`, `SPBDicionario`
- **Queue:** `Fila`, `Camaras`
- **Auth:** `User`

### Installation
```bash
cd spb-shared
pip install -e .
```

### Dependencies
- sqlalchemy>=2.0.0
- asyncpg>=0.29.0
- aiosqlite>=0.19.0
- alembic>=1.13.0
- psycopg2-binary>=2.9.9

---

## Project 2: SPBSite - Web Interface

**Location:** `spbsite/`
**Purpose:** FastAPI web application for SPB message management
**Technology:** FastAPI, Jinja2, Bootstrap 5, SQLAlchemy Async

### Key Features
- User authentication and authorization
- Dynamic message form generation
- Real-time monitoring dashboard
- Message submission and tracking
- Queue management
- System logs viewer
- XML message viewer

### App Structure
```
app/
├── routers/           # API endpoints
│   ├── auth.py       # Login/logout
│   ├── messages.py   # Message submission
│   ├── monitoring.py # Dashboard
│   ├── queue.py      # Queue management
│   ├── logs.py       # Log viewing
│   └── viewer.py     # XML viewer
├── services/          # Business logic
│   ├── form_engine.py    # Dynamic form generation
│   ├── xml_builder.py    # XML message builder
│   ├── monitoring.py     # Stats & metrics
│   └── queue_manager.py  # Queue operations
├── schemas/          # Pydantic models
├── templates/        # Jinja2 HTML templates
├── static/          # CSS, JS, images
├── main.py          # FastAPI application
├── database.py      # Database configuration
├── config.py        # App configuration
└── seed.py          # Database seeding
```

### Running
```bash
cd spbsite
pip install -r requirements.txt
pip install -e ../spb-shared

# Seed database
python -m app.seed

# Run server
uvicorn app.main:app --reload --port 8000
```

### Access
- **URL:** http://localhost:8000
- **Default Login:** admin / admin

### Dependencies
- fastapi
- uvicorn
- jinja2
- python-multipart
- sqlalchemy[asyncio]
- aiosqlite
- asyncpg
- bcrypt

---

## Project 3: BCSrvSqlMq - Backend Message Queue Server

**Location:** `BCSrvSqlMq/`
**Purpose:** IBM MQ integration service for SPB message routing
**Technology:** Python 3.10+, IBM MQ Client, psycopg2, Windows Service

### Key Features
- IBM MQ queue management (8 queues: 4 local + 4 remote)
- Message routing (BACEN ↔ SELIC ↔ Finvest)
- PostgreSQL data persistence
- Message acknowledgment tracking
- Windows Service support
- Security (OpenSSL wrapper for message signing)

### Python Module Structure
```
bcsrvsqlmq/
├── bacen_req.py      # BACEN Request handler
├── bacen_rsp.py      # BACEN Response handler
├── bacen_rep.py      # BACEN Report handler
├── bacen_sup.py      # BACEN Support handler
├── if_req.py         # SELIC Request handler
├── if_rsp.py         # SELIC Response handler
├── if_rep.py         # SELIC Report handler
├── if_sup.py         # SELIC Support handler
├── thread_mq.py      # IBM MQ thread manager
├── monitor.py        # System monitoring
├── msg_sgr.py        # Message security/signing
├── init_srv.py       # Service initialization
├── main_srv.py       # Main service entry point
├── nt_service.py     # Windows service wrapper
├── security/         # OpenSSL wrappers
└── db/               # Database recordsets
    ├── bacen_app_rs.py   # BACEN message recordset
    ├── if_app_rs.py      # SELIC message recordset
    ├── controle_rs.py    # Control table recordset
    └── str_log_rs.py     # Log recordset
```

### IBM MQ Configuration
- **Queue Manager:** QM.36266751.01
- **ISPB Finvest:** 36266751
- **ISPB BACEN:** 00038166
- **ISPB SELIC:** 00038121
- **Port:** 1414
- **Channel:** FINVEST.SVRCONN

### Queue Architecture

**Local Queues (4) - Messages FROM Bacen TO Finvest:**
- `QL.REQ.00038166.36266751.01` - BACEN Request to Finvest
- `QL.RSP.00038166.36266751.01` - BACEN Response to Finvest
- `QL.REP.00038166.36266751.01` - BACEN Report to Finvest
- `QL.SUP.00038166.36266751.01` - BACEN Support to Finvest

**Remote Queues (4) - Messages FROM Finvest TO Bacen:**
- `QR.REQ.36266751.00038166.01` - Finvest Request to BACEN
- `QR.RSP.36266751.00038166.01` - Finvest Response to BACEN
- `QR.REP.36266751.00038166.01` - Finvest Report to BACEN
- `QR.SUP.36266751.00038166.01` - Finvest Support to BACEN

### Running
```bash
cd BCSrvSqlMq/python
pip install -r requirements.txt
pip install -e ../../spb-shared

# Configure
cp ../BCSrvSqlMq.ini.example ../BCSrvSqlMq.ini
# Edit BCSrvSqlMq.ini with your settings

# Run
python -m bcsrvsqlmq.main_srv
```

### IBM MQ Setup
Run the automated setup script as Administrator:
```cmd
cd BCSrvSqlMq
setup_mq_36266751.cmd
```

See [IBM_MQ_SETUP_GUIDE.md](BCSrvSqlMq/IBM_MQ_SETUP_GUIDE.md) for detailed instructions.

### Dependencies
- pymqi>=1.12.0
- psycopg2-binary>=2.9.0
- cryptography>=41.0.0
- lxml>=4.9.0
- pywin32>=306

---

## Project 4: Carga_Mensageria - Message Catalog ETL Tool

**Location:** `Carga_Mensageria/`
**Purpose:** ETL tool for SPB message catalog processing
**Technology:** Python 3.8+, SQLite, Tkinter (GUI), XML/XSL

### Key Features
- Import SPB message catalogs from XSD schemas or Access (.mdb) files
- Generate normalized database tables
- Create XML/XSL schemas for message forms
- Generate HTML reference documentation
- Process 12 ETL steps (0A → C)

### Main Files
```
Carga_Mensageria/
├── main.py               # Tkinter GUI entry point
├── etapas.py             # ETL business logic (12 steps)
├── db_connection.py      # SQLite connection manager
├── init_database.py      # Schema creation
├── import_from_xsd.py    # Import from XSD schemas
├── import_from_mdb.py    # Import from Access files
├── xml_generator.py      # XML/XSL generation
├── spbmodelo.xsl         # XSL template
├── emissor.txt           # Valid entity types
├── spb_schemas.zip       # BCB XSD schemas
└── BCSPBSTR.db          # Output SQLite database
```

### ETL Steps

#### Configuration Steps (0A-0)
| Step | Description | Output Table |
|------|-------------|--------------|
| **0A** | Load operation grades | `PLAN_Grade` |
| **0**  | Associate messages to grades | `PLAN_Grade_X_Msg` |

#### Table Generation Steps (1-5)
| Step | Description | Output Table |
|------|-------------|--------------|
| **1**  | Generate grade codes with ISPB routing | `SPB_CODGRADE` |
| **2**  | Map grade × message × destination | `APP_CODGRADE_X_MSG` |
| **3**  | Consolidate message catalog | `SPB_MENSAGEM` |
| **4**  | Generate data dictionary | `SPB_DICIONARIO` |
| **5**  | Denormalize message field structure | `SPB_MSGFIELD` |

#### Artifact Generation Steps (A-C)
| Step | Description | Output |
|------|-------------|--------|
| **A**  | Generate XML/XSL schemas | `SPB_XMLXSL` table |
| **B**  | Generate domain HTML files | `*.htm` files |
| **C**  | Generate ISPB registry HTML | `ISPB.htm` |

### Data Model

**Input Tables (populated via import):**
- `PLAN_MENSAGEM` - SPB message catalog
- `PLAN_EVENTO` - Event descriptions
- `PLAN_DADOS` - Field dictionary (tags)
- `PLAN_TIPOLOGIA` - Type definitions
- `PLAN_Mensagem_Dados` - Message field structure
- `SPB_DOMINIOS` - Domain value lists
- `SPB_ISPB` - Institution registry (ISPB codes)

**Output Tables (generated by ETL):**
- `PLAN_Grade` / `PLAN_Grade_X_Msg` - Grade configuration
- `SPB_CODGRADE` - Grades with ISPB routing
- `APP_CODGRADE_X_MSG` - Grade × message × destination mapping
- `SPB_MENSAGEM` - Consolidated message catalog
- `SPB_DICIONARIO` - Consolidated data dictionary
- `SPB_MSGFIELD` - Denormalized field structure
- `SPB_XMLXSL` - Generated XML/XSL schemas

### Usage
```bash
# Initialize database
python init_database.py

# Import from XSD schemas (recommended)
python import_from_xsd.py

# OR import from Access files (legacy)
python import_from_mdb.py

# Run GUI
python main.py
```

### Configuration
- **Default ISPB:** 61377677 (Banco Cidade - default sender)
- **Output DB:** BCSPBSTR.db (SQLite)

---

## System Integration Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│   SPBSite (Web UI)  │────────▶│    spb-shared       │
│   FastAPI:8000      │         │  (Shared Models)    │
│   - Message Forms   │         │  - SQLAlchemy ORM   │
│   - Monitoring      │         │  - Alembic          │
│   - Queue Mgmt      │         └─────────────────────┘
└─────────────────────┘                    ▲
         │                                 │
         │ Database                        │ Database
         │ Operations                      │ Operations
         ▼                                 │
┌─────────────────────┐         ┌─────────────────────┐
│  PostgreSQL/SQLite  │◀────────│   BCSrvSqlMq        │
│  - spbsite DB       │         │  (MQ Service)       │
│  - spb_messages DB  │         │  - Message Routing  │
│  (Development)      │         │  - Persistence      │
└─────────────────────┘         │  - Acknowledgments  │
                                └─────────────────────┘
                                         │
                                         │ IBM MQ
                                         │ Protocol
                                         ▼
                                ┌─────────────────────┐
                                │      IBM MQ         │
                                │  QM.36266751.01     │
                                │  - 8 Queues         │
                                │  - REQ/RSP/REP/SUP  │
                                │  - Port 1414        │
                                └─────────────────────┘
                                         │
                                         │ Network
                                         ▼
                                ┌─────────────────────┐
                                │    BACEN / SELIC    │
                                │    SPB Network      │
                                └─────────────────────┘

         ┌─────────────────────┐
         │  Carga_Mensageria   │  (Standalone ETL)
         │  (Message Catalog)  │
         │  - Import from XSD  │
         │  - Generate Schemas │
         │  - Create HTML Docs │
         └─────────────────────┘
                  │
                  ▼
         ┌─────────────────────┐
         │    BCSPBSTR.db      │
         │  (Catalog Database) │
         └─────────────────────┘
```

---

## Quick Start Guide

### Prerequisites
- Python 3.10 or higher
- PostgreSQL 15+ (production) or SQLite (development)
- IBM MQ Client 9.x (for BCSrvSqlMq)
- Git

### Setup All Projects

```bash
# 1. Install shared models (required for all projects)
cd spb-shared
pip install -e .

# 2. Setup SPBSite
cd ../spbsite
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000 &

# 3. Setup BCSrvSqlMq
cd ../BCSrvSqlMq/python
pip install -r requirements.txt
cp ../BCSrvSqlMq.ini.example ../BCSrvSqlMq.ini
# Edit BCSrvSqlMq.ini with your settings
python -m bcsrvsqlmq.main_srv &

# 4. (Optional) Setup IBM MQ queues
cd ..
# Run as Administrator
setup_mq_36266751.cmd

# 5. (Optional) Run Carga_Mensageria
cd ../Carga_Mensageria
python init_database.py
python import_from_xsd.py
python main.py
```

---

## Database Configuration

### Development (SQLite)

**SPBSite** `.env`:
```bash
DATABASE_URL=sqlite+aiosqlite:///./spbsite.db
CATALOG_DATABASE_URL=sqlite+aiosqlite:///./spb_messages.db
SECRET_KEY=your-secret-key-here
ISPB_LOCAL=36266751
ISPB_BACEN=00038166
ISPB_SELIC=00038121
```

### Production (PostgreSQL)

**SPBSite** `.env`:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/spbsite
CATALOG_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/spb_messages
SECRET_KEY=your-secret-key-here
ISPB_LOCAL=36266751
ISPB_BACEN=00038166
ISPB_SELIC=00038121
```

**BCSrvSqlMq** `BCSrvSqlMq.ini`:
```ini
[Database]
Server=localhost
Port=5432
Database=spbsite
User=postgres
Password=password
```

---

## Database Schema Synchronization

All projects share the same database schema via the `spb-shared` package.

### Making Schema Changes

1. Edit models in `spb-shared/spb_shared/models/`
2. Create migration:
   ```bash
   cd spb-shared
   alembic revision --autogenerate -m "Description"
   alembic upgrade head
   ```
3. Apply to other projects:
   ```bash
   cd ../spbsite
   alembic upgrade head

   cd ../BCSrvSqlMq
   alembic upgrade head
   ```

---

## Testing

### SPBSite Tests
```bash
cd spbsite
pytest tests/ -v
# Expected: 89 tests passing
```

### BCSrvSqlMq Tests
```bash
cd BCSrvSqlMq/python
pytest tests/ -v
```

---

## Documentation

- [README.md](README.md) - Main repository documentation
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Database migration instructions
- [BCSRVSQLMQ_INTEGRATION.md](BCSRVSQLMQ_INTEGRATION.md) - Backend integration guide
- [IBM_MQ_SETUP_GUIDE.md](BCSrvSqlMq/IBM_MQ_SETUP_GUIDE.md) - MQ configuration guide
- [MESSAGE_FLOWS.md](BCSrvSqlMq/MESSAGE_FLOWS.md) - Message flow documentation
- [MQ_QUICK_REFERENCE.md](BCSrvSqlMq/MQ_QUICK_REFERENCE.md) - MQ quick reference
- [HSM_Guide.pdf](HSM_Guide.pdf) - HSM documentation
- [CONVERSATION_SUMMARY_2026-03-07.md](CONVERSATION_SUMMARY_2026-03-07.md) - Recent changes

---

## Security Features

- Session-based authentication
- Password hashing with bcrypt
- CSRF protection
- SQL injection prevention via ORM
- Input validation on all forms
- OpenSSL message signing (BCSrvSqlMq)

**Default Credentials** (Change in production!):
- Username: `admin`
- Password: `admin`

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (Async) |
| Database | PostgreSQL / SQLite |
| Message Queue | IBM MQ |
| Template Engine | Jinja2 |
| Frontend | Bootstrap 5 |
| Authentication | Session-based |
| Migrations | Alembic |
| Message Security | OpenSSL |

---

## ISPB Codes Reference

| Entity | ISPB Code |
|--------|-----------|
| Finvest DTVM | 36266751 |
| Banco Central (BACEN) | 00038166 |
| SELIC | 00038121 |
| Banco Cidade (Legacy) | 61377677 |

---

## Contributing

1. Create feature branch
2. Make changes in appropriate project
3. If schema changes: update `spb-shared` models first
4. Run tests
5. Create pull request

---

## License

Proprietary - Finvest DTVM

---

## Authors

- Finvest DTVM Development Team
- Built with assistance from Claude (Anthropic)

---

## Support

For issues or questions, contact the Finvest DTVM IT team.

---

**Version:** 1.0.0
**Last Updated:** March 7, 2026
**Repository:** Novo_SPB Monorepo
