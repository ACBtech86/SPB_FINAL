# IBM MQ Quick Reference - BCSrvSqlMq
## FINVEST ISPB 36266751

---

## Setup Checklist

```
□ Install IBM MQ 9.4.5.0 (Installation name: FinvestDTVM)
□ Set service MQ_FinvestDTVM to use Local System account
□ Run setup_mq_36266751.cmd as Administrator
□ Verify 8 queues created
□ Test Python application
```

---

## Queue Names

### Local Queues (FROM Bacen TO Finvest)
```
QL.REQ.00038166.36266751.01  (Request)
QL.RSP.00038166.36266751.01  (Response)
QL.REP.00038166.36266751.01  (Report)
QL.SUP.00038166.36266751.01  (Support)
```

### Remote Queues (FROM Finvest TO Bacen)
```
QR.REQ.36266751.00038166.01  (Request)
QR.RSP.36266751.00038166.01  (Response)
QR.REP.36266751.00038166.01  (Report)
QR.SUP.36266751.00038166.01  (Support)
```

---

## Essential Commands

### Queue Manager Operations
```cmd
# Check status
dspmq

# Start queue manager
strmqm QM.36266751.01

# Stop queue manager (immediate)
endmqm -i QM.36266751.01

# Delete queue manager (WARNING!)
dltmqm QM.36266751.01
```

### Service Operations
```cmd
# Start service
net start "MQ_FinvestDTVM"

# Stop service
net stop "MQ_FinvestDTVM"

# Check service status
sc query MQ_FinvestDTVM
```

### Queue Verification
```cmd
# Interactive MQSC
runmqsc QM.36266751.01

# Then run:
DISPLAY QLOCAL(QL.REQ.00038166.36266751.01)
DISPLAY QREMOTE(QR.REQ.36266751.00038166.01)
END
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Service Error 1069 | Set service to use Local System account |
| Queue Manager exists | Run: `endmqm -i QM.36266751.01` then `dltmqm QM.36266751.01` |
| Script fails | Run as Administrator |
| Queues not found | Run `setup_mq_36266751.cmd` |

---

## File Paths

```
Script:         setup_mq_36266751.cmd
Config:         BCSrvSqlMq.ini
MQ Install:     C:\Program Files\IBM\MQ
MQ Binaries:    C:\Program Files\IBM\MQ\bin
```

---

## Configuration Snippet

```ini
[MQSeries]
MQServer=localhost
QueueManager=QM.36266751.01
QueueTimeout=30
QLBacenCidadeReq=QL.REQ.00038166.36266751.01
QLBacenCidadeRsp=QL.RSP.00038166.36266751.01
QLBacenCidadeRep=QL.REP.00038166.36266751.01
QLBacenCidadeSup=QL.SUP.00038166.36266751.01
QRCidadeBacenReq=QR.REQ.36266751.00038166.01
QRCidadeBacenRsp=QR.RSP.36266751.00038166.01
QRCidadeBacenRep=QR.REP.36266751.00038166.01
QRCidadeBacenSup=QR.SUP.36266751.00038166.01
```

---

## Success Check

```cmd
# Should show: STATUS(Running)
dspmq

# Should show 8 queues with AMQ8409I
runmqsc QM.36266751.01 < verification_script.mqsc
```

---

**Quick Setup Command:**
```cmd
cd "C:\Users\AntonioBosco\OneDrive - Finvest\Documentos\GitHub\BCSrvSqlMq"
.\setup_mq_36266751.cmd
```
