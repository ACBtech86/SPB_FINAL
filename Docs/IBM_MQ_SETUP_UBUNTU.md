# IBM MQ Setup Guide for Ubuntu Server

Complete guide to install and configure IBM MQ on Ubuntu Server for the SPB messaging system.

---

## Prerequisites

- Ubuntu Server 20.04 LTS or newer
- Sudo/root access
- At least 2GB free disk space
- Port 1414 available (default MQ listener port)
- Internet connection for downloading IBM MQ

---

## Step 1: Download IBM MQ for Linux

### Option A: IBM MQ Developer Edition (Free - Recommended)

```bash
# Create download directory
mkdir -p ~/ibm-mq-install
cd ~/ibm-mq-install

# Download IBM MQ 9.3 LTS for Linux (Ubuntu)
# Visit: https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqadv/
# or use wget (example for 9.3.4.0):
wget https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqadv/mqadv_dev934_ubuntu_x86-64.tar.gz

# Extract the archive
tar -xzf mqadv_dev934_ubuntu_x86-64.tar.gz
cd MQServer
```

### Option B: Direct Download from IBM

1. Visit: https://www.ibm.com/products/mq/advanced
2. Click "Try IBM MQ"
3. Select "IBM MQ Advanced for Developers (Linux)"
4. Download and transfer to your Ubuntu server

---

## Step 2: Install Prerequisites

Install required system packages:

```bash
# Update package list
sudo apt update

# Install required packages
sudo apt install -y \
    rpm \
    alien \
    bash \
    bc \
    coreutils \
    findutils \
    gawk \
    grep \
    libc6 \
    mount \
    passwd \
    procps \
    sed \
    tar \
    util-linux \
    ksh

# Install additional libraries
sudo apt install -y \
    libstdc++6 \
    libgcc1 \
    libc6-dev
```

---

## Step 3: Install IBM MQ

### Method 1: Using Debian Packages (Recommended for Ubuntu)

```bash
cd ~/ibm-mq-install/MQServer

# Accept the license
sudo ./mqlicense.sh -accept

# Install MQ Server packages
sudo apt install -y \
    ./ibmmq-runtime_*.deb \
    ./ibmmq-server_*.deb \
    ./ibmmq-msg-*.deb \
    ./ibmmq-samples_*.deb \
    ./ibmmq-java_*.deb \
    ./ibmmq-jre_*.deb \
    ./ibmmq-gskit_*.deb \
    ./ibmmq-web_*.deb
```

### Method 2: Using RPM packages with alien (Alternative)

```bash
cd ~/ibm-mq-install/MQServer

# Convert RPM to DEB and install
for rpm in MQSeriesRuntime-*.rpm MQSeriesServer-*.rpm MQSeriesMsg*.rpm \
           MQSeriesSamples-*.rpm MQSeriesJava-*.rpm MQSeriesJRE-*.rpm \
           MQSeriesGSKit-*.rpm MQSeriesWeb-*.rpm; do
    sudo alien -i "$rpm"
done
```

---

## Step 4: Configure Environment

### Add MQ to PATH

```bash
# Add to .bashrc
echo '# IBM MQ Environment' >> ~/.bashrc
echo 'export MQ_INSTALLATION_PATH=/opt/mqm' >> ~/.bashrc
echo 'export PATH=$PATH:/opt/mqm/bin' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/opt/mqm/lib64:/opt/mqm/lib:$LD_LIBRARY_PATH' >> ~/.bashrc

# Reload bashrc
source ~/.bashrc
```

### Verify Installation

```bash
# Check MQ version
dspmqver

# Expected output:
# Name:        IBM MQ
# Version:     9.3.4.0
# ...
```

---

## Step 5: Create MQ User and Group

```bash
# Create mqm group and user
sudo groupadd mqm
sudo useradd -g mqm -m -d /home/mqm -s /bin/bash mqm

# Set password for mqm user (optional, for direct login)
sudo passwd mqm

# Add your current user to mqm group
sudo usermod -a -G mqm $USER

# Apply group changes (logout/login may be required)
newgrp mqm
```

---

## Step 6: Create Queue Manager

```bash
# Switch to mqm user (or use sudo -u mqm)
sudo su - mqm

# Create queue manager QM.36266751.01
crtmqm QM.36266751.01

# Start the queue manager
strmqm QM.36266751.01

# Verify it's running
dspmq
```

Expected output:
```
QMNAME(QM.36266751.01)                                        STATUS(Running)
```

---

## Step 7: Configure Queue Manager

Run MQSC commands to configure:

```bash
# Run MQSC as mqm user
runmqsc QM.36266751.01
```

In the MQSC console, enter these commands:

```mqsc
* Define server connection channel
DEFINE CHANNEL(FINVEST.SVRCONN) CHLTYPE(SVRCONN)

* Define listener on port 1414
DEFINE LISTENER(FINVEST.LISTENER) TRPTYPE(TCP) PORT(1414) CONTROL(QMGR)
START LISTENER(FINVEST.LISTENER)

* Set channel authentication (for development - disable authentication)
* WARNING: For production, use proper authentication!
ALTER QMGR CHLAUTH(DISABLED)

* Set connection authentication (for development)
ALTER QMGR CONNAUTH(' ')
REFRESH SECURITY TYPE(CONNAUTH)

* Allow all users (for development)
SET CHLAUTH(FINVEST.SVRCONN) TYPE(BLOCKUSER) USERLIST('nobody') ACTION(REMOVE)
SET CHLAUTH(*) TYPE(ADDRESSMAP) ADDRESS(*) USERSRC(NOACCESS) ACTION(REMOVE)
REFRESH SECURITY TYPE(SSL)

* Exit MQSC
END
```

---

## Step 8: Create SPB Queues

Create all required queues for the SPB system:

```bash
# Run MQSC
runmqsc QM.36266751.01
```

```mqsc
* ========================================
* BACEN Local Queues (receive from BACEN)
* ========================================
DEFINE QLOCAL(QL.REQ.00038166.36266751.01) MAXDEPTH(100000) DESCR('BACEN Request to Finvest')
DEFINE QLOCAL(QL.RSP.00038166.36266751.01) MAXDEPTH(100000) DESCR('BACEN Response to Finvest')
DEFINE QLOCAL(QL.REP.00038166.36266751.01) MAXDEPTH(100000) DESCR('BACEN Report to Finvest')
DEFINE QLOCAL(QL.SUP.00038166.36266751.01) MAXDEPTH(100000) DESCR('BACEN Support to Finvest')

* ========================================
* BACEN Remote Queues (send to BACEN)
* ========================================
* Note: For local testing, we'll create local queues instead
DEFINE QLOCAL(QL.REQ.36266751.00038166.01) MAXDEPTH(100000) DESCR('Finvest Request to BACEN - Local Simulation')
DEFINE QLOCAL(QL.RSP.36266751.00038166.01) MAXDEPTH(100000) DESCR('Finvest Response to BACEN - Local Simulation')
DEFINE QLOCAL(QL.REP.36266751.00038166.01) MAXDEPTH(100000) DESCR('Finvest Report to BACEN - Local Simulation')
DEFINE QLOCAL(QL.SUP.36266751.00038166.01) MAXDEPTH(100000) DESCR('Finvest Support to BACEN - Local Simulation')

* Alternative: Use remote queues for production
* DEFINE QREMOTE(QR.REQ.36266751.00038166.01) RNAME(QL.REQ.36266751.00038166.01) RQMNAME(QM.BACEN) XMITQ(BACEN.XMITQ)
* DEFINE QREMOTE(QR.RSP.36266751.00038166.01) RNAME(QL.RSP.36266751.00038166.01) RQMNAME(QM.BACEN) XMITQ(BACEN.XMITQ)
* DEFINE QREMOTE(QR.REP.36266751.00038166.01) RNAME(QL.REP.36266751.00038166.01) RQMNAME(QM.BACEN) XMITQ(BACEN.XMITQ)
* DEFINE QREMOTE(QR.SUP.36266751.00038166.01) RNAME(QL.SUP.36266751.00038166.01) RQMNAME(QM.BACEN) XMITQ(BACEN.XMITQ)

* ========================================
* IF (Interfaceamento) Local Queues
* ========================================
DEFINE QLOCAL(QL.36266751.01.ENTRADA.IF) MAXDEPTH(100000) DESCR('IF Entrada Queue')
DEFINE QLOCAL(QL.36266751.01.SAIDA.IF) MAXDEPTH(100000) DESCR('IF Saida Queue')
DEFINE QLOCAL(QL.36266751.01.REPORT.IF) MAXDEPTH(100000) DESCR('IF Report Queue')
DEFINE QLOCAL(QL.36266751.01.SUPORTE.IF) MAXDEPTH(100000) DESCR('IF Support Queue')

* ========================================
* System Queues
* ========================================
* Transmission Queue for BACEN (for production use)
DEFINE QLOCAL(BACEN.XMITQ) USAGE(XMITQ) MAXDEPTH(100000)

* Dead Letter Queue
DEFINE QLOCAL(DEAD.LETTER.QUEUE) MAXDEPTH(100000)
ALTER QMGR DEADQ(DEAD.LETTER.QUEUE)

* Exit MQSC
END
```

---

## Step 9: Configure Firewall

Allow MQ listener port:

```bash
# Using UFW (Ubuntu Firewall)
sudo ufw allow 1414/tcp
sudo ufw status

# Using iptables (alternative)
sudo iptables -A INPUT -p tcp --dport 1414 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

---

## Step 10: Configure Auto-Start (Systemd Service)

Create systemd service for automatic startup:

```bash
# Create service file
sudo nano /etc/systemd/system/ibmmq@.service
```

Add the following content:

```ini
[Unit]
Description=IBM MQ Queue Manager %I
After=network.target

[Service]
Type=forking
User=mqm
Group=mqm
ExecStart=/opt/mqm/bin/strmqm %I
ExecStop=/opt/mqm/bin/endmqm -i %I
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start for queue manager
sudo systemctl enable ibmmq@QM.36266751.01

# Start the queue manager
sudo systemctl start ibmmq@QM.36266751.01

# Check status
sudo systemctl status ibmmq@QM.36266751.01
```

---

## Step 11: Verify Queue Creation

```bash
# As mqm user
sudo su - mqm

# Run MQSC
runmqsc QM.36266751.01
```

```mqsc
* Display all local queues
DISPLAY QLOCAL(*) CURDEPTH

* Display specific queue
DISPLAY QLOCAL(QL.REQ.00038166.36266751.01) ALL

* Display channels
DISPLAY CHANNEL(FINVEST.SVRCONN) ALL

* Display listener status
DISPLAY LSSTATUS(*) ALL

* Exit
END
```

---

## Step 12: Test MQ Connection

### Test with Python (pymqi)

First, install pymqi on Ubuntu:

```bash
# Install build dependencies
sudo apt install -y gcc python3-dev

# Activate virtual environment
cd ~/projects/SPB_FINAL
source venv/bin/activate

# Install pymqi
pip install pymqi
```

Create test file `test_mq_ubuntu.py`:

```python
#!/usr/bin/env python3
import pymqi

qmgr_name = 'QM.36266751.01'
channel = 'FINVEST.SVRCONN'
conn_info = 'localhost(1414)'
queue_name = 'QL.36266751.01.ENTRADA.IF'

try:
    # Connect to queue manager
    qmgr = pymqi.connect(qmgr_name, channel, conn_info)
    print(f'✅ Connected to {qmgr_name}')

    # Open queue
    queue = pymqi.Queue(qmgr, queue_name)
    print(f'✅ Opened queue {queue_name}')

    # Put test message
    test_msg = b'TEST MESSAGE FROM UBUNTU'
    queue.put(test_msg)
    print(f'✅ Message sent to queue')

    # Get message back
    msg = queue.get()
    print(f'✅ Message received: {msg.decode()}')

    # Close
    queue.close()
    qmgr.disconnect()
    print('✅ Test completed successfully!')

except pymqi.MQMIError as e:
    print(f'❌ MQ Error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
```

Run test:

```bash
chmod +x test_mq_ubuntu.py
python test_mq_ubuntu.py
```

---

## Step 13: Configure BCSrvSqlMq.ini for Ubuntu

Update the MQ configuration section:

```bash
nano ~/projects/SPB_FINAL/BCSrvSqlMq/BCSrvSqlMq.ini
```

```ini
[IBM_MQ]
QueueManager=QM.36266751.01
Host=localhost
Port=1414
Channel=FINVEST.SVRCONN

# Queue names
LocalQueue_BACEN_REQ=QL.REQ.00038166.36266751.01
LocalQueue_BACEN_RSP=QL.RSP.00038166.36266751.01
LocalQueue_BACEN_REP=QL.REP.00038166.36266751.01
LocalQueue_BACEN_SUP=QL.SUP.00038166.36266751.01

RemoteQueue_BACEN_REQ=QL.REQ.36266751.00038166.01
RemoteQueue_BACEN_RSP=QL.RSP.36266751.00038166.01
RemoteQueue_BACEN_REP=QL.REP.36266751.00038166.01
RemoteQueue_BACEN_SUP=QL.SUP.36266751.00038166.01
```

---

## Troubleshooting

### Queue Manager Won't Start

```bash
# Check status
dspmq

# Check detailed status
dspmq -m QM.36266751.01 -x

# View error logs
sudo cat /var/mqm/qmgrs/QM\!36266751\!01/errors/AMQERR01.LOG

# Check permissions
ls -la /var/mqm/
```

### Connection Refused (2538)

```bash
# Verify listener is running
echo "DISPLAY LSSTATUS(*)" | runmqsc QM.36266751.01

# Check if port 1414 is listening
sudo netstat -tulpn | grep 1414
# or
sudo ss -tulpn | grep 1414

# Restart listener
runmqsc QM.36266751.01 << EOF
STOP LISTENER(FINVEST.LISTENER)
START LISTENER(FINVEST.LISTENER)
END
EOF
```

### Permission Denied (2035)

```bash
# Disable channel authentication (for development)
runmqsc QM.36266751.01 << EOF
ALTER QMGR CHLAUTH(DISABLED)
REFRESH SECURITY
END
EOF

# Check channel status
echo "DISPLAY CHSTATUS(FINVEST.SVRCONN)" | runmqsc QM.36266751.01
```

### pymqi Installation Issues

```bash
# Install build tools
sudo apt install -y build-essential gcc g++ make python3-dev

# Set MQ environment variables for pymqi
export MQ_FILE_PATH=/opt/mqm
export LD_LIBRARY_PATH=/opt/mqm/lib64:/opt/mqm/lib

# Reinstall pymqi
pip uninstall pymqi
pip install pymqi --no-cache-dir
```

---

## Useful Commands Reference

```bash
# Queue Manager Operations
strmqm QM.36266751.01              # Start queue manager
endmqm QM.36266751.01               # Stop queue manager (controlled)
endmqm -i QM.36266751.01           # Stop queue manager (immediate)
dspmq                               # Display all queue managers
dspmq -m QM.36266751.01 -x         # Display detailed status

# MQSC Commands
runmqsc QM.36266751.01              # Interactive MQSC
echo "DISPLAY QLOCAL(*)" | runmqsc QM.36266751.01  # Single command

# Queue Operations
# Display queue depth
echo "DISPLAY QLOCAL(*) CURDEPTH" | runmqsc QM.36266751.01

# Clear a queue
runmqsc QM.36266751.01 << EOF
CLEAR QLOCAL(QL.36266751.01.ENTRADA.IF)
END
EOF

# Browse messages without removing
/opt/mqm/samp/bin/amqsbcg QL.36266751.01.ENTRADA.IF QM.36266751.01

# Get and remove messages
/opt/mqm/samp/bin/amqsget QL.36266751.01.ENTRADA.IF QM.36266751.01

# Put a test message
echo "TEST MESSAGE" | /opt/mqm/samp/bin/amqsput QL.36266751.01.ENTRADA.IF QM.36266751.01

# Service Management (systemd)
sudo systemctl start ibmmq@QM.36266751.01
sudo systemctl stop ibmmq@QM.36266751.01
sudo systemctl restart ibmmq@QM.36266751.01
sudo systemctl status ibmmq@QM.36266751.01
sudo journalctl -u ibmmq@QM.36266751.01 -f  # View logs
```

---

## Security Hardening (Production)

For production environments, enable proper authentication:

```bash
runmqsc QM.36266751.01
```

```mqsc
* Enable channel authentication
ALTER QMGR CHLAUTH(ENABLED)

* Require TLS/SSL
ALTER CHANNEL(FINVEST.SVRCONN) CHLTYPE(SVRCONN) SSLCIPH(TLS_RSA_WITH_AES_256_CBC_SHA256)

* Restrict by IP
SET CHLAUTH(FINVEST.SVRCONN) TYPE(ADDRESSMAP) ADDRESS('192.168.1.*') USERSRC(CHANNEL) CHCKCLNT(REQUIRED)

* Require authentication
ALTER QMGR CONNAUTH('SYSTEM.DEFAULT.AUTHINFO.IDPWOS')
REFRESH SECURITY TYPE(CONNAUTH)

END
```

---

## Summary

After completing these steps:
- ✅ IBM MQ installed on Ubuntu Server
- ✅ Queue Manager `QM.36266751.01` created and running
- ✅ All SPB queues created (BACEN, IF, system queues)
- ✅ Channel `FINVEST.SVRCONN` configured
- ✅ Listener running on port 1414
- ✅ Auto-start configured via systemd
- ✅ Firewall configured
- ✅ Ready for BCSrvSqlMq integration

**Next Steps:**
1. Configure BCSrvSqlMq.ini with MQ settings
2. Test connection with Python/pymqi
3. Start BCSrvSqlMq service
4. Monitor logs for successful connection

---

**Useful Links:**
- IBM MQ Documentation: https://www.ibm.com/docs/en/ibm-mq/
- IBM MQ Downloads: https://www.ibm.com/products/mq/advanced
- pymqi Documentation: https://pythonhosted.org/pymqi/

**Last Updated:** March 8, 2026
