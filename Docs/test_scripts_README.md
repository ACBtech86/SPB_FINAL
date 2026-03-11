# SPB E2E Test Scripts

Automated scripts for testing the complete SPB message flow.

## Overview

These scripts test the end-to-end flow:
```
SPBSite → Database → BCSrvSqlMq → IBM MQ → BACEN (simulated) → IBM MQ → BCSrvSqlMq → Database → SPBSite
```

## Prerequisites

1. **IBM MQ** running with Queue Manager `QM.36266751.01`
2. **SPBSite** web server running on port 8000
3. **BCSrvSqlMq** service running
4. **Python dependencies** installed:
   ```bash
   pip install pymqi
   ```

## Quick Start

### Automated Test (Bash)

```bash
chmod +x test_scripts/quick_test.sh
./test_scripts/quick_test.sh
```

This runs the complete test automatically.

### Manual Step-by-Step

#### 1. Check MQ Status

```bash
python test_scripts/check_mq_status.py
```

**Verifies:**
- Queue Manager is running
- All 8 queues are created
- Queues are accessible

**Expected Output:**
```
✅ Connected to Queue Manager: QM.36266751.01
✅ QL.REQ.00038166.36266751.01  Type: Local    Depth:    0/5000
✅ QL.RSP.00038166.36266751.01  Type: Local    Depth:    0/5000
...
✅ All queues are ready!
```

#### 2. Submit Test Message

```bash
python test_scripts/submit_test_message.py
```

**Creates:**
- Test message in `spb_local_to_bacen` table
- Status: `P` (Pending)
- Auto-generated operation number

**Expected Output:**
```
✅ Test message created successfully!
Operation Number: 20260307120000
Message Code: SPB0001
Status: P (Pending)
```

**Operation number** is saved to `test_scripts/last_operation.txt`

#### 3. Browse Outbound Queue

Wait ~5 seconds for BCSrvSqlMq to process, then:

```bash
python test_scripts/browse_mq_queue.py QR.REQ.36266751.00038166.01
```

**Verifies:**
- Message sent to MQ by BCSrvSqlMq
- Queue depth = 1
- Message contains operation number

**Expected Output:**
```
Queue Depth: 1 messages

Message 1:
  Message ID: 414d51204...
  Operation Number: 20260307120000
```

#### 4. Simulate BACEN Response

```bash
# Get operation number
NU_OPE=$(cat test_scripts/last_operation.txt)

# Send COA (Confirmation of Arrival)
python test_scripts/simulate_bacen_response.py --operation-number $NU_OPE --response-type COA
```

**Response Types:**
- `COA` - Confirmation of Arrival
- `COD` - Confirmation of Delivery
- `REP` - Report
- `ERR` - Error (use `--error-code 9999`)

**Expected Output:**
```
✅ Response message sent successfully!
Queue: QL.RSP.00038166.36266751.01
Message ID: 414d51204...
```

#### 5. Browse Response Queue

Wait ~5 seconds for BCSrvSqlMq to receive, then:

```bash
python test_scripts/browse_mq_queue.py QL.RSP.00038166.36266751.01
```

**Verifies:**
- Response received from MQ
- Or queue empty (already processed by BCSrvSqlMq)

#### 6. Verify in Database

```sql
-- Check original message status
SELECT nu_ope, status_msg, flag_proc, mq_msg_id_coa
FROM spb_local_to_bacen
WHERE nu_ope = '20260307120000';

-- Check response received
SELECT * FROM spb_bacen_to_local
WHERE nu_ope LIKE '%20260307120000%'
ORDER BY db_datetime DESC;
```

#### 7. Verify in SPBSite

1. Open http://localhost:8000
2. Login: `admin` / `admin`
3. Go to "Messages" → "Sent Messages"
4. Find message with operation number
5. Should show updated status with confirmation

## Scripts Reference

### check_mq_status.py

```bash
python test_scripts/check_mq_status.py
```

Checks IBM MQ Queue Manager and all queues.

**Exit Codes:**
- `0` - All OK
- `1` - Error

### submit_test_message.py

```bash
python test_scripts/submit_test_message.py
```

Creates test message in database.

**Outputs:**
- Console: Operation number and details
- File: `test_scripts/last_operation.txt`

### browse_mq_queue.py

```bash
python test_scripts/browse_mq_queue.py <queue_name> [max_messages]
```

**Examples:**
```bash
# Browse outbound requests
python test_scripts/browse_mq_queue.py QR.REQ.36266751.00038166.01

# Browse inbound responses (limit 20)
python test_scripts/browse_mq_queue.py QL.RSP.00038166.36266751.01 20
```

**Common Queues:**
- `QR.REQ.36266751.00038166.01` - Outbound requests to BACEN
- `QL.RSP.00038166.36266751.01` - Inbound responses from BACEN
- `QL.REP.00038166.36266751.01` - Inbound reports from BACEN
- `QL.SUP.00038166.36266751.01` - Inbound support messages

### simulate_bacen_response.py

```bash
python test_scripts/simulate_bacen_response.py --operation-number <NU_OPE> [--response-type <TYPE>] [--error-code <CODE>]
```

**Arguments:**
- `--operation-number` or `-o`: Required. Operation number to respond to
- `--response-type` or `-t`: COA, COD, REP, or ERR (default: COA)
- `--error-code` or `-e`: Error code (for ERR type)

**Examples:**
```bash
# Send Confirmation of Arrival
python test_scripts/simulate_bacen_response.py -o 20260307120000 -t COA

# Send Confirmation of Delivery
python test_scripts/simulate_bacen_response.py -o 20260307120000 -t COD

# Send Error
python test_scripts/simulate_bacen_response.py -o 20260307120000 -t ERR -e 9999
```

## Test Scenarios

### Scenario 1: Happy Path (COA)

```bash
# 1. Submit message
python test_scripts/submit_test_message.py
NU_OPE=$(cat test_scripts/last_operation.txt)

# 2. Wait for processing
sleep 10

# 3. Send COA response
python test_scripts/simulate_bacen_response.py -o $NU_OPE -t COA

# 4. Wait for response processing
sleep 10

# 5. Verify
python test_scripts/browse_mq_queue.py QL.RSP.00038166.36266751.01
```

### Scenario 2: Full Cycle (COA → COD)

```bash
NU_OPE=$(cat test_scripts/last_operation.txt)

# Send COA
python test_scripts/simulate_bacen_response.py -o $NU_OPE -t COA
sleep 10

# Send COD
python test_scripts/simulate_bacen_response.py -o $NU_OPE -t COD
sleep 10
```

### Scenario 3: Error Response

```bash
NU_OPE=$(cat test_scripts/last_operation.txt)

# Send error
python test_scripts/simulate_bacen_response.py -o $NU_OPE -t ERR -e 9999
sleep 10
```

## Troubleshooting

### Issue: "Cannot connect to Queue Manager"

**Check:**
```powershell
Get-Service MQ_FinvestDTVM
dspmq
```

**Fix:**
```cmd
strmqm QM.36266751.01
```

### Issue: "Queue not found"

**Check:**
```bash
echo "DISPLAY QLOCAL(*)" | runmqsc QM.36266751.01
```

**Fix:**
```cmd
cd BCSrvSqlMq
setup_mq_36266751.cmd
```

### Issue: "No module named 'pymqi'"

**Fix:**
```bash
pip install pymqi
```

### Issue: "Database error"

**Check:**
```bash
cd spbsite
python -c "from app.database import engine; print('OK')"
```

**Fix:**
```bash
cd spbsite
python -m app.seed
```

## Expected Timings

| Step | Time |
|------|------|
| Submit message | < 1 sec |
| BCSrvSqlMq processes | 1-10 sec |
| Send to MQ | < 1 sec |
| Simulate response | < 1 sec |
| Receive response | 1-10 sec |
| Update database | < 1 sec |

**Total:** ~15-30 seconds for complete cycle

## Output Files

- `test_scripts/last_operation.txt` - Last operation number created
- BCSrvSqlMq logs (if configured)
- SPBSite logs (if configured)

## Integration with VS Code

Add to `.vscode/tasks.json`:

```json
{
  "label": "Run E2E Test",
  "type": "shell",
  "command": "./test_scripts/quick_test.sh",
  "problemMatcher": []
}
```

Run with: `Ctrl+Shift+P` → "Tasks: Run Task" → "Run E2E Test"

## Next Steps

After successful test:
1. Test with real message types from catalog
2. Test multiple messages
3. Performance testing
4. Error handling testing
5. Integration with actual BACEN (when available)
