# SPB System - Ubuntu Server Deployment Guide
**VS Code Remote Development**

Complete guide for deploying and updating the SPB system on Ubuntu Server using VS Code Remote SSH.

---

## Prerequisites

### Local Machine (Windows)
- VS Code installed
- SSH client available (built-in on Windows 10/11)
- Git credentials configured

### Ubuntu Server
- Ubuntu Server 20.04 LTS or newer
- SSH server running
- User with sudo privileges
- Internet connection

---

## Part 1: Initial Server Setup

### 1.1 Install Required System Packages

SSH into your Ubuntu server and install dependencies:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+ and essentials
sudo apt install -y python3.10 python3.10-venv python3-pip git curl wget

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib libpq-dev

# Install build tools (for Python packages)
sudo apt install -y build-essential python3-dev

# Install IBM MQ Client (if needed for BCSrvSqlMq)
# See IBM_MQ_SETUP.md for IBM MQ installation on Linux
```

### 1.2 Configure PostgreSQL

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create databases and user
sudo -u postgres psql << EOF
CREATE DATABASE "BCSPB";
CREATE DATABASE "BCSPBSTR";
CREATE USER spbadmin WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE "BCSPB" TO spbadmin;
GRANT ALL PRIVILEGES ON DATABASE "BCSPBSTR" TO spbadmin;
ALTER USER spbadmin CREATEDB;
\q
EOF

# Allow password authentication (edit pg_hba.conf if needed)
sudo nano /etc/postgresql/*/main/pg_hba.conf
# Change 'peer' to 'md5' for local connections
sudo systemctl restart postgresql
```

---

## Part 2: VS Code Remote SSH Setup

### 2.1 Install VS Code Remote SSH Extension

1. Open VS Code on your local machine
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Remote - SSH"
4. Install the extension by Microsoft

### 2.2 Configure SSH Connection

1. Press `F1` or `Ctrl+Shift+P`
2. Type "Remote-SSH: Open SSH Configuration File"
3. Select your SSH config file (usually `C:\Users\YourName\.ssh\config`)
4. Add your server configuration:

```ssh-config
Host ubuntu-spb
    HostName 192.168.1.100  # Replace with your server IP
    User yourusername       # Replace with your Ubuntu username
    Port 22
    IdentityFile ~/.ssh/id_rsa  # Optional: use SSH key
```

### 2.3 Connect to Server

1. Press `F1` → "Remote-SSH: Connect to Host"
2. Select `ubuntu-spb`
3. Enter password (or use SSH key)
4. VS Code will connect and install the VS Code Server on Ubuntu

**First connection will take a few minutes while VS Code installs its server components.**

---

## Part 3: Initial Deployment

### 3.1 Clone Repository

In VS Code Remote terminal (connected to Ubuntu):

```bash
# Navigate to your projects directory
cd ~
mkdir -p projects
cd projects

# Clone the repository
git clone https://github.com/ACBtech86/SPB_FINAL.git
cd SPB_FINAL

# Or if already exists, update it
cd ~/projects/SPB_FINAL
git pull origin main
```

### 3.2 Run Installation Script

```bash
# Make the script executable
chmod +x install_spb_system.sh

# Run the installation
./install_spb_system.sh
```

The script will:
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Set up spb-shared package
- ✅ Configure environment files
- ✅ Run database migrations

### 3.3 Configure Environment Variables

Edit the configuration files:

**SPBSite `.env`:**
```bash
cd ~/projects/SPB_FINAL/spbsite
nano .env
```

```env
DATABASE_URL=postgresql+asyncpg://spbadmin:your_secure_password@localhost:5432/BCSPB
CATALOG_DATABASE_URL=postgresql+asyncpg://spbadmin:your_secure_password@localhost:5432/BCSPBSTR
SECRET_KEY=generate-a-secure-random-key-here
APP_TITLE=SPBSite - Finvest DTVM
ISPB_LOCAL=36266751
ISPB_BACEN=00038166
ISPB_SELIC=00038121
```

**BCSrvSqlMq `BCSrvSqlMq.ini`:**
```bash
cd ~/projects/SPB_FINAL/BCSrvSqlMq
cp BCSrvSqlMq.ini.example BCSrvSqlMq.ini
nano BCSrvSqlMq.ini
```

```ini
[Database]
Server=localhost
Port=5432
Database=BCSPB
User=spbadmin
Password=your_secure_password

[IBM_MQ]
QueueManager=QM.36266751.01
Host=localhost
Port=1414
Channel=FINVEST.SVRCONN
```

### 3.4 Initialize Databases

```bash
# Activate virtual environment
cd ~/projects/SPB_FINAL
source venv/bin/activate

# Run migrations for SPBSite
cd spbsite
alembic upgrade head

# Load catalog data (if needed)
cd ../Carga_Mensageria
python init_database.py
python import_from_xsd.py
```

---

## Part 4: Running the Services

### 4.1 Manual Testing

**Test SPBSite:**
```bash
cd ~/projects/SPB_FINAL
source venv/bin/activate
cd spbsite

# Run in development mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Access: `http://your-server-ip:8000`

**Test BCSrvSqlMq:**
```bash
cd ~/projects/SPB_FINAL
source venv/bin/activate
cd BCSrvSqlMq/python

# Run the service
python -m bcsrvsqlmq.main_srv
```

### 4.2 Production Deployment with Systemd

Create systemd service files for automatic startup:

**SPBSite Service:**
```bash
sudo nano /etc/systemd/system/spbsite.service
```

```ini
[Unit]
Description=SPBSite FastAPI Application
After=network.target postgresql.service

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/projects/SPB_FINAL/spbsite
Environment="PATH=/home/yourusername/projects/SPB_FINAL/venv/bin"
ExecStart=/home/yourusername/projects/SPB_FINAL/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**BCSrvSqlMq Service:**
```bash
sudo nano /etc/systemd/system/bcsrvsqlmq.service
```

```ini
[Unit]
Description=BCSrvSqlMq Message Queue Service
After=network.target postgresql.service

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/projects/SPB_FINAL/BCSrvSqlMq/python
Environment="PATH=/home/yourusername/projects/SPB_FINAL/venv/bin"
ExecStart=/home/yourusername/projects/SPB_FINAL/venv/bin/python -m bcsrvsqlmq.main_srv
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start services:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable spbsite
sudo systemctl enable bcsrvsqlmq

# Start services
sudo systemctl start spbsite
sudo systemctl start bcsrvsqlmq

# Check status
sudo systemctl status spbsite
sudo systemctl status bcsrvsqlmq
```

### 4.3 Setup Nginx Reverse Proxy (Optional)

```bash
# Install Nginx
sudo apt install -y nginx

# Create configuration
sudo nano /etc/nginx/sites-available/spbsite
```

```nginx
server {
    listen 80;
    server_name your-domain.com;  # or server IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static {
        alias /home/yourusername/projects/SPB_FINAL/spbsite/app/static;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/spbsite /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Part 5: Updating the System

### 5.1 Connect with VS Code Remote

1. Open VS Code
2. Press `F1` → "Remote-SSH: Connect to Host"
3. Select `ubuntu-spb`
4. Open folder: `/home/yourusername/projects/SPB_FINAL`

### 5.2 Pull Latest Changes

In VS Code integrated terminal:

```bash
# Stop services
sudo systemctl stop spbsite
sudo systemctl stop bcsrvsqlmq

# Pull updates
cd ~/projects/SPB_FINAL
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies (if requirements changed)
cd spbsite
pip install -r requirements.txt --upgrade

cd ../BCSrvSqlMq/python
pip install -r requirements.txt --upgrade

# Run database migrations (if any)
cd ../spbsite
alembic upgrade head

# Restart services
sudo systemctl start spbsite
sudo systemctl start bcsrvsqlmq

# Check status
sudo systemctl status spbsite
sudo systemctl status bcsrvsqlmq
```

### 5.3 Quick Update Script

Create an update script for convenience:

```bash
nano ~/projects/SPB_FINAL/update.sh
```

```bash
#!/bin/bash
set -e

echo "🔄 Updating SPB System..."

# Stop services
echo "⏸️  Stopping services..."
sudo systemctl stop spbsite
sudo systemctl stop bcsrvsqlmq

# Pull changes
echo "📥 Pulling latest changes..."
cd ~/projects/SPB_FINAL
git pull origin main

# Activate venv
source venv/bin/activate

# Update dependencies
echo "📦 Updating dependencies..."
pip install --upgrade pip
cd spbsite && pip install -r requirements.txt --upgrade
cd ../BCSrvSqlMq/python && pip install -r requirements.txt --upgrade

# Run migrations
echo "🗄️  Running database migrations..."
cd ../../spbsite
alembic upgrade head

# Restart services
echo "▶️  Starting services..."
sudo systemctl start spbsite
sudo systemctl start bcsrvsqlmq

# Check status
echo "✅ Update complete! Service status:"
sudo systemctl status spbsite --no-pager
sudo systemctl status bcsrvsqlmq --no-pager

echo "✨ Done!"
```

```bash
chmod +x ~/projects/SPB_FINAL/update.sh
```

**To update in the future:**
```bash
cd ~/projects/SPB_FINAL
./update.sh
```

---

## Part 6: Monitoring & Maintenance

### 6.1 View Service Logs

```bash
# View SPBSite logs
sudo journalctl -u spbsite -f

# View BCSrvSqlMq logs
sudo journalctl -u bcsrvsqlmq -f

# View last 100 lines
sudo journalctl -u spbsite -n 100

# View logs from today
sudo journalctl -u spbsite --since today
```

### 6.2 Common Commands

```bash
# Restart services
sudo systemctl restart spbsite
sudo systemctl restart bcsrvsqlmq

# Stop services
sudo systemctl stop spbsite
sudo systemctl stop bcsrvsqlmq

# Check status
sudo systemctl status spbsite
sudo systemctl status bcsrvsqlmq

# View database connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity WHERE datname='BCSPB';"

# Check disk space
df -h

# Check memory usage
free -h
```

### 6.3 Backup Strategy

**Automated PostgreSQL Backup:**
```bash
nano ~/backup_spb.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/yourusername/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup databases
pg_dump -U spbadmin -h localhost BCSPB > $BACKUP_DIR/BCSPB_$TIMESTAMP.sql
pg_dump -U spbadmin -h localhost BCSPBSTR > $BACKUP_DIR/BCSPBSTR_$TIMESTAMP.sql

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup completed: $TIMESTAMP"
```

```bash
chmod +x ~/backup_spb.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/yourusername/backup_spb.sh
```

---

## Part 7: VS Code Remote Development Tips

### 7.1 Recommended Extensions (Install on Remote)

- Python
- Pylance
- GitLens
- SQLTools (with PostgreSQL driver)
- Better Comments

### 7.2 Remote Terminal

Use VS Code integrated terminal:
- Terminal → New Terminal (Ctrl+Shift+`)
- Runs directly on Ubuntu server
- Full access to all commands

### 7.3 File Editing

- Edit files directly in VS Code
- Changes are made on the server
- Git integration works seamlessly
- IntelliSense and debugging available

### 7.4 Port Forwarding

Forward ports from server to local machine:

1. Press `F1` → "Forward a Port"
2. Enter port `8000` (SPBSite)
3. Access via `http://localhost:8000` on your Windows machine

---

## Part 8: Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status spbsite

# Check logs for errors
sudo journalctl -u spbsite -n 50

# Check if port is in use
sudo netstat -tulpn | grep 8000

# Test configuration
cd ~/projects/SPB_FINAL
source venv/bin/activate
cd spbsite
uvicorn app.main:app --reload  # Run manually to see errors
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U spbadmin -h localhost -d BCSPB

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check pg_hba.conf authentication
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R yourusername:yourusername ~/projects/SPB_FINAL

# Fix Python virtual environment
cd ~/projects/SPB_FINAL
rm -rf venv
python3 -m venv venv
source venv/bin/activate
./install_spb_system.sh
```

---

## Summary

### Initial Deployment
1. ✅ Setup Ubuntu server (PostgreSQL, Python)
2. ✅ Configure VS Code Remote SSH
3. ✅ Clone repository
4. ✅ Run `install_spb_system.sh`
5. ✅ Configure `.env` and `.ini` files
6. ✅ Create systemd services
7. ✅ Start services

### Regular Updates
1. 🔄 Connect via VS Code Remote
2. 🔄 Run `./update.sh`
3. 🔄 Monitor logs
4. 🔄 Test application

### Monitoring
- 📊 `systemctl status spbsite`
- 📊 `sudo journalctl -u spbsite -f`
- 📊 Database backups (automated)

---

**Questions or Issues?**
Contact the Finvest DTVM IT team.

**Last Updated:** March 8, 2026
