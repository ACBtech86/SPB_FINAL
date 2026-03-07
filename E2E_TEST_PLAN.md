# End-to-End Message Flow Test Plan

Complete testing guide for SPB message flow from SPBSite → BCSrvSqlMq → IBM MQ → Central Bank (simulated) → back.

---

## Test Objective

Verify complete message flow:
1. **SPBSite** submits message via web interface
2. **BCSrvSqlMq** picks up message and sends to IBM MQ
3. **IBM MQ** queues message for BACEN
4. **Simulate BACEN** response
5. **BCSrvSqlMq** receives response and updates database
6. **SPBSite** displays updated message status

---

## Prerequisites

### 1. Python Version

**IMPORTANT:** `pymqi` requires Python 3.12 or earlier. Python 3.13 is not compatible.

- **Using Python 3.13?** Use `test_scripts/simple_db_test.py` (no pymqi required)
- **Want full MQ testing?** Install Python 3.12 - See [PYTHON312_SETUP.md](PYTHON312_SETUP.md)

### 2. Services Required

- [x] PostgreSQL or SQLite database
- [x] IBM MQ Queue Manager (QM.36266751.01)
- [x] SPBSite web server
- [x] BCSrvSqlMq service

### 3. Configuration Check

**Database:**
- SPBSite: `spbsite.db` or PostgreSQL `spbsite`
- Catalog: `spb_messages.db` or PostgreSQL `spb_messages`
- BCSrvSqlMq: PostgreSQL `bcspbstr` (or configured database)

**IBM MQ:**
- Queue Manager: `QM.36266751.01`
- Queues created (8 total)

**ISPB Codes:**
- Finvest: `36266751`
- BACEN: `00038166`
- SELIC: `00038121`

---

## Test Setup

### Step 1: Verify IBM MQ is Running

```powershell
# Check service status
Get-Service MQ_FinvestDTVM

# Check queue manager
runmqsc QM.36266751.01
# In MQSC, type:
DISPLAY QMGR
DISPLAY QLOCAL(QL.REQ.00038166.36266751.01)
DISPLAY QLOCAL(QR.REQ.36266751.00038166.01)
end

# Or check with Python
python test_scripts/check_mq_status.py
```

### Step 2: Start SPBSite

```bash
cd spbsite
source venv/Scripts/activate  # or venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Verify:** http://localhost:8000 (should show login page)

### Step 3: Start BCSrvSqlMq

```bash
cd BCSrvSqlMq/python
source venv/Scripts/activate
python -m bcsrvsqlmq.main_srv
```

**Expected Output:**
```
BCSrvSqlMq Service Starting...
Connected to database: bcspbstr
Connected to Queue Manager: QM.36266751.01
Monitoring queues...
```

### Step 4: Verify Database Seeding

```bash
cd spbsite
python -m app.seed
```

This ensures message catalog is loaded.

---

## Test Execution

### Test Case 1: Submit Message from SPBSite

#### 1.1 Login to SPBSite

1. Open http://localhost:8000
2. Login: `admin` / `admin`
3. Should redirect to dashboard

#### 1.2 Submit a Test Message

**Option A: Via Web Interface**

1. Click "Messages" → "Send Message"
2. Select message type (e.g., `SPB0001` - Generic message)
3. Fill in required fields:
   - Destination: `00038166` (BACEN)
   - Operation Number: Auto-generated or manual
   - Message content (XML fields)
4. Click "Submit"

**Option B: Via Test Script**

```bash
cd test_scripts
python submit_test_message.py
```

#### 1.3 Expected Results

**SPBSite:**
- Message appears in "Messages" → "Sent Messages"
- Status: `P` (Pending) or `E` (Enviada - Sent)
- Record created in `spb_local_to_bacen` table

**Database Check:**
```sql
-- In spbsite database
SELECT db_datetime, nu_ope, cod_msg, status_msg, flag_proc
FROM spb_local_to_bacen
ORDER BY db_datetime DESC
LIMIT 5;
```

**Expected:**
- `status_msg`: `P` or `E`
- `flag_proc`: `N` (Not processed)

---

### Test Case 2: BCSrvSqlMq Processes Message

#### 2.1 Monitor BCSrvSqlMq Output

Watch the BCSrvSqlMq terminal for:

```
[TIMESTAMP] Processing message from database...
[TIMESTAMP] Operation Number: 20260307001
[TIMESTAMP] Message Code: SPB0001
[TIMESTAMP] Sending to queue: QR.REQ.36266751.00038166.01
[TIMESTAMP] Message sent successfully
[TIMESTAMP] MQ Message ID: 414D5120...
```

#### 2.2 Verify Message in MQ

```bash
# Check queue depth
echo "DISPLAY QLOCAL(QR.REQ.36266751.00038166.01) CURDEPTH" | runmqsc QM.36266751.01

# Browse messages (non-destructive)
python test_scripts/browse_mq_queue.py QR.REQ.36266751.00038166.01
```

**Expected:**
- Queue depth increased by 1
- Message visible in queue

#### 2.3 Expected Database Update

```sql
-- BCSrvSqlMq updates the record
SELECT status_msg, flag_proc, mq_msg_id
FROM spb_local_to_bacen
WHERE nu_ope = '20260307001';
```

**Expected:**
- `status_msg`: `E` (Enviada)
- `flag_proc`: `S` (Sim - processed)
- `mq_msg_id`: Set to MQ message ID

---

### Test Case 3: Simulate BACEN Response

Since we don't have actual BACEN connection, we'll simulate a response.

#### 3.1 Create Response Message

```bash
cd test_scripts
python simulate_bacen_response.py --operation-number 20260307001
```

This script will:
1. Read the original message from queue `QR.REQ.36266751.00038166.01`
2. Create a response message (ACK/COA/COD)
3. Put response in queue `QL.RSP.00038166.36266751.01`

#### 3.2 Expected Output

```
[INFO] Reading message from outbound queue...
[INFO] Found message: NU_OPE=20260307001
[INFO] Creating response message (COA - Confirmation of Arrival)
[INFO] Putting response in queue: QL.RSP.00038166.36266751.01
[SUCCESS] Response message sent
```

---

### Test Case 4: BCSrvSqlMq Receives Response

#### 4.1 Monitor BCSrvSqlMq Output

```
[TIMESTAMP] Message received from queue: QL.RSP.00038166.36266751.01
[TIMESTAMP] Response Type: COA (Confirmation of Arrival)
[TIMESTAMP] Original Operation: 20260307001
[TIMESTAMP] Correlation ID: 414D5120...
[TIMESTAMP] Updating database...
[TIMESTAMP] Response processed successfully
```

#### 4.2 Verify Database Update

```sql
-- Check response in database
SELECT db_datetime, nu_ope, status_msg, mq_msg_id_coa
FROM spb_local_to_bacen
WHERE nu_ope = '20260307001';
```

**Expected:**
- `status_msg`: `C` (Confirmada) or updated status
- `mq_msg_id_coa`: Set to response MQ message ID

Also check response table:
```sql
SELECT * FROM spb_bacen_to_local
WHERE nu_ope = '20260307001'
ORDER BY db_datetime DESC;
```

---

### Test Case 5: Verify in SPBSite

#### 5.1 Refresh SPBSite Interface

1. Go to "Messages" → "Sent Messages"
2. Find message with NU_OPE = `20260307001`
3. Click to view details

**Expected:**
- Status updated to show confirmation received
- Response details visible
- Timestamps updated

#### 5.2 Check Monitoring Dashboard

1. Go to "Monitoring" → "Dashboard"
2. Should show:
   - Total messages sent
   - Messages confirmed
   - Recent activity

---

## Test Scenarios

### Scenario 1: Simple Request-Response

```
SPBSite → BCSrvSqlMq → MQ Queue (Request) → Simulate Response →
BCSrvSqlMq → Database → SPBSite
```

**Message Types:**
- SPB0001 (Generic)
- Request → COA (Confirmation)

### Scenario 2: Request-Response-Acknowledgment

```
SPBSite → Request → COA → COD (Definitive Confirmation) → SPBSite
```

### Scenario 3: Error Handling

**Test negative acknowledgment:**
```bash
python simulate_bacen_response.py --operation-number 20260307001 --response-type ERR --error-code 9999
```

**Expected:**
- Status updated to error
- Error code visible in SPBSite
- Alert/notification in monitoring

---

## Monitoring Commands

### Real-time Monitoring

**Terminal 1 - SPBSite Logs:**
```bash
cd spbsite
tail -f logs/spbsite.log  # if logging to file
# Or watch terminal output
```

**Terminal 2 - BCSrvSqlMq Logs:**
```bash
cd BCSrvSqlMq/python
tail -f ../../Traces/bcsrvsqlmq.log  # if configured
# Or watch terminal output
```

**Terminal 3 - MQ Queue Depths:**
```bash
watch -n 2 'echo "DISPLAY QLOCAL(*) CURDEPTH" | runmqsc QM.36266751.01 | grep CURDEPTH'
```

**Terminal 4 - Database Activity:**
```bash
# PostgreSQL
watch -n 2 'psql -U postgres -d spbsite -c "SELECT COUNT(*) FROM spb_local_to_bacen WHERE status_msg = '\''P'\''; SELECT COUNT(*) FROM spb_local_to_bacen WHERE status_msg = '\''E'\'';"'

# SQLite
watch -n 2 'sqlite3 spbsite.db "SELECT status_msg, COUNT(*) FROM spb_local_to_bacen GROUP BY status_msg;"'
```

---

## Verification Checklist

### Pre-Test
- [ ] PostgreSQL/SQLite running
- [ ] IBM MQ service running
- [ ] Queue Manager created and started
- [ ] All 8 queues created
- [ ] SPBSite database seeded
- [ ] BCSrvSqlMq.ini configured correctly

### During Test
- [ ] SPBSite accessible at http://localhost:8000
- [ ] BCSrvSqlMq service running without errors
- [ ] Can login to SPBSite
- [ ] Can submit message from SPBSite
- [ ] Message appears in database
- [ ] BCSrvSqlMq picks up message
- [ ] Message sent to MQ queue
- [ ] Can simulate BACEN response
- [ ] Response received by BCSrvSqlMq
- [ ] Database updated with response
- [ ] SPBSite shows updated status

### Post-Test
- [ ] All messages processed
- [ ] No messages stuck in queues
- [ ] Database consistent
- [ ] Logs clean (no unexpected errors)

---

## Troubleshooting

### Issue: SPBSite won't start

**Check:**
```bash
cd spbsite
python -c "from app.database import engine; print('Database OK')"
```

**Fix:**
- Verify database URL in `.env`
- Run `python -m app.seed` to initialize

### Issue: BCSrvSqlMq can't connect to MQ

**Check:**
```bash
echo "DISPLAY QMGR" | runmqsc QM.36266751.01
```

**Fix:**
- Start queue manager: `strmqm QM.36266751.01`
- Check queue manager name in `BCSrvSqlMq.ini`

### Issue: Message stuck in Pending status

**Check:**
1. Is BCSrvSqlMq running?
2. Database connection OK?
3. Check BCSrvSqlMq logs

**Fix:**
```bash
# Restart BCSrvSqlMq
cd BCSrvSqlMq/python
python -m bcsrvsqlmq.main_srv
```

### Issue: Response not received

**Check:**
```bash
# Check if response is in queue
python test_scripts/browse_mq_queue.py QL.RSP.00038166.36266751.01
```

**Fix:**
- Verify BCSrvSqlMq is monitoring response queue
- Check correlation IDs match

---

## Expected Timings

| Step | Expected Time |
|------|---------------|
| Submit message via SPBSite | < 1 second |
| BCSrvSqlMq picks up message | 1-5 seconds (polling interval) |
| Send to MQ queue | < 1 second |
| Simulate BACEN response | Immediate (manual) |
| BCSrvSqlMq receives response | 1-5 seconds (polling interval) |
| Database update | < 1 second |
| SPBSite refresh | Immediate (page refresh) |

**Total end-to-end:** ~10-20 seconds (with manual simulation)

---

## Success Criteria

✅ **Test Passes If:**
1. Message submitted successfully from SPBSite
2. Message appears in `spb_local_to_bacen` with status `P`
3. BCSrvSqlMq processes and sends to MQ (status → `E`)
4. Message visible in MQ queue
5. Simulated response successfully created
6. BCSrvSqlMq receives and processes response
7. Database updated with response details
8. SPBSite shows updated message status
9. No errors in any service logs
10. All queues return to empty state

---

## Next Steps

After successful E2E test:
1. Test with different message types
2. Test error scenarios
3. Performance testing (multiple messages)
4. Load testing
5. Integration with actual BACEN (when available)

---

**Test Date:** _______________
**Tester:** _______________
**Result:** [ ] PASS  [ ] FAIL
**Notes:** _______________________________________________
