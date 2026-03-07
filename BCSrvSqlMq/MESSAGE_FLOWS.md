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
flowchart TD
    subgraph FINVEST ["FINVEST (IF) -- ISPB 36266751"]
        DB_OUT[("PostgreSQL\n---------\nspb_local_to_bacen\nflag_proc = 'P'")]
        IFREQ["CIFReq Thread\n(if_req.py)"]
        DB_UPD[("PostgreSQL\n---------\nflag_proc 'P' -> 'E'\n+ INSERT spb_log_bacen")]
        QL_IF["QL.36266751.01.ENTRADA.IF\n(local staging queue)"]
    end

    subgraph SECURITY_OUT ["Security Layer -- Outbound (V2)"]
        SIGN["1. SIGN\nFinvest Private Key\nRSA-2048 + SHA-256\n-> 256B signature in SECHDR"]
        ENCRYPT["2. ENCRYPT\nBacen Public Cert\n3DES key wrapped with RSA-2048\npayload encrypted 3DES-CBC"]
    end

    subgraph MQ_OUT ["IBM MQ -- QM.36266751.01"]
        QR_REQ["QR.REQ.36266751.00038166.01\n(remote queue definition)"]
    end

    subgraph BACEN ["BACEN -- ISPB 00038166"]
        BC_QM["Bacen Queue Manager\nQL.REQ.00038166.36266751.01"]
    end

    DB_OUT -->|"1. SELECT WHERE\nflag_proc='P'"| IFREQ
    IFREQ -->|"2. Read XML\n3. Build SECHDR (588 bytes)\n4. Encode Latin-1 -> UTF-16BE"| SIGN
    SIGN --> ENCRYPT
    ENCRYPT -->|"5. MQPUT\n(syncpoint)\nSECHDR + encrypted payload"| QL_IF
    QL_IF --> QR_REQ
    IFREQ -->|"6. Update DB + MQCMIT"| DB_UPD
    QR_REQ -->|"MQ Channel\nto Bacen"| BC_QM

    style FINVEST fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style SECURITY_OUT fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style MQ_OUT fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style BACEN fill:#fce4ec,stroke:#b71c1c,stroke-width:2px
    style DB_OUT fill:#e8f5e9,stroke:#2e7d32
    style DB_UPD fill:#e8f5e9,stroke:#2e7d32
    style SIGN fill:#fff8e1,stroke:#f57f17
    style ENCRYPT fill:#fff8e1,stroke:#f57f17
    style QL_IF fill:#ede7f6,stroke:#4527a0
    style QR_REQ fill:#ede7f6,stroke:#4527a0
    style BC_QM fill:#ffcdd2,stroke:#c62828
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
flowchart TD
    subgraph BACEN ["BACEN -- ISPB 00038166"]
        BC_QM["Bacen Queue Manager\nsends encrypted message"]
    end

    subgraph MQ_IN ["IBM MQ -- QM.36266751.01"]
        QL_BC["QL.REQ.00038166.36266751.01\n(local queue -- Bacen msgs\narriving for Finvest)"]
    end

    subgraph SECURITY_IN ["Security Layer -- Inbound (V2)"]
        DECRYPT["1. DECRYPT\nFinvest Private Key\nRSA-2048 unwrap 3DES key\nthen 3DES-CBC decrypt"]
        VERIFY["2. VERIFY SIGNATURE\nBacen Public Cert\nRSA-2048 + SHA-256\ncheck hash matches"]
    end

    subgraph FINVEST ["FINVEST (IF) -- ISPB 36266751"]
        BCREQ["CBacenReq Thread\n(bacen_req.py)"]
        PARSE["Parse XML\n---------\nExtract: NuOpe, CodMsg\nEmissor, Destinatario\n---------\nSpecial: GEN0001 (Echo)\nGEN0002 (Log)\nGEN0003 (UltMsg)"]
        DB_IN[("PostgreSQL\n---------\nINSERT spb_bacen_to_local\nINSERT spb_log_bacen\nMQCMIT + DB COMMIT")]
    end

    BC_QM -->|"MQ Channel\nfrom Bacen"| QL_BC
    QL_BC -->|"1. MQGET\n(exclusive, syncpoint, wait)"| BCREQ
    BCREQ -->|"2. Parse SECHDR\n(588 bytes V2 / 332 bytes V1)"| DECRYPT
    DECRYPT --> VERIFY
    VERIFY -->|"3. Decode\nUTF-16BE -> Latin-1"| PARSE
    PARSE -->|"4. INSERT + COMMIT"| DB_IN

    style BACEN fill:#fce4ec,stroke:#b71c1c,stroke-width:2px
    style MQ_IN fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style SECURITY_IN fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style FINVEST fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
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
flowchart LR
    subgraph DB ["PostgreSQL -- bcspbstr"]
        TBL_OUT[("spb_local_to_bacen\n(outbound msgs)")]
        TBL_IN[("spb_bacen_to_local\n(inbound msgs)")]
        TBL_LOG[("spb_log_bacen\n(audit log)")]
        TBL_CTR[("spb_controle\n(control)")]
    end

    subgraph SRV ["BCSrvSqlMq Service"]
        direction TB
        subgraph OUT_THREADS ["Outbound Threads (DB -> MQ)"]
            IF_REQ["CIFReq"]
            IF_RSP["CIFRsp"]
            IF_REP["CIFRep"]
            IF_SUP["CIFSup"]
        end
        subgraph IN_THREADS ["Inbound Threads (MQ -> DB)"]
            BC_REQ["CBacenReq"]
            BC_RSP["CBacenRsp"]
            BC_REP["CBacenRep"]
            BC_SUP["CBacenSup"]
        end
        subgraph CRYPTO ["Security (V2)"]
            PRV["Finvest RSA-2048\nprivate key"]
            PUB["Bacen RSA-2048\npublic cert"]
        end
    end

    subgraph MQ ["IBM MQ -- QM.36266751.01\nlocalhost:1414 / FINVEST.SVRCONN"]
        direction TB
        subgraph IF_QUEUES ["IF Staging Queues (local)"]
            QL_E["QL...ENTRADA.IF"]
            QL_S["QL...SAIDA.IF"]
            QL_RP["QL...REPORT.IF"]
            QL_SP["QL...SUPORTE.IF"]
        end
        subgraph QR_QUEUES ["Remote Queue Definitions"]
            QR_REQ2["QR.REQ..."]
            QR_RSP2["QR.RSP..."]
            QR_REP2["QR.REP..."]
            QR_SUP2["QR.SUP..."]
        end
        subgraph BC_QUEUES ["Bacen Local Queues"]
            QL_REQ2["QL.REQ.00038166..."]
            QL_RSP2["QL.RSP.00038166..."]
            QL_REP2["QL.REP.00038166..."]
            QL_SUP2["QL.SUP.00038166..."]
        end
    end

    subgraph BACEN ["BACEN\nISPB 00038166"]
        BC_NET["Bacen Network\n(RSFN)"]
    end

    TBL_OUT --> IF_REQ & IF_RSP & IF_REP & IF_SUP
    IF_REQ --> QL_E --> QR_REQ2
    IF_RSP --> QL_S --> QR_RSP2
    IF_REP --> QL_RP --> QR_REP2
    IF_SUP --> QL_SP --> QR_SUP2
    QR_REQ2 & QR_RSP2 & QR_REP2 & QR_SUP2 --> BC_NET

    BC_NET --> QL_REQ2 & QL_RSP2 & QL_REP2 & QL_SUP2
    QL_REQ2 --> BC_REQ
    QL_RSP2 --> BC_RSP
    QL_REP2 --> BC_REP
    QL_SUP2 --> BC_SUP
    BC_REQ & BC_RSP & BC_REP & BC_SUP --> TBL_IN
    BC_REQ & BC_RSP & BC_REP & BC_SUP --> TBL_LOG
    IF_REQ & IF_RSP & IF_REP & IF_SUP --> TBL_LOG

    style DB fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style SRV fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style MQ fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style BACEN fill:#fce4ec,stroke:#b71c1c,stroke-width:2px
    style OUT_THREADS fill:#bbdefb,stroke:#1565c0
    style IN_THREADS fill:#bbdefb,stroke:#1565c0
    style CRYPTO fill:#fff8e1,stroke:#f57f17
    style IF_QUEUES fill:#ede7f6,stroke:#4527a0
    style QR_QUEUES fill:#ede7f6,stroke:#4527a0
    style BC_QUEUES fill:#ede7f6,stroke:#4527a0
```

---

## Security Detail -- Message Envelope V2

```mermaid
flowchart LR
    subgraph MSG ["MQ Message Payload"]
        direction LR
        subgraph HDR ["SECHDR V2 (588 bytes)"]
            direction TB
            H1["C01 TamSecHeader (2B)\n0x024C = 588"]
            H2["C02 Versao (1B)\n0x00=clear, 0x02=V2"]
            H3["C03 CodErro (1B)"]
            H4["C04 TratamentoEspecial (1B)"]
            H5["C05 Reservado (1B)"]
            H6["C06 AlgAssymKey (1B)\n0x02=RSA-2048"]
            H7["C07 AlgSymKey (1B)\n0x01=3DES-168"]
            H8["C08 AlgAssymKeyLocal (1B)\n0x02=RSA-2048"]
            H9["C09 AlgHash (1B)\n0x03=SHA-256"]
            H10["C10 CADest (1B)"]
            H11["C11 NumSerieCertDest (32B)"]
            H12["C12 CALocal (1B)"]
            H13["C13 NumSerieCertLocal (32B)"]
            H14["C14 SymKeyCifr (256B)\nRSA-2048 wrapped 3DES key"]
            H15["C15 HashCifrSign (256B)\nRSA-2048 digital signature"]
        end
        subgraph PAYLOAD ["Payload"]
            PL["XML Document\n(UTF-16BE encoded)\n---------\nIf Versao=0x02:\nEncrypted with 3DES-CBC\n(zero IV)"]
        end
    end

    style MSG fill:#f5f5f5,stroke:#424242,stroke-width:2px
    style HDR fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    style PAYLOAD fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
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
flowchart LR
    subgraph FINVEST_SRV ["BCSrvSqlMq Service (Finvest)"]
        direction TB
        IF_REQ["CIFReq\n(outbound DB->MQ)"]
        BC_REQ["CBacenReq\n(inbound MQ->DB)"]
        subgraph FIN_CRYPTO ["Finvest Crypto"]
            FIN_PRV["finvest_sim.key\n(sign + decrypt)"]
            FIN_PUB["bacen_sim.cer\n(encrypt + verify)"]
        end
    end

    subgraph MQ ["IBM MQ -- QM.36266751.01"]
        direction TB
        QL_IF["QL.36266751.01.ENTRADA.IF\n(IF staging queue)"]
        QL_BC["QL.REQ.00038166.36266751.01\n(Bacen local queue)"]
    end

    subgraph BACEN_SIM ["Bacen Simulator"]
        direction TB
        SIM_RCV["Receive\n(MQGET from IF queues)"]
        SIM_SND["Send\n(MQPUT to Bacen queues)"]
        subgraph BC_CRYPTO ["Bacen Crypto"]
            BC_PRV["bacen_sim.key\n(sign + decrypt)"]
            BC_PUB["finvest_sim.cer\n(encrypt + verify)"]
        end
    end

    IF_REQ -->|"sign(finvest_sim.key)\nencrypt(bacen_sim.cer)"| QL_IF
    QL_IF -->|"MQGET"| SIM_RCV
    SIM_RCV -->|"decrypt(bacen_sim.key)\nverify(finvest_sim.cer)"| BC_CRYPTO

    BC_CRYPTO -->|"sign(bacen_sim.key)\nencrypt(finvest_sim.cer)"| SIM_SND
    SIM_SND -->|"MQPUT"| QL_BC
    QL_BC -->|"MQGET"| BC_REQ
    BC_REQ -->|"decrypt(finvest_sim.key)\nverify(bacen_sim.cer)"| FIN_CRYPTO

    style FINVEST_SRV fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style MQ fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style BACEN_SIM fill:#fce4ec,stroke:#b71c1c,stroke-width:2px
    style FIN_CRYPTO fill:#fff8e1,stroke:#f57f17
    style BC_CRYPTO fill:#fff8e1,stroke:#f57f17
    style QL_IF fill:#ede7f6,stroke:#4527a0
    style QL_BC fill:#ede7f6,stroke:#4527a0
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
# Terminal 1: Finvest server
cd python
py -m bcsrvsqlmq -d

# Terminal 2: Bacen simulator
cd python
py scripts/bacen_simulator.py

# Terminal 3 (optional): Insert test message in DB
cd python
py scripts/test_db_insert.py
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
