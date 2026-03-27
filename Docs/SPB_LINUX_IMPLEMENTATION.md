# SPB System — Linux Implementation Diagram

---

## 1. High-Level Linux Architecture

```mermaid
graph LR
    BROWSER["Browser\nUser"] -->|HTTP :8000| SITE
    SITE["SPBSite\nuvicorn + FastAPI\n:8000"] --> DB[(PostgreSQL\nBanuxSPB\n:5432)]
    BCS["BCSrvSqlMq\nPython Service\n8 Threads :14499"] --> DB
    BCS --> MQ["IBM MQ\nQM.36266751.01\n:1414"]
    AUTO["Bacen Auto-Responder\nbacen_auto_responder.py"] --> MQ
    MON["monitor_live.py\n--inject"] --> DB
    MON --> MQ

    MQ <=="RSFN\nNetwork\n(simulated)"==> BACEN["BACEN\n00038166\n(simulated)"]

    style BROWSER fill:#ecf0f1,stroke:#7f8c8d,stroke-width:2px,color:#000
    style SITE fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style DB fill:#f4ecf7,stroke:#8e44ad,stroke-width:2px,color:#000
    style BCS fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style MQ fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style BACEN fill:#fadbd8,stroke:#e74c3c,stroke-width:2px,color:#000
    style AUTO fill:#fadbd8,stroke:#e74c3c,stroke-width:1px,color:#000
    style MON fill:#fdebd0,stroke:#e67e22,stroke-width:1px,color:#000
```

---

## 2. Process Map (What Actually Runs on Linux)

```mermaid
graph TB
    subgraph VENV["Python venv — /home/ubuntu/SPBFinal/SPB_FINAL/venv"]
        direction TB
        UV["uvicorn app.main:app\n--host 0.0.0.0 --port 8000\nPID: spbsite"]
        BCSRV["python -m bcsrvsqlmq -d\nPID: bcsrvsqlmq daemon"]
        AUTORESP["BacenAutoResponder.run_continuous\nduration=3600  poll=1s"]
        MONLIVE["python monitor_live.py --inject\nReal-time console + test injector"]
    end

    subgraph SYSTEM["System Services"]
        PG["PostgreSQL 16\nlocalhost:5432\nDB: BanuxSPB"]
        MQSRV["IBM MQ 9.x\nlocalhost:1414\nQM: QM.36266751.01\nChannel: FINVEST.SVRCONN"]
    end

    UV --> PG
    BCSRV --> PG
    BCSRV --> MQSRV
    AUTORESP --> MQSRV
    MONLIVE --> PG
    MONLIVE --> MQSRV

    style VENV fill:#eaf2f8,stroke:#2c3e50,stroke-width:2px,color:#000
    style SYSTEM fill:#fdf2e9,stroke:#e67e22,stroke-width:2px,color:#000
    style UV fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style BCSRV fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style AUTORESP fill:#fadbd8,stroke:#e74c3c,stroke-width:2px,color:#000
    style MONLIVE fill:#fdebd0,stroke:#e67e22,stroke-width:2px,color:#000
    style PG fill:#f4ecf7,stroke:#8e44ad,stroke-width:2px,color:#000
    style MQSRV fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
```

---

## 3. SPBSite — FastAPI Router Map

```mermaid
graph LR
    SITE["uvicorn\napp.main:app\n:8000"] --> AUTH["/auth\nLogin · Logout"]
    SITE --> ADMIN["/admin\nProfiles · Permissions"]
    SITE --> MSG["/messages\nSelect · Form · Submit"]
    SITE --> MONR["/monitoring\nControl · Messages"]
    SITE --> QUEUE["/queue\nPiloto STR · Process"]
    SITE --> LOGS["/logs\nSystem Logs"]
    SITE --> VIEW["/viewer\nXML Message Viewer"]
    SITE --> QMSG["/consultar\nConsultar Mensagens"]

    MSG -->|POST /submit| DB[(PostgreSQL)]
    MONR -->|SELECT| DB
    QUEUE -->|SELECT/UPDATE| DB
    VIEW -->|SELECT| DB
    QMSG -->|SELECT| DB

    style SITE fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style DB fill:#f4ecf7,stroke:#8e44ad,stroke-width:2px,color:#000
    style MSG fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style MONR fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style AUTH fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style ADMIN fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style QUEUE fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style LOGS fill:#ecf0f1,stroke:#95a5a6,stroke-width:1px,color:#000
    style VIEW fill:#ecf0f1,stroke:#95a5a6,stroke-width:1px,color:#000
    style QMSG fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
```

---

## 4. BCSrvSqlMq — Eight Worker Threads (Python)

### 4a. Outbound Threads (DB → MQ → BACEN)

```mermaid
graph LR
    DB[(spb_local_to_bacen\nflag_proc = P)] -->|"poll 1s"| T1["CIFReq\nif_req.py"]
    DB -->|"poll 1s"| T2["CIFRsp\nif_rsp.py"]
    DB -->|"poll 1s"| T3["CIFRep\nif_rep.py"]
    DB -->|"poll 1s"| T4["CIFSup\nif_sup.py"]

    T1 -->|MQPUT| Q1["QL.36266751.01\n.ENTRADA.IF"]
    T2 -->|MQPUT| Q2["QL.36266751.01\n.SAIDA.IF"]
    T3 -->|MQPUT| Q3["QL.36266751.01\n.REPORT.IF"]
    T4 -->|MQPUT| Q4["QL.36266751.01\n.SUPORTE.IF"]

    Q1 ==> BAC((BACEN\n00038166))
    Q2 ==> BAC
    Q3 ==> BAC
    Q4 ==> BAC

    style DB fill:#f4ecf7,stroke:#8e44ad,stroke-width:2px,color:#000
    style BAC fill:#fadbd8,stroke:#e74c3c,stroke-width:2px,color:#000
    style T1 fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style T2 fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style T3 fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style T4 fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style Q1 fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style Q2 fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style Q3 fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style Q4 fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
```

### 4b. Inbound Threads (BACEN → MQ → DB)

```mermaid
graph LR
    BAC((BACEN\n00038166)) ==> Q1["QL.REQ.00038166\n.36266751.01"]
    BAC ==> Q2["QL.RSP.00038166\n.36266751.01"]
    BAC ==> Q3["QL.REP.00038166\n.36266751.01"]
    BAC ==> Q4["QL.SUP.00038166\n.36266751.01"]

    Q1 -->|MQGET| T1["CBacenReq\nbacen_req.py"]
    Q2 -->|MQGET| T2["CBacenRsp\nbacen_rsp.py"]
    Q3 -->|MQGET| T3["CBacenRep\nbacen_rep.py"]
    Q4 -->|MQGET| T4["CBacenSup\nbacen_sup.py"]

    T1 -->|INSERT| DB[(spb_bacen_to_local)]
    T2 -->|INSERT| DB
    T3 -->|INSERT| DB
    T4 -->|INSERT| DB

    style DB fill:#f4ecf7,stroke:#8e44ad,stroke-width:2px,color:#000
    style BAC fill:#fadbd8,stroke:#e74c3c,stroke-width:2px,color:#000
    style T1 fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style T2 fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style T3 fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style T4 fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style Q1 fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style Q2 fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style Q3 fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style Q4 fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
```

---

## 5. End-to-End Request-Response (Linux Test Loop)

```mermaid
sequenceDiagram
    participant USER as Browser
    participant SITE as SPBSite<br/>FastAPI :8000
    participant DB as PostgreSQL<br/>BanuxSPB :5432
    participant IF as CIFReq Thread<br/>if_req.py
    participant MQ as IBM MQ<br/>QM.36266751.01 :1414
    participant AUTO as Bacen Auto-Responder<br/>bacen_auto_responder.py
    participant RSP as CBacenRsp Thread<br/>bacen_rsp.py

    Note over USER,RSP: PHASE 1 — User Submits Message

    USER->>SITE: POST /messages/submit<br/>(GEN0001 + form fields)
    SITE->>SITE: xml_builder.py builds SPBDOC XML<br/>form_engine.py validates fields
    SITE->>DB: INSERT spb_local_to_bacen<br/>flag_proc='P', cod_msg='GEN0001'<br/>nu_ope='36266751...'
    SITE-->>USER: Redirect to /monitoring

    Note over USER,RSP: PHASE 2 — BCSrvSqlMq Sends to MQ

    loop Poll every 1 second
        IF->>DB: SELECT WHERE flag_proc='P'
    end
    DB-->>IF: Pending message found

    Note over IF: Prepend SECHDR<br/>(security=N in test mode)

    rect rgb(230, 255, 230)
        Note over IF,MQ: Atomic MQ + DB Transaction
        IF->>MQ: MQPUT → QL.36266751.01.ENTRADA.IF
        IF->>DB: UPDATE flag_proc='E'<br/>INSERT spb_log_bacen
        Note over IF: MQCMIT + DB COMMIT
    end

    Note over USER,RSP: PHASE 3 — BACEN Simulator Responds

    loop Poll every 1 second
        AUTO->>MQ: MQGET ← QL.36266751.01.ENTRADA.IF
    end
    MQ-->>AUTO: SECHDR + XML payload

    Note over AUTO: Decode XML<br/>Extract cod_msg=GEN0001<br/>Generate GEN0001R1 response<br/>Swap Emissor ↔ Destinatario

    AUTO->>MQ: MQPUT → QL.RSP.00038166.36266751.01<br/>Response XML with SECHDR

    Note over USER,RSP: PHASE 4 — BCSrvSqlMq Receives Response

    loop MQGET wait 30s
        RSP->>MQ: MQGET ← QL.RSP.00038166.36266751.01
    end
    MQ-->>RSP: SECHDR + response payload

    Note over RSP: Strip SECHDR<br/>Decode XML<br/>Extract cod_msg=GEN0001R1

    rect rgb(220, 235, 255)
        Note over RSP,DB: Atomic DB Transaction
        RSP->>DB: INSERT spb_bacen_to_local<br/>cod_msg='GEN0001R1'
        RSP->>DB: INSERT spb_log_bacen
        Note over RSP: MQCMIT + DB COMMIT
    end

    Note over USER,RSP: PHASE 5 — User Sees Result

    USER->>SITE: GET /monitoring/messages/inbound/bacen
    SITE->>DB: SELECT spb_bacen_to_local
    DB-->>SITE: GEN0001R1 response row
    SITE-->>USER: Display response + XML viewer
```

---

## 6. BACEN Auto-Responder Detail (Test Simulator)

```mermaid
sequenceDiagram
    participant MQ as IBM MQ
    participant AUTO as BacenAutoResponder
    participant LOG as Console / Trace

    Note over AUTO: run_continuous(duration=3600, poll=1.0)

    loop Every 1 second for 1 hour
        AUTO->>MQ: MQGET ← QL.36266751.01.ENTRADA.IF
        alt Message found
            MQ-->>AUTO: Raw message bytes
            AUTO->>AUTO: Strip SECHDR (skip first N bytes)
            AUTO->>AUTO: Decode payload (UTF-16BE or UTF-8)
            AUTO->>AUTO: Parse XML → extract CodMsg

            alt CodMsg = GEN0001
                AUTO->>AUTO: Generate GEN0001R1 (Echo Response)
            else CodMsg = GEN0002
                AUTO->>AUTO: Generate GEN0002R1 (Log Response)
            else CodMsg = GEN0003
                AUTO->>AUTO: Generate GEN0003R1 (UltMsg Response)
            else Other
                AUTO->>AUTO: Generate generic R1 response
            end

            Note over AUTO: Build SPBDOC response XML<br/>Id_Emissor=00038166 (BACEN)<br/>Id_Destinatario=36266751 (Finvest)

            AUTO->>AUTO: Prepend SECHDR V0 (clear)
            AUTO->>MQ: MQPUT → QL.RSP.00038166.36266751.01
            AUTO->>LOG: Log response sent
        else No message
            Note over AUTO: Sleep 1s, continue
        end
    end
```

---

## 7. monitor_live.py — Real-Time Event Monitor

```mermaid
graph TB
    subgraph MONITOR["monitor_live.py --inject"]
        direction TB
        POLL["Event Loop\nPolls every 1s"]
        INJ["Test Injector\nInserts GEN0001 into DB"]
    end

    POLL -->|"SELECT spb_local_to_bacen\nWHERE flag_proc='P'"| DB[(PostgreSQL)]
    POLL -->|"SELECT spb_bacen_to_local\nLatest responses"| DB
    POLL -->|"SELECT spb_log_bacen\nAudit entries"| DB
    POLL -->|"MQINQ queue depth"| MQ["IBM MQ"]
    POLL -->|"Check BCSrvSqlMq\nport 14499"| BCS["BCSrvSqlMq"]
    INJ -->|"INSERT flag_proc='P'\ncod_msg='GEN0001'"| DB

    subgraph DISPLAY["Console Output (color-coded)"]
        E1["01 DB INSERT — Yellow"]
        E2["02 BCSrvSqlMq P→E — Green"]
        E3["03 MQ PUT/GET — Cyan"]
        E4["04 RESPONSE RECEIVED — Cyan"]
        E5["✓  FLOW COMPLETE — Green"]
    end

    POLL --> DISPLAY

    style MONITOR fill:#fdebd0,stroke:#e67e22,stroke-width:2px,color:#000
    style DB fill:#f4ecf7,stroke:#8e44ad,stroke-width:2px,color:#000
    style MQ fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style BCS fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style DISPLAY fill:#ecf0f1,stroke:#95a5a6,stroke-width:1px,color:#000
```

---

## 8. Security Pipeline (When Enabled)

```mermaid
graph TD
    subgraph OUTBOUND["Outbound — Sign + Encrypt"]
        A1["Raw XML\nLatin-1"] --> A2["Encode\nUTF-16BE"]
        A2 --> A3["Generate random\n3DES key 168-bit"]
        A3 --> A4["Encrypt payload\n3DES-CBC"]
        A4 --> A5["Wrap 3DES key\nwith BACEN cert\nRSA-2048"]
        A5 --> A6["Sign hash\nwith Finvest key\nRSA-2048 + SHA-256"]
        A6 --> A7["Build SECHDR\n588 bytes V2"]
        A7 --> A8["SECHDR +\nEncrypted Payload"]
    end

    subgraph INBOUND["Inbound — Verify + Decrypt"]
        B1["SECHDR +\nEncrypted Payload"] --> B2["Parse SECHDR\nV0=clear / V1=332B / V2=588B"]
        B2 --> B3["Unwrap 3DES key\nwith Finvest key\nRSA-2048"]
        B3 --> B4["Decrypt payload\n3DES-CBC"]
        B4 --> B5["Verify signature\nwith BACEN cert\nRSA-2048 + SHA-256"]
        B5 --> B6["Decode\nUTF-16BE → Latin-1"]
        B6 --> B7["Decrypted XML"]
    end

    subgraph CONFIG["BCSrvSqlMq.ini [Security]"]
        C1["securityenable = N  (test)\nsecurityenable = S  (prod)"]
        C2["certificatefile = certificates/bacen_sim.cer\nprivatekeyfile = certificates/finvest_sim.key"]
    end

    CONFIG -.->|controls| OUTBOUND
    CONFIG -.->|controls| INBOUND

    style A1 fill:#fff,stroke:#333,stroke-width:2px,color:#000
    style A8 fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style B1 fill:#fadbd8,stroke:#e74c3c,stroke-width:2px,color:#000
    style B7 fill:#fff,stroke:#333,stroke-width:2px,color:#000
    style CONFIG fill:#ecf0f1,stroke:#95a5a6,stroke-width:1px,color:#000
```

---

## 9. Database Tables (ER Diagram)

```mermaid
erDiagram
    spb_local_to_bacen ||--o{ spb_log_bacen : "audit"
    spb_bacen_to_local ||--o{ spb_log_bacen : "audit"
    spb_mensagem ||--o{ spb_msg_field : "fields"
    spb_dicionario ||--o{ spb_msg_field : "type"
    user ||--o{ profile : "permissions"

    spb_local_to_bacen {
        timestamp db_datetime PK
        varchar cod_msg PK
        varchar nu_ope
        text msg
        char flag_proc "P=Pending E=Sent"
        varchar mq_msg_id
        varchar mq_qn_destino
        timestamp mq_datetime_put
        char status_msg
    }

    spb_bacen_to_local {
        timestamp db_datetime PK
        varchar mq_msg_id PK
        varchar mq_correl_id
        varchar nu_ope
        varchar cod_msg
        text msg
        char flag_proc
        varchar mq_qn_origem
        char status_msg
    }

    spb_log_bacen {
        timestamp db_datetime PK
        varchar cod_msg
        varchar nu_ope
        char status
    }

    spb_mensagem {
        varchar CodMsg PK
        varchar Nome_Mensagem
    }

    spb_msg_field {
        varchar CodMsg FK
        varchar Tag FK
        int ordem
    }

    spb_dicionario {
        varchar Tag PK
        varchar Tipologia
    }

    spb_controle {
        varchar key PK
        varchar value
    }

    user {
        int id PK
        varchar username
        varchar password_hash
    }

    profile {
        int id PK
        int user_id FK
        varchar role
    }
```

---

## 10. Linux Deployment View

```mermaid
graph TB
    subgraph HOST["Ubuntu Linux Server"]
        subgraph APP["Application Layer (Python venv)"]
            SITE["SPBSite\nuvicorn + FastAPI\n:8000"]
            BCS["BCSrvSqlMq\npython -m bcsrvsqlmq -d\n8 threads  :14499"]
            AUTO["bacen_auto_responder.py\nBACEN simulator"]
            MONLIVE["monitor_live.py\n--inject mode"]
        end

        subgraph DATA["Data Layer"]
            PG["PostgreSQL 16\nlocalhost:5432\nDB: BanuxSPB"]
        end

        subgraph MQ_LAYER["Messaging Layer"]
            MQSRV["IBM MQ 9.x\nlocalhost:1414\nQM: QM.36266751.01\nChannel: FINVEST.SVRCONN"]
        end

        subgraph CERTS["Security Assets"]
            CERT["certificates/\nbacen_sim.cer\nfinvest_sim.key"]
        end

        subgraph FILES["File System"]
            TRACES["Traces/\nTRACE_SPB__YYYYMMDD.log"]
            AUDIT["AuditFiles/\nMessage audit trail"]
            INI["BCSrvSqlMq.ini\nService configuration"]
        end
    end

    subgraph EXT["External (Simulated)"]
        RSFN["RSFN Network\n(not connected)"]
        BACEN["BACEN 00038166\n(auto-responder simulates)"]
    end

    SITE --> PG
    BCS --> PG
    BCS --> MQSRV
    BCS --> CERT
    BCS --> TRACES
    BCS --> AUDIT
    AUTO --> MQSRV
    MONLIVE --> PG
    MONLIVE --> MQSRV
    MQSRV -.->|"simulated by\nauto-responder"| RSFN
    RSFN -.-> BACEN

    style HOST fill:#eaf2f8,stroke:#2c3e50,stroke-width:2px,color:#000
    style APP fill:#d6eaf8,stroke:#2980b9,stroke-width:1px,color:#000
    style DATA fill:#f4ecf7,stroke:#8e44ad,stroke-width:1px,color:#000
    style MQ_LAYER fill:#fef9e7,stroke:#f39c12,stroke-width:1px,color:#000
    style CERTS fill:#fdebd0,stroke:#e67e22,stroke-width:1px,color:#000
    style FILES fill:#ecf0f1,stroke:#95a5a6,stroke-width:1px,color:#000
    style EXT fill:#fdf2e9,stroke:#e67e22,stroke-width:2px,color:#000
```

---

## 11. How to Start All Services (Linux)

```mermaid
graph TD
    S1["1. PostgreSQL\n(system service — already running)"] --> S2
    S2["2. IBM MQ\n(system service — already running)"] --> S3
    S3["3. BCSrvSqlMq\ncd BCSrvSqlMq/python\nsource ../../venv/bin/activate\nnohup python -m bcsrvsqlmq -d &"] --> S4
    S4["4. SPBSite\ncd spbsite\nsource ../venv/bin/activate\nnohup uvicorn app.main:app\n--host 0.0.0.0 --port 8000 &"] --> S5
    S5["5. Bacen Auto-Responder\nsource venv/bin/activate\npython -c 'from BCSrvSqlMq...\nBacenAutoResponder().run_continuous(3600)'"] --> S6
    S6["6. Monitor Live (optional)\npython monitor_live.py --inject"]

    style S1 fill:#f4ecf7,stroke:#8e44ad,stroke-width:2px,color:#000
    style S2 fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style S3 fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style S4 fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style S5 fill:#fadbd8,stroke:#e74c3c,stroke-width:2px,color:#000
    style S6 fill:#fdebd0,stroke:#e67e22,stroke-width:2px,color:#000
```

---

## Port & Service Reference

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| **SPBSite** | 8000 | HTTP | FastAPI web application |
| **IBM MQ** | 1414 | MQ TCP | Queue manager (FINVEST.SVRCONN) |
| **PostgreSQL** | 5432 | TCP | Database (BanuxSPB) |
| **BCSrvSqlMq** | 14499 | TCP | Monitoring/health listener |

## Queue Reference

| Direction | Type | Queue Name | Used By |
|-----------|------|------------|---------|
| **Outbound** | IF-REQ | `QL.36266751.01.ENTRADA.IF` | CIFReq → BACEN |
| **Outbound** | IF-RSP | `QL.36266751.01.SAIDA.IF` | CIFRsp → BACEN |
| **Outbound** | IF-REP | `QL.36266751.01.REPORT.IF` | CIFRep → BACEN |
| **Outbound** | IF-SUP | `QL.36266751.01.SUPORTE.IF` | CIFSup → BACEN |
| **Inbound** | REQ | `QL.REQ.00038166.36266751.01` | CBacenReq ← BACEN |
| **Inbound** | RSP | `QL.RSP.00038166.36266751.01` | CBacenRsp ← BACEN |
| **Inbound** | REP | `QL.REP.00038166.36266751.01` | CBacenRep ← BACEN |
| **Inbound** | SUP | `QL.SUP.00038166.36266751.01` | CBacenSup ← BACEN |

## ISPB Codes

| Entity | ISPB | Role |
|--------|------|------|
| **Finvest** | `36266751` | Local institution |
| **BACEN** | `00038166` | Central Bank (simulated) |
| **SELIC** | `00038121` | Settlement system (optional) |

## Key Configuration Files

| File | Purpose |
|------|---------|
| `BCSrvSqlMq/BCSrvSqlMq.ini` | Service config (MQ, DB, security, queues) |
| `spbsite/app/config.py` | FastAPI settings (Pydantic) |
| `spbsite/.env` | Environment variables |
| `certificates/bacen_sim.cer` | BACEN public cert (test) |
| `certificates/finvest_sim.key` | Finvest private key (test) |

## Key Differences from Windows (SPB_E2E_DIAGRAM)

| Aspect | Windows (Original) | Linux (This Implementation) |
|--------|--------------------|-----------------------------|
| **BCSrvSqlMq** | Windows Service (C++) | Python daemon (`python -m bcsrvsqlmq -d`) |
| **Web Server** | IIS / manual | uvicorn + FastAPI (async) |
| **BACEN** | Real RSFN network | Simulated via `bacen_auto_responder.py` |
| **Monitor** | N/A | `monitor_live.py` with color-coded console |
| **Carga_Mensageria** | ETL tool | Not needed (catalog loaded in DB) |
| **Security** | Always enabled | Configurable (`securityenable = N` for test) |
| **Database** | Same PostgreSQL | Same PostgreSQL |
| **MQ** | Same IBM MQ | Same IBM MQ |
