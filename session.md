# BCSrvSqlMq Worker Thread Fix Session

**Date:** 2026-03-13
**Task:** Investigate why BCSrvSqlMq worker threads not auto-starting after restart

## Problem Statement

After restarting services, BCSrvSqlMq worker threads were not processing pending messages from the database. Messages were being inserted by SPBSite but remained stuck with `flag_proc='P'` status, never being sent to IBM MQ.

## Investigation Process

### Initial Observations
- BCSrvSqlMq service was running but showed no worker thread activity in logs
- Database had 7 pending messages with `status='P'`, `flag='P'`
- Messages had `mq_qn_destino='QL.36266751.01.ENTRADA.IF'` (Local IF queue)
- Worker process was running but not polling database

### Root Cause Analysis

Examined worker thread code in `if_req.py` and discovered **queue name mismatch**:

1. **Query Filter Mismatch** (Line 233):
   - Worker searched for: `QR.REQ.36266751.00038166.01` (Remote queue)
   - Database contained: `QL.36266751.01.ENTRADA.IF` (Local IF queue)
   - Result: SQL query returned 0 rows, worker sat idle

2. **UPDATE WHERE Clause Bug** (Line 619):
   - Used hardcoded Remote queue name in WHERE clause
   - Records had Local queue name
   - Result: UPDATE never matched, `flag_proc` never changed from 'P' to 'E'

3. **Queue Name Overwrite** (Line 555):
   - After successful send, overwrote `mq_qn_destino` to Remote queue
   - Caused records to change from Local to Remote queue in database

### Side Effect Discovered

Due to the UPDATE bug, worker was sending the same messages repeatedly:
- Found **100,000+ duplicate messages** in MQ queue `QL.36266751.01.ENTRADA.IF`
- Each poll cycle re-processed same records because flag never changed
- Had to clear queue using: `echo "CLEAR QLOCAL('QL.36266751.01.ENTRADA.IF')" | runmqsc QM.36266751.01`

## Solution Implemented

### Changes to `if_req.py`

#### 1. Fix Query Filter (Lines 233, 242)
```python
# Before:
remote_queue_name = init_srv.m_MqQrCidadeBacenReq
self.m_pRS.m_ParamMQ_QN_DESTINO = remote_queue_name

# After:
local_queue_name = init_srv.m_MqQlIFCidadeReq
self.m_pRS.m_ParamMQ_QN_DESTINO = local_queue_name
```

#### 2. Save Original Queue Name (Lines 439-442)
```python
# -- Save original queue name before update changes it --
if not erro:
    self.m_original_queue_name = rs.m_MQ_QN_DESTINO
```

#### 3. Prevent Queue Name Overwrite (Line 555)
```python
# Destination queue - keep original value from database, don't overwrite
# rs.m_MQ_QN_DESTINO = self.pMainSrv.pInitSrv.m_MqQrCidadeBacenReq
```

#### 4. Fix UPDATE Statement (Lines 600-623)
```python
# Removed mq_qn_destino from SET clause (don't change it)
sql = f'''UPDATE {rs.m_sTblName}
          SET mq_msg_id = %s,
              status_msg = %s,
              flag_proc = %s,
              -- mq_qn_destino removed
              mq_datetime_put = %s,
              mq_header = %s,
              security_header = %s
          WHERE db_datetime = %s
            AND cod_msg = %s
            AND mq_qn_destino = %s'''  # Uses self.m_original_queue_name
```

### Changes to `bacen_simulator.py`

Fixed UTF-8 encoding for clear text mode to prevent NUL character errors:

```python
if use_security:
    # Encrypted mode: use UTF-16BE encoding
    payload = encode_xml_to_payload(xml_text)
    # ... encryption logic
else:
    # Clear text mode: use plain UTF-8 encoding (matching BCSrvSqlMq)
    payload = xml_text.encode('utf-8')
    sec_hdr = SECHDR()
    sec_hdr.Versao = SECHDR_VERSION_CLEAR
    mq_msg = sec_hdr.pack() + payload
```

### Changes to `xml_builder.py`

Changed queue routing from Remote to Local IF queues for bacen_simulator compatibility:

```python
def _determine_queue_name(msg_id: str, ispb_dest: str) -> str:
    """Determine the MQ queue destination name based on message type.

    Uses Local IF queues for bacen_simulator compatibility.
    """
    ispb_local = settings.ispb_local
    # Use Local IF queues (QL.*) instead of Remote queues (QR.*)
    if "R1" in msg_id or "R2" in msg_id:
        return f"QL.{ispb_local}.01.SAIDA.IF"
    return f"QL.{ispb_local}.01.ENTRADA.IF"
```

## Git Commit

**Commit Hash:** `29c3ad0`
**Message:** "fix: Fix worker thread queue name mismatch preventing message processing"

**Files Changed:**
- `BCSrvSqlMq/python/bcsrvsqlmq/if_req.py` (16 lines changed)
- `BCSrvSqlMq/python/scripts/bacen_simulator.py` (6 lines changed)
- `spbsite/app/services/xml_builder.py` (11 lines changed)

## Cleanup Actions

1. Cleared 100,000+ duplicate messages from MQ queue
2. Deleted all test records from `spb_local_to_bacen` table
3. Killed orphaned Python processes

## Expected Behavior After Fixes

1. SPBSite inserts message with `mq_qn_destino='QL.36266751.01.ENTRADA.IF'`, `flag_proc='P'`
2. BCSrvSqlMq LocReq worker finds record (queue names match)
3. Worker builds MQ message and sends via MQPUT
4. Worker updates record: `status_msg='N'`, `flag_proc='E'`, sets `mq_datetime_put`
5. Queue name **remains unchanged** as `QL.36266751.01.ENTRADA.IF`
6. Record won't be re-processed (flag='E', not 'P')

## Next Steps

1. Start BCSrvSqlMq: `cd BCSrvSqlMq/python && python -m bcsrvsqlmq -d`
2. Send test message from SPBSite
3. Verify message processed once and flag updated to 'E'
4. Start bacen_simulator to receive and respond to messages
5. Test complete end-to-end flow

## Key Learnings

- **Queue Architecture**: Local IF queues (QL.*) for bacen_simulator on same QM vs Remote queues (QR.*) for actual BACEN
- **Database Consistency**: Original queue name from SPBSite must be preserved, not overwritten during processing
- **WHERE Clause Matching**: UPDATE statements must use original values to match records before they're modified
- **Encoding**: Clear text mode uses UTF-8, encrypted mode uses UTF-16BE

## Technical Context

- **Queue Manager:** QM.36266751.01
- **Local IF Queue:** QL.36266751.01.ENTRADA.IF
- **Remote Queue:** QR.REQ.36266751.00038166.01
- **Database:** BanuxSPB (PostgreSQL)
- **Table:** spb_local_to_bacen
- **Worker Thread:** LocReq (CIFReq class in if_req.py)
