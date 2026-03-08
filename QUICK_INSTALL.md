# SPB System - Quick Installation Reference

## Windows Installation (3 Steps)

### 1. Run PowerShell as Administrator
```powershell
# Enable scripts
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Navigate to project
cd "C:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\Novo_SPB"
```

### 2. Run Installation Script
```powershell
# Full installation
.\install_spb_system.ps1

# Or with custom directory
.\install_spb_system.ps1 -InstallDir "D:\SPB"

# Or skip IBM MQ (manual install)
.\install_spb_system.ps1 -SkipIBMMQ
```

### 3. Configure and Start
```powershell
# Edit configuration
notepad C:\SPB\.env

# Initialize database
cd C:\SPB\spb-shared
py -c "from spb_shared.models import create_tables; import asyncio; asyncio.run(create_tables())"

# Run tests
cd C:\SPB\spbsite
py -m pytest -v

# Start application
py -m uvicorn app.main:app --reload --port 8000
```

---

## Linux Installation (3 Steps)

### 1. Make Script Executable
```bash
chmod +x install_spb_system.sh
```

### 2. Run Installation Script
```bash
# Full installation
sudo ./install_spb_system.sh

# Or with custom directory
sudo ./install_spb_system.sh --install-dir /opt/spb

# Or skip IBM MQ
sudo ./install_spb_system.sh --skip-ibmmq
```

### 3. Configure and Start
```bash
# Edit configuration
sudo nano /opt/spb/.env

# Initialize database
cd /opt/spb/spb-shared
python3 -c "from spb_shared.models import create_tables; import asyncio; asyncio.run(create_tables())"

# Run tests
cd /opt/spb/spbsite
python3 -m pytest -v

# Start services
sudo systemctl enable spbsite bcsrvsqlmq
sudo systemctl start spbsite bcsrvsqlmq
```

---

## What Gets Installed

| Component | Version | Port | Notes |
|-----------|---------|------|-------|
| Python | 3.12.9 (64-bit) | - | System-wide |
| PostgreSQL | 16 | 5432 | 3 databases |
| IBM MQ | 9.3 | 1414 | Manual install may be needed |
| SPBSite | Latest | 8000 | FastAPI web app |
| BCSrvSqlMq | Latest | - | Background service |

---

## Default Credentials (CHANGE THESE!)

```ini
PostgreSQL User: postgres
PostgreSQL Password: postgres

Database Names:
- BCSPB (main)
- BCSPBSTR (catalog)
- BCSPB_TEST (testing)

IBM MQ Queue Manager: QM.36266751.01
```

---

## Quick Verification

```bash
# Check Python (must be 64-bit)
py -c "import platform; print(platform.architecture())"
# Expected: ('64bit', ...)

# Check PostgreSQL
psql -U postgres -h localhost -l

# Check databases
psql -U postgres -h localhost -c "\l" | grep BCSPB

# Check IBM MQ
dspmq

# Run tests
cd spbsite && py -m pytest -v
# Expected: 89/89 passing
```

---

## Quick Start Commands

```bash
# Start web application (development)
cd C:\SPB\spbsite  # or /opt/spb/spbsite
py -m uvicorn app.main:app --reload --port 8000

# Start backend service
cd C:\SPB\BCSrvSqlMq  # or /opt/spb/BCSrvSqlMq
py main.py

# Run BACEN simulator
cd C:\SPB  # or /opt/spb
py bacen_simulator.py

# Access web interface
http://localhost:8000
```

---

## Common Issues

| Problem | Solution |
|---------|----------|
| "Python not 64-bit" | Reinstall Python 3.12.9 (64-bit) |
| "Port 8000 in use" | `netstat -ano \| findstr :8000` then kill process |
| "PostgreSQL connection failed" | Check service is running, verify password |
| "IBM MQ queues not found" | Run `strmqm QM.36266751.01` |
| "Tests failing" | Check database connection in .env |

---

## Important Files

```
C:\SPB\                          # Installation directory
├── .env                         # Configuration (EDIT THIS!)
├── spbsite/                     # Web application
│   ├── app/main.py             # FastAPI app
│   └── tests/                  # Test suite
├── spb-shared/                  # Shared models
├── BCSrvSqlMq/                  # Backend service
└── bacen_simulator.py           # BACEN simulator
```

---

## Monitoring & Logs

### Windows
```powershell
# View application logs
Get-Content C:\SPB\spbsite\logs\app.log -Tail 50 -Wait

# Check Python processes
Get-Process python
```

### Linux
```bash
# View service logs
sudo journalctl -u spbsite -f
sudo journalctl -u bcsrvsqlmq -f

# Check service status
sudo systemctl status spbsite bcsrvsqlmq
```

---

## Uninstall

### Windows
```powershell
# Stop processes
Stop-Process -Name python -Force

# Remove directory
Remove-Item -Recurse -Force C:\SPB

# Uninstall components via Control Panel
```

### Linux
```bash
# Stop services
sudo systemctl stop spbsite bcsrvsqlmq
sudo systemctl disable spbsite bcsrvsqlmq

# Remove installation
sudo rm -rf /opt/spb
sudo rm /etc/systemd/system/spbsite.service
sudo rm /etc/systemd/system/bcsrvsqlmq.service
```

---

## Need Help?

- Full Guide: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- Architecture: [ARCHITECTURE_VERIFICATION.md](ARCHITECTURE_VERIFICATION.md)
- Project Overview: [PROJECTS_OVERVIEW.md](PROJECTS_OVERVIEW.md)
- PostgreSQL: [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)
- IBM MQ: [IBM_MQ_SETUP.md](IBM_MQ_SETUP.md)

---

**Installation Time**: ~20-30 minutes (excluding IBM MQ manual install)
**Requirements**: Administrator/root privileges, Internet connection
**Tested**: Windows 11 Pro, Ubuntu 22.04 LTS
