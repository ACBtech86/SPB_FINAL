# BCSrvSqlMq Setup Complete ✅

**Setup Date:** 2026-03-08
**Platform:** Ubuntu Server 24.04 LTS
**Status:** ✅ All components configured and tested

---

## 📋 Summary

The complete BCSrvSqlMq environment has been successfully installed and configured on Ubuntu Server with IBM MQ and PostgreSQL database.

---

## ✅ Components Installed

### 1. IBM MQ 9.3.0.0
- **Queue Manager:** QM.36266751.01
- **Status:** Running (auto-start enabled)
- **Channel:** FINVEST.SVRCONN
- **Listener:** Port 1414
- **Packages Installed:**
  - ibmmq-runtime
  - ibmmq-server
  - ibmmq-client
  - ibmmq-sdk
  - ibmmq-java
  - ibmmq-samples
  - ibmmq-gskit
  - ibmmq-web
  - Language packs (multi-language support)

### 2. PostgreSQL 16.13
- **Database:** bcspbstr
- **User:** postgres
- **Port:** 5432
- **Status:** Running

### 3. Python Libraries
- **pymqi 1.12.13** - IBM MQ Python interface
- **psycopg2-binary 2.9.11** - PostgreSQL Python interface

---

## 📁 Directory Structure

```
/home/ubuntu/SPB_FINAL/BCSrvSqlMq/
├── BCSrvSqlMq.ini                 # Main configuration file
├── BCSrvSqlMq.ini.example         # Configuration template
├── setup_database.py              # Database setup script
├── verify_mq_config.py            # MQ verification script
├── verify_db_config.py            # Database verification script
├── test_integration.py            # Integration test suite
├── Traces/                        # Log traces directory
├── AuditFiles/                    # Audit files directory
├── certificates/                  # SSL certificates directory
└── python/                        # Python application code

/home/ubuntu/SPB_FINAL/
└── test_mq_ubuntu.py              # Simple MQ test script
```

---

## 🗄️ Database Tables Created

### Application Tables
1. **SPB_LOG_BACEN** - Transaction log
2. **SPB_BACEN_TO_LOCAL** - Messages from BACEN to local system
3. **SPB_LOCAL_TO_BACEN** - Messages from local system to BACEN
4. **SPB_CONTROLE** - Control/coordination table
   - Default record: ISPB=36266751, Name=FINVEST, Status=A

### Catalog Tables
5. **SPB_MENSAGEM** - Message definitions
6. **SPB_DICIONARIO** - Data dictionary
7. **SPB_MSGFIELD** - Message field definitions

### Views (for compatibility)
- spb_mensagem_view
- spb_dicionario_view
- spb_msgfield_view

---

## 📬 IBM MQ Queues Created

### BACEN Local Queues (Receive from BACEN)
- QL.REQ.00038166.36266751.01 - Request
- QL.RSP.00038166.36266751.01 - Response
- QL.REP.00038166.36266751.01 - Report
- QL.SUP.00038166.36266751.01 - Support

### BACEN Remote Queues (Send to BACEN - Local Simulation)
- QL.REQ.36266751.00038166.01 - Request
- QL.RSP.36266751.00038166.01 - Response
- QL.REP.36266751.00038166.01 - Report
- QL.SUP.36266751.00038166.01 - Support

### IF (Interfaceamento) Queues
- QL.36266751.01.ENTRADA.IF - Input
- QL.36266751.01.SAIDA.IF - Output
- QL.36266751.01.REPORT.IF - Report
- QL.36266751.01.SUPORTE.IF - Support

### System Queues
- BACEN.XMITQ - Transmission queue
- DEAD.LETTER.QUEUE - Dead letter queue

**Total:** 14 queues

---

## ⚙️ Configuration Files

### BCSrvSqlMq.ini

```ini
[MQSeries]
MQServer=localhost
QueueManager=QM.36266751.01
QueueTimeout=30
QLBacenCidadeReq=QL.REQ.00038166.36266751.01
QLBacenCidadeRsp=QL.RSP.00038166.36266751.01
QLBacenCidadeRep=QL.REP.00038166.36266751.01
QLBacenCidadeSup=QL.SUP.00038166.36266751.01
QRCidadeBacenReq=QL.REQ.36266751.00038166.01
QRCidadeBacenRsp=QL.RSP.36266751.00038166.01
QRCidadeBacenRep=QL.REP.36266751.00038166.01
QRCidadeBacenSup=QL.SUP.36266751.00038166.01

[DataBase]
DBServer=localhost
DBName=BCSPBSTR
DbTbStrLog=SPB_LOG_BACEN
DbTbBacenCidadeApp=SPB_BACEN_TO_LOCAL
DbTbCidadeBacenApp=SPB_LOCAL_TO_BACEN
DbTbControle=SPB_CONTROLE

[Diretorios]
DirTraces=/home/ubuntu/SPB_FINAL/BCSrvSqlMq/Traces
DirAudFile=/home/ubuntu/SPB_FINAL/BCSrvSqlMq/AuditFiles
```

### Environment Variables (.bashrc)

```bash
# IBM MQ Environment
export MQ_INSTALLATION_PATH=/opt/mqm
export PATH=$PATH:/opt/mqm/bin
export LD_LIBRARY_PATH=/opt/mqm/lib64:/opt/mqm/lib:$LD_LIBRARY_PATH
```

---

## 🔄 Auto-Start Configuration

### Systemd Service
- **Service:** `ibmmq@QM.36266751.01.service`
- **Status:** Enabled and running
- **Location:** `/etc/systemd/system/ibmmq@.service`

**Management Commands:**
```bash
# Start/Stop/Restart
sudo systemctl start ibmmq@QM.36266751.01
sudo systemctl stop ibmmq@QM.36266751.01
sudo systemctl restart ibmmq@QM.36266751.01

# Check status
sudo systemctl status ibmmq@QM.36266751.01

# View logs
sudo journalctl -u ibmmq@QM.36266751.01 -f
```

---

## 🧪 Testing & Verification

### Test Scripts

1. **test_mq_ubuntu.py** - Simple MQ connection test
   ```bash
   python3 /home/ubuntu/SPB_FINAL/test_mq_ubuntu.py
   ```

2. **verify_mq_config.py** - Verify MQ configuration
   ```bash
   python3 /home/ubuntu/SPB_FINAL/BCSrvSqlMq/verify_mq_config.py
   ```

3. **verify_db_config.py** - Verify database configuration
   ```bash
   python3 /home/ubuntu/SPB_FINAL/BCSrvSqlMq/verify_db_config.py
   ```

4. **test_integration.py** - Full integration test
   ```bash
   python3 /home/ubuntu/SPB_FINAL/BCSrvSqlMq/test_integration.py
   ```

### Test Results
✅ All tests passed on 2026-03-08:
- MQ Connection: PASSED
- Database Connection: PASSED
- MQ to Database Integration: PASSED

---

## 🛠️ Useful Commands

### IBM MQ Commands

```bash
# Queue Manager Operations
strmqm QM.36266751.01              # Start queue manager
endmqm QM.36266751.01              # Stop (controlled)
endmqm -i QM.36266751.01          # Stop (immediate)
dspmq                              # Display all queue managers

# MQSC Commands
runmqsc QM.36266751.01             # Interactive MQSC

# Display queues
echo "DISPLAY QLOCAL(*) CURDEPTH" | runmqsc QM.36266751.01

# Display listener status
echo "DISPLAY LSSTATUS(*)" | runmqsc QM.36266751.01

# Browse messages
/opt/mqm/samp/bin/amqsbcg QL.36266751.01.ENTRADA.IF QM.36266751.01

# Put test message
echo "TEST" | /opt/mqm/samp/bin/amqsput QL.36266751.01.ENTRADA.IF QM.36266751.01
```

### PostgreSQL Commands

```bash
# Connect to database
sudo -u postgres psql -d bcspbstr

# List tables
\dt

# Describe table
\d spb_log_bacen

# Query examples
SELECT COUNT(*) FROM SPB_LOG_BACEN;
SELECT * FROM SPB_CONTROLE;
```

---

## 🔒 Security Notes

### Current Configuration (Development Mode)
⚠️ **DEVELOPMENT ONLY** - Not suitable for production

- IBM MQ channel authentication: **DISABLED**
- IBM MQ connection authentication: **DISABLED**
- No SSL/TLS encryption
- PostgreSQL authentication: password-based

### For Production
See [IBM_MQ_SETUP_UBUNTU.md](IBM_MQ_SETUP_UBUNTU.md) section "Security Hardening (Production)" for:
- Enabling channel authentication
- Configuring SSL/TLS
- IP restrictions
- User authentication

---

## 📚 Documentation

- **IBM MQ Setup Guide:** [Docs/IBM_MQ_SETUP_UBUNTU.md](../Docs/IBM_MQ_SETUP_UBUNTU.md)
- **Message Flows:** [MESSAGE_FLOWS.md](MESSAGE_FLOWS.md)
- **MQ Quick Reference:** [MQ_QUICK_REFERENCE.md](MQ_QUICK_REFERENCE.md)
- **Session Notes:** [SESSION_NOTES.md](SESSION_NOTES.md)

---

## 🎯 Next Steps

1. **Load Catalog Data**
   - Import SPB message definitions into SPB_MENSAGEM
   - Import data dictionary into SPB_DICIONARIO
   - Import message fields into SPB_MSGFIELD

2. **Configure Security**
   - Enable SSL/TLS for production
   - Configure proper authentication
   - Set up certificate management

3. **Application Development**
   - Develop/test BCSrvSqlMq application
   - Implement message handlers
   - Add monitoring and alerting

4. **Performance Tuning**
   - Adjust queue manager settings
   - Optimize database indexes
   - Configure connection pooling

---

## 📞 Support & Resources

- **IBM MQ Documentation:** https://www.ibm.com/docs/en/ibm-mq/
- **PostgreSQL Documentation:** https://www.postgresql.org/docs/
- **pymqi Documentation:** https://pythonhosted.org/pymqi/

---

**Setup completed by:** Claude Code
**Last Updated:** 2026-03-08
