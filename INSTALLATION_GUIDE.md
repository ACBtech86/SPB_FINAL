# SPB System Installation Guide
**Version**: 1.0
**Date**: March 8, 2026
**Status**: Production Ready

---

## Overview

This guide provides complete instructions for installing the SPB (Sistema de Pagamentos Brasileiro) system on a clean machine. Two automated installation scripts are provided:

- **install_spb_system.ps1** - For Windows 10/11 Pro
- **install_spb_system.sh** - For Linux (Ubuntu/Debian/RHEL)

Both scripts automate the installation of all required components and dependencies.

---

## Prerequisites

### Hardware Requirements
- **CPU**: x64 (64-bit) processor
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk**: Minimum 20GB free space
- **Network**: Internet connection for downloads

### Windows Requirements
- Windows 10/11 Pro (64-bit)
- Administrator privileges
- PowerShell 5.1 or later
- Execution policy allowing scripts

### Linux Requirements
- Ubuntu 20.04+, Debian 11+, or RHEL 8+ (64-bit)
- Root or sudo privileges
- Bash shell
- Internet connection

---

## Quick Start

### Windows Installation

1. **Open PowerShell as Administrator**
   ```powershell
   # Right-click PowerShell -> Run as Administrator
   ```

2. **Enable script execution (if needed)**
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Run the installation script**
   ```powershell
   cd "C:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\Novo_SPB"
   .\install_spb_system.ps1
   ```

4. **With custom options**
   ```powershell
   # Custom installation directory
   .\install_spb_system.ps1 -InstallDir "D:\SPB"

   # Skip IBM MQ (install manually later)
   .\install_spb_system.ps1 -SkipIBMMQ

   # Skip PostgreSQL (if already installed)
   .\install_spb_system.ps1 -SkipPostgreSQL
   ```

### Linux Installation

1. **Make script executable**
   ```bash
   chmod +x install_spb_system.sh
   ```

2. **Run as root**
   ```bash
   sudo ./install_spb_system.sh
   ```

3. **With custom options**
   ```bash
   # Custom installation directory
   sudo ./install_spb_system.sh --install-dir /opt/spb

   # Skip IBM MQ
   sudo ./install_spb_system.sh --skip-ibmmq

   # View all options
   ./install_spb_system.sh --help
   ```

---

## What Gets Installed

### 1. Core Components

#### Python 3.12.9 (64-bit)
- **Windows**: Downloaded from python.org
- **Linux**: Installed from distribution repository
- **Verification**: Ensures 64-bit architecture
- **Location**: System-wide installation

#### PostgreSQL 16
- **Databases Created**:
  - `BCSPB` - Main production database
  - `BCSPBSTR` - Catalog database
  - `BCSPB_TEST` - Testing database
- **Port**: 5432 (default)
- **User**: postgres
- **Password**: postgres (change this!)

#### IBM MQ 9.3
- **Queue Manager**: QM.36266751.01
- **Queues**: 8 local queues for SPB messaging
- **Note**: Manual installation may be required

### 2. SPB Application Components

#### SPBSite (Web Frontend)
- FastAPI web application
- Jinja2 templates
- Static assets (CSS/JS)
- API routes for SPB operations
- **Port**: 8000

#### spb-shared (Shared Models)
- SQLAlchemy ORM models
- Database schema definitions
- Installed as editable Python package
- Shared across all projects

#### BCSrvSqlMq (Backend Service)
- Message queue processor
- IBM MQ integration
- Database operations
- Background service

### 3. Python Dependencies

All dependencies from requirements.txt:
- **Web Framework**: FastAPI, uvicorn
- **Database**: SQLAlchemy, asyncpg, psycopg2-binary
- **IBM MQ**: pymqi (if available)
- **Security**: passlib, bcrypt==3.2.2
- **Testing**: pytest, pytest-asyncio
- **Utilities**: python-dotenv, Jinja2

### 4. Configuration Files

#### .env File
Generated with default values:
```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/BCSPB
DATABASE_URL_STR=postgresql+asyncpg://postgres:postgres@localhost:5432/BCSPBSTR
DATABASE_URL_TEST=postgresql+asyncpg://postgres:postgres@localhost:5432/BCSPB_TEST

MQ_QUEUE_MANAGER=QM.36266751.01
MQ_CHANNEL=SYSTEM.DEF.SVRCONN
MQ_HOST=localhost
MQ_PORT=1414

SECRET_KEY=<generated-uuid>
DEBUG=false
LOG_LEVEL=INFO

ISPB_FINVEST=36266751
ISPB_BACEN=00038166
```

#### Systemd Services (Linux only)
- `spbsite.service` - Web application service
- `bcsrvsqlmq.service` - Backend service
- Auto-restart on failure
- Start on boot (when enabled)

---

## Installation Details

### Script Flow

1. **Prerequisites Check**
   - Verify administrator/root privileges
   - Check OS compatibility
   - Detect system architecture

2. **Core Tools Installation**
   - Package manager (Chocolatey on Windows)
   - Git version control
   - Build tools and compilers

3. **Python Installation**
   - Download Python 3.12.9 (64-bit)
   - Install system-wide
   - Verify architecture (must be 64-bit)
   - Upgrade pip to latest

4. **Database Setup**
   - Install PostgreSQL 16
   - Create databases (BCSPB, BCSPBSTR, BCSPB_TEST)
   - Set postgres password
   - Configure local connections

5. **IBM MQ Setup**
   - Check for existing installation
   - Provide manual installation instructions
   - Create queue manager
   - Define local queues

6. **Application Setup**
   - Clone Git repository
   - Install Python dependencies for each project
   - Install spb-shared as editable package
   - Generate .env configuration

7. **Verification**
   - Test Python 64-bit architecture
   - Verify PostgreSQL connectivity
   - Check installed Python packages
   - Confirm repository structure

8. **Service Configuration (Linux)**
   - Create systemd service files
   - Configure auto-restart
   - Enable boot start (optional)

---

## Post-Installation Steps

### 1. Update Configuration

Edit `.env` file in installation directory:

```bash
# Windows
notepad C:\SPB\.env

# Linux
nano /opt/spb/.env
```

**Important settings to change**:
- `DATABASE_URL` - Update password
- `SECRET_KEY` - Keep the generated value
- `ISPB_FINVEST` - Your institution's ISPB code
- `ISPB_BACEN` - Central Bank ISPB code

### 2. Initialize Database Schema

```bash
# Navigate to spb-shared
cd C:\SPB\spb-shared  # Windows
cd /opt/spb/spb-shared  # Linux

# Create database tables
py -c "from spb_shared.models import create_tables; import asyncio; asyncio.run(create_tables())"
```

### 3. Load Initial Data (Optional)

```bash
cd C:\SPB\Carga_Mensageria  # Windows
cd /opt/spb/Carga_Mensageria  # Linux

# Load sample messages
py carga_mensageria.py
```

### 4. Run Tests

```bash
cd C:\SPB\spbsite  # Windows
cd /opt/spb/spbsite  # Linux

# Run all tests
py -m pytest -v

# Expected: 89/89 tests passing
```

### 5. Start the Application

#### Windows

```powershell
# Start web application
cd C:\SPB\spbsite
py -m uvicorn app.main:app --reload --port 8000

# In another terminal, start backend service
cd C:\SPB\BCSrvSqlMq
py main.py
```

#### Linux (with systemd)

```bash
# Enable services to start on boot
sudo systemctl enable spbsite bcsrvsqlmq

# Start services
sudo systemctl start spbsite bcsrvsqlmq

# Check status
sudo systemctl status spbsite
sudo systemctl status bcsrvsqlmq

# View logs
sudo journalctl -u spbsite -f
sudo journalctl -u bcsrvsqlmq -f
```

### 6. Access the Application

Open browser and navigate to:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Troubleshooting

### Python Architecture Issues

**Problem**: Tests fail with "Platform not supported" errors

**Solution**:
```bash
# Check Python architecture
py -c "import platform; print(platform.architecture())"

# Should output: ('64bit', 'WindowsPE') on Windows
# Should output: ('64bit', 'ELF') on Linux
```

If 32-bit, uninstall and reinstall with the script.

### PostgreSQL Connection Errors

**Problem**: "Connection refused" or "Authentication failed"

**Solution**:
```bash
# Check PostgreSQL is running
# Windows
sc query postgresql-x64-16

# Linux
sudo systemctl status postgresql

# Test connection
psql -U postgres -h localhost -p 5432 -d BCSPB
```

### IBM MQ Issues

**Problem**: Queue manager not starting

**Solution**:
```bash
# Check queue manager status
dspmq

# Start queue manager manually
strmqm QM.36266751.01

# View error logs
# Windows: C:\ProgramData\IBM\MQ\qmgrs\QM.36266751.01\errors\AMQERR01.LOG
# Linux: /var/mqm/qmgrs/QM.36266751.01/errors/AMQERR01.LOG
```

### Python Package Installation Failures

**Problem**: "Failed to build" errors during pip install

**Solution**:
```bash
# Upgrade pip and setuptools
py -m pip install --upgrade pip setuptools wheel

# Install build tools (if needed)
# Windows: Install Visual Studio Build Tools
# Linux: sudo apt-get install build-essential python3-dev
```

### Port Already in Use

**Problem**: "Address already in use" on port 8000

**Solution**:
```bash
# Windows - Find process using port
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux - Find and kill process
sudo lsof -i :8000
sudo kill -9 <pid>
```

---

## Manual Installation Steps

If automated installation fails, follow these manual steps:

### 1. Install Python 3.12 (64-bit)

**Windows**:
1. Download from https://www.python.org/downloads/
2. Choose "Windows installer (64-bit)"
3. Check "Add Python to PATH"
4. Install for all users

**Linux**:
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
```

### 2. Install PostgreSQL 16

**Windows**:
1. Download from https://www.postgresql.org/download/windows/
2. Run installer
3. Set postgres password
4. Use default port 5432

**Linux**:
```bash
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install postgresql-16
```

### 3. Create Databases

```bash
# Create databases
psql -U postgres -h localhost -c "CREATE DATABASE BCSPB;"
psql -U postgres -h localhost -c "CREATE DATABASE BCSPBSTR;"
psql -U postgres -h localhost -c "CREATE DATABASE BCSPB_TEST;"
```

### 4. Install IBM MQ

Follow IBM MQ installation guide for your platform:
- Windows: https://www.ibm.com/docs/en/ibm-mq/9.3?topic=windows-installing-mq
- Linux: https://www.ibm.com/docs/en/ibm-mq/9.3?topic=linux-installing-mq

### 5. Clone Repository

```bash
# Windows
cd C:\
git clone https://github.com/yourusername/novo_spb.git SPB

# Linux
sudo git clone https://github.com/yourusername/novo_spb.git /opt/spb
```

### 6. Install Python Dependencies

```bash
# Install for each project
cd spbsite && py -m pip install -r requirements.txt
cd ../spb-shared && py -m pip install -e .
cd ../BCSrvSqlMq && py -m pip install -r requirements.txt
```

---

## Verification Checklist

After installation, verify all components:

- [ ] Python 3.12.9 (64-bit) installed
- [ ] PostgreSQL 16 running on port 5432
- [ ] Three databases created (BCSPB, BCSPBSTR, BCSPB_TEST)
- [ ] IBM MQ queue manager running
- [ ] 8 local queues created
- [ ] Git repository cloned
- [ ] Python dependencies installed (no errors)
- [ ] .env file created and configured
- [ ] All tests passing (89/89)
- [ ] Web application starts on port 8000
- [ ] Backend service starts without errors

---

## Security Considerations

### Before Production Deployment

1. **Change Default Passwords**
   - PostgreSQL postgres user
   - Application SECRET_KEY
   - IBM MQ authentication

2. **Configure Firewall**
   - Allow only necessary ports
   - Restrict PostgreSQL to localhost
   - Configure IBM MQ channel authentication

3. **Enable SSL/TLS**
   - PostgreSQL connections
   - Web application (HTTPS)
   - IBM MQ channels

4. **Review Permissions**
   - File system permissions on .env
   - Database user privileges
   - MQ queue permissions

5. **Enable Audit Logging**
   - Application logs
   - Database audit trail
   - MQ message logging

---

## Uninstallation

### Windows

```powershell
# Stop services if running
Stop-Process -Name python -Force

# Uninstall Python (via Control Panel)
# Uninstall PostgreSQL (via Control Panel)
# Uninstall IBM MQ (via Control Panel)

# Remove installation directory
Remove-Item -Recurse -Force C:\SPB

# Uninstall Chocolatey (optional)
# Follow: https://docs.chocolatey.org/en-us/choco/uninstallation
```

### Linux

```bash
# Stop services
sudo systemctl stop spbsite bcsrvsqlmq
sudo systemctl disable spbsite bcsrvsqlmq

# Remove service files
sudo rm /etc/systemd/system/spbsite.service
sudo rm /etc/systemd/system/bcsrvsqlmq.service
sudo systemctl daemon-reload

# Uninstall packages
sudo apt remove postgresql-16 python3.12  # Ubuntu/Debian
sudo yum remove postgresql16 python3.12  # RHEL/CentOS

# Remove installation directory
sudo rm -rf /opt/spb

# Remove IBM MQ (follow IBM documentation)
```

---

## Support and Documentation

### Documentation Files
- [PROJECTS_OVERVIEW.md](PROJECTS_OVERVIEW.md) - System architecture
- [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) - Database configuration
- [IBM_MQ_SETUP.md](IBM_MQ_SETUP.md) - MQ configuration
- [ARCHITECTURE_VERIFICATION.md](ARCHITECTURE_VERIFICATION.md) - Architecture details
- [README.md](README.md) - Main project readme

### Additional Resources
- PostgreSQL Documentation: https://www.postgresql.org/docs/16/
- IBM MQ Documentation: https://www.ibm.com/docs/en/ibm-mq/9.3
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Python Documentation: https://docs.python.org/3.12/

---

## Script Customization

### Configuration Variables

Edit these variables at the top of the scripts:

**PowerShell (install_spb_system.ps1)**:
```powershell
$Config = @{
    InstallDir = "C:\SPB"              # Change installation directory
    PostgreSQL = @{
        Version = "16"                  # PostgreSQL version
        Port = 5432                     # PostgreSQL port
        Password = "postgres"           # Change this!
    }
    Python = @{
        Version = "3.12.9"              # Python version
        URL = "https://..."             # Python download URL
    }
    Git = @{
        Repository = "https://..."      # Your Git repository
    }
}
```

**Bash (install_spb_system.sh)**:
```bash
INSTALL_DIR="/opt/spb"                 # Installation directory
POSTGRESQL_VERSION="16"                # PostgreSQL version
PYTHON_VERSION="3.12"                  # Python version
POSTGRESQL_PASSWORD="postgres"         # Change this!
GIT_REPOSITORY="https://..."           # Your Git repository
```

---

## License

This installation guide and scripts are part of the SPB system project.

---

**Last Updated**: March 8, 2026
**Script Version**: 1.0
**Tested On**: Windows 11 Pro, Ubuntu 22.04 LTS
