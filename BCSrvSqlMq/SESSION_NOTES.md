# BCSrvSqlMq - Session Notes (2026-03-05)

## Summary

End-to-end message flow through IBM MQ was successfully tested. A test message was inserted in the DB, the server picked it up, did MQPUT to the queue, committed, and updated the DB.

## What Was Done

### 1. Fixed `spb_log_bacen` table schema mismatch
- **Problem**: `spb_log_bacen` table had `flag_proc NOT NULL` without a DEFAULT, but `CSTRLogRS.COLUMNS` doesn't include `flag_proc`. INSERT failed with "o valor nulo na coluna 'flag_proc' viola a restrição de não-nulo".
- **Fix**: `ALTER TABLE spb_log_bacen ALTER COLUMN flag_proc SET DEFAULT 'N'`

### 2. Fixed INI file path resolution (`__main__.py`)
- **Problem**: When running `py -m bcsrvsqlmq -d`, `sys.argv[0]` points to `python/bcsrvsqlmq/__main__.py`. The old code only searched exe_dir and parent, missing the INI at the repo root. With no INI found, all defaults were used (wrong DB name `BCSPB` instead of `bcspbstr`), causing psycopg2 to get a Portuguese error message with Latin-1 characters that it couldn't decode as UTF-8.
- **Fix**: Added grandparent directory and CWD to the search path list in `__main__.py`.

### 3. Added traceback to error handler (`thread_mq.py`)
- Added `import traceback` and `traceback.format_exc()` to the 8099 error handler in `task_thread()` so exceptions show full stack traces in the log.

## End-to-End Test Result

```
MQPUT OK qmgr=QM.36266751.01 queue=QR.REQ.36266751.00038166.01 len=1388
MQCMIT OK
```

- **DB**: `spb_local_to_bacen` row updated `flag_proc='P' -> 'E'`
- **DB**: `spb_log_bacen` row inserted (cod_msg=GEN0014, nu_ope=20260305000001)
- **MQ**: Message on queue `QL.36266751.01.ENTRADA.IF` with `CURDEPTH(1)`

## Remaining Issues

### `bacen_rep.py:288` - monta_audit() argument mismatch
- Error: `CMainSrv.monta_audit() takes 4 positional arguments but 5 were given`
- The `bacen_rep.py` calls `self.pMainSrv.monta_audit(self.m_t, self.m_md, self.m_buflen, self.m_buffermsg)` (4 args + self = 5), but `CMainSrv.monta_audit()` signature is `monta_audit(self, mq_header, sec_header, msg_xml)` (3 args + self = 4).
- Need to fix the call sites in bacen_rep.py (and likely bacen_req.py, bacen_rsp.py, bacen_sup.py) to match the method signature.

### TripleDES deprecation warning
- `openssl_wrapper.py:158`: TripleDES moved to `cryptography.hazmat.decrepit.ciphers.algorithms.TripleDES`
- Cosmetic only, will need updating before cryptography 48.0.0

## Files Modified (Uncommitted)

1. `python/bcsrvsqlmq/__main__.py` - INI path search fix
2. `python/bcsrvsqlmq/thread_mq.py` - Added traceback import and full traceback in error handler
3. `python/bcsrvsqlmq/init_srv.py` - Property aliases (m_QueueMgr, m_DBUser), MQ channel/conninfo attributes
4. `python/bcsrvsqlmq/bacen_req.py` - connect_qmgr() usage
5. `python/bcsrvsqlmq/bacen_rsp.py` - connect_qmgr() usage
6. `python/bcsrvsqlmq/bacen_rep.py` - connect_qmgr() usage
7. `python/bcsrvsqlmq/bacen_sup.py` - connect_qmgr() usage
8. `python/bcsrvsqlmq/if_req.py` - connect_qmgr() usage
9. `python/bcsrvsqlmq/if_rsp.py` - connect_qmgr() usage
10. `python/bcsrvsqlmq/if_rep.py` - connect_qmgr() usage
11. `python/bcsrvsqlmq/if_sup.py` - connect_qmgr() usage
12. `python/scripts/test_db_insert.py` - Fixed INSERT columns

## DB Changes Applied (Not in Code)

- `ALTER TABLE spb_log_bacen ALTER COLUMN flag_proc SET DEFAULT 'N'`
- `ALTER TABLE spb_bacen_to_local ADD COLUMN flag_proc CHAR(1) NOT NULL DEFAULT 'N'` (from prior session)

## How to Run

```bash
cd python
py -m bcsrvsqlmq -d
```

## How to Insert a Test Message

```bash
cd python
py scripts/test_db_insert.py
```

## Architecture Reference

- **8 worker threads**: CBacenReq/Rsp/Rep/Sup (inbound MQ->DB) + CIFReq/Rsp/Rep/Sup (outbound DB->MQ)
- **MQ**: QM.36266751.01 on localhost(1414) via FINVEST.SVRCONN channel (TCP client mode, pymqi uses mqic.dll)
- **DB**: PostgreSQL `bcspbstr` on localhost:5432
- **Security**: OpenSSL certificates with 3DES+RSA encryption, digital signatures (SecurityEnable=S)
- **IF queues**: QL.36266751.01.ENTRADA/SAIDA/REPORT/SUPORTE.IF (local queues for IF-side staging)
- **Bacen queues**: QL.REQ/RSP/REP/SUP.00038166.36266751.01 (local) + QR.REQ/RSP/REP/SUP.36266751.00038166.01 (remote)

## Next Steps

1. Fix `monta_audit()` argument mismatch in bacen_*.py files
2. Commit all changes
3. Test inbound flow (put a message on QL.REQ queue -> server reads -> inserts to DB)
4. Address TripleDES deprecation warning
