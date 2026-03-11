# SPB System - Brazilian Payment System Integration

Monorepo containing complete SPB (Sistema de Pagamentos Brasileiro) integration system for Finvest DTVM.

## 🏗️ Repository Structure

```
Novo_SPB/
├── Docs/                # 📚 Complete documentation
├── spb-shared/          # Shared database models package
├── spbsite/             # Web interface (FastAPI)
├── BCSrvSqlMq/          # Backend server (IBM MQ integration)
├── Carga_Mensageria/    # Message catalog ETL tool
└── README.md            # This file
```

**📖 Full Documentation:** See [Docs/](Docs/) folder or start with [PROJECTS_OVERVIEW.md](Docs/PROJECTS_OVERVIEW.md)

## 📦 Projects

### 1. spb-shared - Shared Models Package

Centralized SQLAlchemy models ensuring schema synchronization between all projects.

**Technology**: Python 3.10+, SQLAlchemy 2.0, Alembic

**Key Features**:
- Single source of truth for database schema
- PostgreSQL database support
- Automatic migrations via Alembic
- Type-safe ORM models

**Installation**:
```bash
cd spb-shared
pip install -e .
```

**Models**:
- Messages: `SPBBacenToLocal`, `SPBSelicToLocal`, `SPBLocalToBacen`, `SPBLocalToSelic`
- Control: `SPBControle`, `BacenControle`
- Logs: `SPBLogBacen`, `SPBLogSelic`
- Catalog: `SPBMensagem`, `SPBMsgField`, `SPBDicionario`
- Queue: `Fila`, `Camaras`
- Auth: `User`

### 2. SPBSite - Web Interface

FastAPI web application for SPB message management and monitoring.

**Technology**: FastAPI, Jinja2, Bootstrap 5, SQLAlchemy Async

**Features**:
- ✅ User authentication and authorization
- ✅ Dynamic message form generation
- ✅ Real-time monitoring dashboard
- ✅ Message submission and tracking
- ✅ Queue management
- ✅ System logs viewer
- ✅ XML message viewer

**Installation**:
```bash
cd spbsite
pip install -r requirements.txt
pip install -e ../spb-shared

# Seed database
python -m app.seed

# Run server
uvicorn app.main:app --reload --port 8000
```

**Access**: http://localhost:8000
**Default Login**: `admin` / `admin`

### 3. BCSrvSqlMq - Backend Server

C++/Python hybrid service for IBM MQ message queue integration with SPB.

**Technology**: Python 3.10+, psycopg2, IBM MQ Client

**Features**:
- ✅ IBM MQ queue management
- ✅ Message routing (BACEN/SELIC)
- ✅ PostgreSQL data persistence
- ✅ Message acknowledgment tracking
- ✅ Windows Service support

**Installation**:
```bash
cd BCSrvSqlMq/python
pip install -r requirements.txt
pip install -e ../../spb-shared

# Configure
cp BCSrvSqlMq.ini.example BCSrvSqlMq.ini
# Edit BCSrvSqlMq.ini with your settings

# Run
python -m bcsrvsqlmq.main_srv
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10 - 3.12** (3.13 not compatible with pymqi - see [PYTHON312_SETUP.md](Docs/PYTHON312_SETUP.md))
- PostgreSQL 15+
- IBM MQ Client 9.x (for BCSrvSqlMq)
- Git
- Visual Studio 2022 with C++ tools (for pymqi compilation)

### Setup All Projects

```bash
# Clone repository
git clone <repository-url>
cd Novo_SPB

# Install shared models
cd spb-shared
pip install -e .

# Setup SPBSite
cd ../spbsite
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000 &

# Setup BCSrvSqlMq
cd ../BCSrvSqlMq/python
pip install -r requirements.txt
cp ../BCSrvSqlMq.ini.example ../BCSrvSqlMq.ini
# Configure BCSrvSqlMq.ini
python -m bcsrvsqlmq.main_srv
```

## 🔄 Database Schema Synchronization

All projects share the same database schema via `spb-shared` package.

**Making Schema Changes**:

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

## 📊 Database Configuration

### PostgreSQL Setup

```bash
# spbsite/.env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/BCSPB
CATALOG_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/BCSPBSTR

# BCSrvSqlMq.ini
[Database]
Server=localhost
Port=5432
Database=BCSPB
DBAliasName=BCSPBSTR
User=postgres
Password=password
```

## 🧪 Testing

```bash
# SPBSite tests
cd spbsite
pytest tests/ -v

# Expected: 89 tests passing
```

## 📚 Documentation

**📁 Complete Documentation:** [Docs/](Docs/) folder

**Quick Links:**
- **[Projects Overview](Docs/PROJECTS_OVERVIEW.md)** - Complete system architecture and overview
- **[Installation Guide](Docs/INSTALLATION_GUIDE.md)** - Full installation instructions
- **[Quick Install](Docs/QUICK_INSTALL.md)** - Quick setup for development
- **[Ubuntu Deployment](Docs/UBUNTU_DEPLOYMENT_GUIDE.md)** - Deploy on Ubuntu Server with VS Code Remote
- **[Migration Guide](Docs/MIGRATION_GUIDE.md)** - Database migration instructions
- **[BCSrvSqlMq Integration](Docs/BCSRVSQLMQ_INTEGRATION.md)** - Backend integration guide
- **[IBM MQ Setup](BCSrvSqlMq/IBM_MQ_SETUP_GUIDE.md)** - MQ configuration guide

**See [Docs/README.md](Docs/README.md) for complete documentation index.**

## 🔐 Security

- Session-based authentication
- Password hashing with bcrypt
- CSRF protection
- SQL injection prevention via ORM
- Input validation on all forms

**Default Credentials** (⚠️ Change in production):
- Username: `admin`
- Password: `admin`

## 🏢 System Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   SPBSite   │────────▶│  spb-shared  │◀────────│ BCSrvSqlMq  │
│  (FastAPI)  │         │   (Models)   │         │  (MQ Srv)   │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │                        │
      └────────────────────────┼────────────────────────┘
                               ▼
                        ┌──────────────┐         ┌─────────────┐
                        │  PostgreSQL  │         │    IBM MQ   │
                        │    BCSPB     │         │             │
                        └──────────────┘         └─────────────┘
```

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (Async) |
| Database | PostgreSQL |
| Message Queue | IBM MQ |
| Template Engine | Jinja2 |
| Frontend | Bootstrap 5 |
| Authentication | Session-based |
| Migrations | Alembic |

## 📝 Configuration

### Environment Variables (SPBSite)

```bash
# .env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/BCSPB
CATALOG_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/BCSPBSTR
SECRET_KEY=your-secret-key-here
ISPB_LOCAL=36266751
ISPB_BACEN=00038166
ISPB_SELIC=00038121
```

### BCSrvSqlMq Configuration

See `BCSrvSqlMq/BCSrvSqlMq.ini.example`

## 🤝 Contributing

1. Create feature branch
2. Make changes in appropriate project
3. If schema changes: update `spb-shared` models
4. Run tests
5. Create pull request

## 📄 License

Proprietary - Finvest DTVM

## 👥 Authors

- Finvest DTVM Development Team
- Built with assistance from Claude (Anthropic)

## 📞 Support

For issues or questions, contact the Finvest DTVM IT team.

---

**Version**: 1.0.0  
**Last Updated**: March 2026
