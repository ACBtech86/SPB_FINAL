# BCSrvSqlMq - Message Flows

## Overview

BCSrvSqlMq has 8 worker threads split into two directions:

| Direction | Threads | Flow |
|-----------|---------|------|
| **IF -> Bacen** (Outbound) | CIFReq, CIFRsp, CIFRep, CIFSup | DB -> MQ |
| **Bacen -> IF** (Inbound)  | CBacenReq, CBacenRsp, CBacenRep, CBacenSup | MQ -> DB |

---

## Certificate Usage

| Key / Certificate | File | Usage |
|-------------------|------|-------|
| **Finvest Private Key** | `finvest_sim.key` (sim) / `private.key` (prod) | Sign outbound msgs (`func_assinar`) / Decrypt inbound msgs (`func_de_cript`) |
| **Bacen Public Certificate** | `bacen_sim.cer` (sim) / `Bacen.cer` (prod) | Encrypt outbound msgs (`func_cript`) / Verify inbound signatures (`func_verify_ass`) |

INI mapping:
- `privatekeyfile` = Finvest private key
- `certificatefile` = Bacen public certificate

---

## Security Protocol Versions

| Version | SECHDR Size | RSA | Hash | Symmetric | Status |
|---------|-------------|-----|------|-----------|--------|
| **V1** (Versao=0x01) | 332 bytes | RSA-1024 | MD5/SHA-1 | 3DES-168 | Legacy (2001-2024) |
| **V2** (Versao=0x02) | 588 bytes | RSA-2048 | SHA-256 | 3DES-168 | **Current** (2024+) |

Per Manual de Seguranca do SFN v5 (BACEN 2024 update).

---

## Flow 1: IF -> Bacen (Outbound)

```mermaid
graph TD
    DB_OUT[("PostgreSQL<br/>spb_local_to_bacen<br/>flag_proc = P")]
    IFREQ["CIFReq Thread<br/>if_req.py"]
    SIGN["SIGN<br/>Finvest Private Key<br/>RSA-2048 + SHA-256"]
    ENCRYPT["ENCRYPT<br/>Bacen Public Cert<br/>3DES + RSA-2048"]
    QL_IF["QL.36266751.01.ENTRADA.IF"]
    QR_REQ["QR.REQ.36266751.00038166.01"]
    DB_UPD[("PostgreSQL<br/>flag_proc P to E<br/>+ spb_log_bacen")]
    BC_QM["BACEN Queue Manager"]

    DB_OUT -->|"SELECT flag_proc=P"| IFREQ
    IFREQ -->|"Build SECHDR 588B<br/>Latin-1 to UTF-16BE"| SIGN
    SIGN --> ENCRYPT
    ENCRYPT -->|"MQPUT syncpoint"| QL_IF
    QL_IF --> QR_REQ
    IFREQ -->|"Update DB + MQCMIT"| DB_UPD
    QR_REQ -->|"MQ Channel"| BC_QM

    style DB_OUT fill:#e8f5e9,stroke:#2e7d32
    style DB_UPD fill:#e8f5e9,stroke:#2e7d32
    style SIGN fill:#fff8e1,stroke:#f57f17
    style ENCRYPT fill:#fff8e1,stroke:#f57f17
    style QL_IF fill:#ede7f6,stroke:#4527a0
    style QR_REQ fill:#ede7f6,stroke:#4527a0
    style BC_QM fill:#ffcdd2,stroke:#c62828
    style IFREQ fill:#bbdefb,stroke:#1565c0
```

### Outbound Steps:
1. Poll DB for pending records (`flag_proc='P'`)
2. Read XML message from `spb_local_to_bacen.msg` column
3. Build Security Header (SECHDR V2, 588 bytes)
4. Convert XML: Latin-1 -> UTF-16BE (byte swap)
5. **Sign** payload with **Finvest private key** (RSA-2048 + SHA-256)
6. **Encrypt** payload with **Bacen public certificate** (3DES + RSA-2048 key wrap)
7. MQPUT `SECHDR + encrypted_payload` under syncpoint
8. Update app record `flag_proc = 'P' -> 'E'`
9. Insert log record in `spb_log_bacen`
10. MQCMIT + DB COMMIT (atomic)

---

## Flow 2: Bacen -> IF (Inbound)

```mermaid
graph TD
    BC_QM["BACEN Queue Manager"]
    QL_BC["QL.REQ.00038166.36266751.01"]
    BCREQ["CBacenReq Thread<br/>bacen_req.py"]
    DECRYPT["DECRYPT<br/>Finvest Private Key<br/>RSA-2048 unwrap 3DES"]
    VERIFY["VERIFY SIGNATURE<br/>Bacen Public Cert<br/>RSA-2048 + SHA-256"]
    PARSE["Parse XML<br/>Extract NuOpe, CodMsg<br/>GEN0001, GEN0002, GEN0003"]
    DB_IN[("PostgreSQL<br/>INSERT spb_bacen_to_local<br/>INSERT spb_log_bacen<br/>MQCMIT + DB COMMIT")]

    BC_QM -->|"MQ Channel"| QL_BC
    QL_BC -->|"MQGET exclusive syncpoint"| BCREQ
    BCREQ -->|"Parse SECHDR 588B"| DECRYPT
    DECRYPT --> VERIFY
    VERIFY -->|"UTF-16BE to Latin-1"| PARSE
    PARSE -->|"INSERT + COMMIT"| DB_IN

    style BC_QM fill:#ffcdd2,stroke:#c62828
    style QL_BC fill:#ede7f6,stroke:#4527a0
    style DECRYPT fill:#fff8e1,stroke:#f57f17
    style VERIFY fill:#fff8e1,stroke:#f57f17
    style BCREQ fill:#bbdefb,stroke:#1565c0
    style PARSE fill:#bbdefb,stroke:#1565c0
    style DB_IN fill:#e8f5e9,stroke:#2e7d32
```

### Inbound Steps:
1. MQGET from `QL.REQ.00038166.36266751.01` (exclusive, syncpoint, wait)
2. Parse Security Header (auto-detect V1 332 bytes or V2 588 bytes)
3. **Decrypt** payload with **Finvest private key** (RSA-2048 unwrap 3DES key, then 3DES-CBC)
4. **Verify signature** with **Bacen public certificate** (RSA-2048 + SHA-256)
5. Decode XML: UTF-16BE -> Latin-1
6. Parse XML to extract NuOpe, CodMsg, Emissor, Destinatario
7. Handle special messages (GEN0001 Echo, GEN0002 Log, GEN0003 UltMsg)
8. INSERT message into `spb_bacen_to_local`
9. INSERT audit record into `spb_log_bacen`
10. MQCMIT + DB COMMIT (atomic)

---

## Complete Architecture

```mermaid
graph LR
    subgraph DB ["PostgreSQL"]
        TBL_OUT[("spb_local_to_bacen")]
        TBL_IN[("spb_bacen_to_local")]
        TBL_LOG[("spb_log_bacen")]
    end

    subgraph SRV ["BCSrvSqlMq - 8 Threads"]
        IF_REQ["CIFReq"]
        IF_RSP["CIFRsp"]
        BC_RSP["CBacenRsp"]
        BC_REQ["CBacenReq"]
    end

    subgraph MQ ["IBM MQ - QM.36266751.01"]
        QL_E["ENTRADA.IF"]
        QL_S["SAIDA.IF"]
        QR_REQ2["QR.REQ..."]
        QR_RSP2["QR.RSP..."]
        QL_REQ2["QL.REQ.00038166..."]
        QL_RSP2["QL.RSP.00038166..."]
    end

    BC_NET["BACEN / RSFN"]

    TBL_OUT --> IF_REQ
    TBL_OUT --> IF_RSP
    IF_REQ --> QL_E
    IF_RSP --> QL_S
    QL_E --> QR_REQ2
    QL_S --> QR_RSP2
    QR_REQ2 --> BC_NET
    QR_RSP2 --> BC_NET

    BC_NET --> QL_REQ2
    BC_NET --> QL_RSP2
    QL_REQ2 --> BC_REQ
    QL_RSP2 --> BC_RSP
    BC_REQ --> TBL_IN
    BC_RSP --> TBL_IN
    BC_REQ --> TBL_LOG
    IF_REQ --> TBL_LOG

    style DB fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style SRV fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style MQ fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style BC_NET fill:#ffcdd2,stroke:#c62828
```

---

## Security Detail -- Message Envelope V2

```mermaid
graph LR
    subgraph HDR ["SECHDR V2 - 588 bytes"]
        H1["C01 TamSecHeader 2B"]
        H2["C02 Versao 1B"]
        H6["C06 AlgAssymKey 1B<br/>RSA-2048"]
        H7["C07 AlgSymKey 1B<br/>3DES-168"]
        H9["C09 AlgHash 1B<br/>SHA-256"]
        H14["C14 SymKeyCifr 256B<br/>RSA wrapped 3DES key"]
        H15["C15 HashCifrSign 256B<br/>RSA digital signature"]
    end

    subgraph PL ["Payload"]
        XML["XML Document<br/>UTF-16BE encoded<br/>3DES-CBC encrypted"]
    end

    H1 --- H2
    H2 --- H6
    H6 --- H7
    H7 --- H9
    H9 --- H14
    H14 --- H15
    H15 --- XML

    style HDR fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    style PL fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
```

### V1 vs V2 Header Comparison

| Field | V1 (332 bytes) | V2 (588 bytes) |
|-------|---------------|---------------|
| C01 TamSecHeader | 0x014C (332) | 0x024C (588) |
| C02 Versao | 0x01 | 0x02 |
| C04-C05 | Reservado (2B) | TratamentoEspecial (1B) + Reservado (1B) |
| C06 AlgAssymKey | 0x01 (RSA-1024) | 0x02 (RSA-2048) |
| C09 AlgHash | 0x01 (MD5) / 0x02 (SHA-1) | 0x03 (SHA-256) |
| C14 SymKeyCifr | 1+127 = 128 bytes | 256 bytes |
| C15 HashCifrSign | 1+127 = 128 bytes | 256 bytes |

The inbound handler auto-detects V1/V2 from the first 2 bytes (TamSecHeader).

---

## Bacen Simulator

The Bacen Simulator (`python/scripts/bacen_simulator.py`) acts as the Central Bank side for local testing. It runs on the **same queue manager** and uses simulation certificates to exchange messages with the Finvest server.

### Simulator Architecture

```mermaid
graph LR
    IF_REQ["CIFReq<br/>outbound DB to MQ"]
    QL_IF["QL...ENTRADA.IF"]
    SIM_RCV["Simulator<br/>Receive + Decrypt"]
    SIM_SND["Simulator<br/>Sign + Encrypt"]
    QL_BC["QL.RSP.00038166..."]
    BC_RSP["CBacenRsp<br/>inbound MQ to DB"]

    IF_REQ -->|"sign finvest_sim.key<br/>encrypt bacen_sim.cer"| QL_IF
    QL_IF -->|"MQGET"| SIM_RCV
    SIM_RCV -->|"decrypt bacen_sim.key<br/>verify finvest_sim.cer"| SIM_SND
    SIM_SND -->|"sign bacen_sim.key<br/>encrypt finvest_sim.cer"| QL_BC
    QL_BC -->|"MQGET"| BC_RSP

    style IF_REQ fill:#bbdefb,stroke:#1565c0
    style BC_RSP fill:#bbdefb,stroke:#1565c0
    style QL_IF fill:#ede7f6,stroke:#4527a0
    style QL_BC fill:#ede7f6,stroke:#4527a0
    style SIM_RCV fill:#ffcdd2,stroke:#c62828
    style SIM_SND fill:#ffcdd2,stroke:#c62828
```

### Simulation Certificates

| Certificate | Key Size | Used By | Purpose |
|-------------|----------|---------|---------|
| `finvest_sim.key` | RSA-2048 | Finvest server | Sign outbound / Decrypt inbound |
| `finvest_sim.cer` | RSA-2048 | Bacen simulator | Encrypt to Finvest / Verify Finvest signatures |
| `bacen_sim.key` | RSA-2048 | Bacen simulator | Sign outbound / Decrypt inbound |
| `bacen_sim.cer` | RSA-2048 | Finvest server | Encrypt to Bacen / Verify Bacen signatures |

### Simulator Menu

| Option | Action | Queue | Direction |
|--------|--------|-------|-----------|
| 1. Browse queue depths | Show CURDEPTH of all queues | All | Read-only |
| 2. Receive from Finvest | MQGET + decrypt + verify | `QL.36266751.01.*.IF` | Finvest -> Bacen |
| 3. Send to Finvest | Sign + encrypt + MQPUT | `QL.*.00038166.36266751.01` | Bacen -> Finvest |
| 4. Browse messages | Peek without removing | Any queue | Read-only |

### How to Run

```bash
cd /home/ubuntu/SPBFinal/SPB_FINAL
source venv/bin/activate

# Terminal 1: Finvest server
cd BCSrvSqlMq/python
python -m bcsrvsqlmq -d

# Terminal 2: Bacen auto-responder
cd BCSrvSqlMq
python bacen_auto_responder.py

# Terminal 3: Visual flow monitor (recommended)
python monitor_live.py --inject
```

### End-to-End Test Flow

1. Insert test message in DB (`test_db_insert.py`) -> `spb_local_to_bacen` with `flag_proc='P'`
2. Finvest server picks it up -> signs with `finvest_sim.key` -> encrypts with `bacen_sim.cer` -> MQPUT
3. Bacen simulator receives -> decrypts with `bacen_sim.key` -> verifies with `finvest_sim.cer` -> displays XML
4. Bacen simulator sends response -> signs with `bacen_sim.key` -> encrypts with `finvest_sim.cer` -> MQPUT
5. Finvest server receives -> decrypts with `finvest_sim.key` -> verifies with `bacen_sim.cer` -> INSERT to DB

---

## Queue Naming Convention

| Pattern | Description | Example |
|---------|-------------|---------|
| `QL.{type}.{dest}.{orig}.{seq}` | Local queues (MQGET inbound) | `QL.REQ.00038166.36266751.01` |
| `QR.{type}.{orig}.{dest}.{seq}` | Remote queue defs (MQPUT outbound) | `QR.REQ.36266751.00038166.01` |
| `QL.{ISPB}.{seq}.{stage}.IF` | IF staging queues (local) | `QL.36266751.01.ENTRADA.IF` |

**Types:** REQ (Request), RSP (Response), REP (Report), SUP (Suporte)

---

## 4 Message Types

| Type | Outbound (IF->Bacen) | Inbound (Bacen->IF) |
|------|---------------------|---------------------|
| **REQ** (Request) | CIFReq: DB->MQPUT new requests | CBacenReq: MQGET->DB incoming requests |
| **RSP** (Response) | CIFRsp: DB->MQPUT responses | CBacenRsp: MQGET->DB incoming responses |
| **REP** (Report) | CIFRep: DB->MQPUT delivery reports | CBacenRep: MQGET->DB incoming reports |
| **SUP** (Suporte) | CIFSup: DB->MQPUT support msgs | CBacenSup: MQGET->DB incoming support |
