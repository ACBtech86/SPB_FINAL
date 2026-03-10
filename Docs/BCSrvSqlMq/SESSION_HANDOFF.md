# Session Handoff - BCSrvSqlMq V2 Security Update

**Date**: 2026-03-06
**Branch**: main
**Last commit**: `4a3f113` - Update SPB security header from V1 (332 bytes) to V2 (588 bytes)
**Pushed**: Yes, up to date with origin

---

## What Was Done

### V2 Security Header Update (BACEN Manual de Seguranca do SFN v5)

Migrated the entire SPB security layer from V1 (2001 legacy) to V2 (2024 BACEN update):

| Aspect | V1 (Old) | V2 (New) |
|--------|----------|----------|
| SECHDR size | 332 bytes | 588 bytes |
| RSA key | RSA-1024 | RSA-2048 |
| Hash | MD5 | SHA-256 |
| SymKeyCifr field | 128 bytes (1+127) | 256 bytes |
| HashCifrSign field | 128 bytes (1+127) | 256 bytes |
| TamSecHeader | 0x014C (332) | 0x024C (588) |
| Versao byte | 0x01 | 0x02 |

### Files Modified

- **python/bcsrvsqlmq/msg_sgr.py** - SECHDR V2 struct (588 bytes), V1 backward compat with auto-detect and `_unpack_v1()`
- **python/bcsrvsqlmq/thread_mq.py** - 256-byte crypto fields, zero IV for 3DES-CBC, `_rsa_size()` helper
- **python/bcsrvsqlmq/bacen_req.py** - Auto-detect V1/V2 from TamSecHeader bytes on inbound
- **python/bcsrvsqlmq/bacen_rsp.py** - Same V1/V2 auto-detection on inbound responses
- **python/bcsrvsqlmq/if_req.py** - Default to V2 protocol (RSA-2048, SHA-256, CA_SERPRO)
- **python/bcsrvsqlmq/if_rsp.py** - Same V2 defaults for outbound responses
- **python/bcsrvsqlmq/security/openssl_wrapper.py** - Added SHA-256 case (`digest_algo == 0x03`)
- **BCSrvSqlMq.ini** - Updated key file paths to sim certs

### Files Created

- **MESSAGE_FLOWS.md** - Full documentation with Mermaid diagrams, V1 vs V2 comparison, Bacen simulator section
- **python/scripts/bacen_simulator.py** - Interactive Bacen (Central Bank) simulator for end-to-end testing

### Key Technical Details

- **3DES-CBC zero IV**: Both encrypt and decrypt use `b'\x00' * 8` (matches C++ original and SPB spec)
- **V1 backward compatibility**: Inbound handlers auto-detect V1/V2 from first 2 bytes of security header
- **RSA-2048 output**: 256 bytes fits exactly in V2's 256-byte fields (no more split 1+127 byte hack)
- **Simulation certificates**: 2048-bit RSA keypairs in `certificates/` folder (finvest_sim.key/cer, bacen_sim.key/cer)
- **Crypto round-trip verified**: Finvest sign+encrypt -> Bacen decrypt+verify passed

---

## Pending Tasks

1. **Fix `monta_audit()` in bacen_rep.py** - Argument mismatch (4 args vs 3+self) from prior session
2. **TripleDES deprecation warning** - Move to `cryptography.hazmat.decrepit.ciphers.algorithms.TripleDES` (cosmetic)
3. **Full end-to-end test with MQ running** - Finvest server <-> Bacen simulator with real MQ queues
4. **Real certificates** - Replace sim certs with production BACEN-issued certs when available (Serial 1E70E52978116328, ISPB 36266751)

---

## How to Resume

```
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\GitHub\BCSrvSqlMq"
git pull  # should already be up to date
```

To run the Bacen simulator:
```
cd python
python -m scripts.bacen_simulator
```

To run the main service:
```
cd python
python -m bcsrvsqlmq.main
```
