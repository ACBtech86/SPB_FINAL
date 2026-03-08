# SPB System Documentation

Complete documentation for the Brazilian Payment System (SPB) integration system.

---

## 📚 Documentation Index

### 🚀 Getting Started

Start here if you're new to the SPB system:

- **[PROJECTS_OVERVIEW.md](PROJECTS_OVERVIEW.md)** - Complete system overview and architecture
- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Full installation guide for all components
- **[QUICK_INSTALL.md](QUICK_INSTALL.md)** - Quick installation for development

### ⚙️ Setup & Configuration

- **[PYTHON312_SETUP.md](PYTHON312_SETUP.md)** - Python 3.12 environment setup
- **[POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)** - PostgreSQL database configuration
- **[IBM_MQ_SETUP.md](IBM_MQ_SETUP.md)** - IBM MQ installation and setup
- **[VSCODE_GUIDE.md](VSCODE_GUIDE.md)** - VS Code workspace configuration
- **[UBUNTU_DEPLOYMENT_GUIDE.md](UBUNTU_DEPLOYMENT_GUIDE.md)** - Ubuntu Server deployment with VS Code Remote

### 🔧 Integration & Backend

- **[BCSRVSQLMQ_INTEGRATION.md](BCSRVSQLMQ_INTEGRATION.md)** - BCSrvSqlMq integration guide
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Database migration procedures

### ✅ Testing & Validation

- **[E2E_TEST_PLAN.md](E2E_TEST_PLAN.md)** - End-to-end test plan
- **[END_TO_END_TEST_REPORT.md](END_TO_END_TEST_REPORT.md)** - E2E test results
- **[FULL_INTEGRATION_TEST.md](FULL_INTEGRATION_TEST.md)** - Full integration test documentation
- **[INTEGRATION_SUCCESS_REPORT.md](INTEGRATION_SUCCESS_REPORT.md)** - Integration success report
- **[ARCHITECTURE_VERIFICATION.md](ARCHITECTURE_VERIFICATION.md)** - Architecture validation

### 📊 Project Management

- **[PROJECT_CLEANUP_SUMMARY.md](PROJECT_CLEANUP_SUMMARY.md)** - Project cleanup summary

---

## Quick Links

### By Role

**🆕 New Developer:**
1. [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - Install everything
2. [PROJECTS_OVERVIEW.md](PROJECTS_OVERVIEW.md) - Understand the system
3. [VSCODE_GUIDE.md](VSCODE_GUIDE.md) - Setup your IDE

**🖥️ DevOps / Sysadmin:**
1. [UBUNTU_DEPLOYMENT_GUIDE.md](UBUNTU_DEPLOYMENT_GUIDE.md) - Deploy on Ubuntu Server
2. [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) - Configure database
3. [IBM_MQ_SETUP.md](IBM_MQ_SETUP.md) - Setup message queue

**🧪 QA / Tester:**
1. [E2E_TEST_PLAN.md](E2E_TEST_PLAN.md) - Test plan
2. [FULL_INTEGRATION_TEST.md](FULL_INTEGRATION_TEST.md) - Integration testing
3. [END_TO_END_TEST_REPORT.md](END_TO_END_TEST_REPORT.md) - Test results

---

## System Components

### Main Projects
- **spb-shared** - Shared database models (SQLAlchemy)
- **spbsite** - Web interface (FastAPI)
- **BCSrvSqlMq** - Message queue service (IBM MQ integration)
- **Carga_Mensageria** - Message catalog ETL tool

### Technologies
- Python 3.10+
- PostgreSQL 15+
- FastAPI
- IBM MQ
- SQLAlchemy 2.0 (Async)
- Alembic

---

## Support

For questions or issues, contact the Finvest DTVM IT team.

**Last Updated:** March 8, 2026
