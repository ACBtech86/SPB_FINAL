# SPB System - End-to-End Message Flow Diagrams

---

## 1. High-Level Architecture

```mermaid
graph LR
    SITE["SPBSite\nFastAPI :8000"] --> DB[(PostgreSQL\nbcspbstr)]
    BCS["BCSrvSqlMq\n8 Threads"] --> DB
    BCS --> MQ["IBM MQ\nQM.36266751.01"]
    CARGA["Carga_Mensageria\nETL Tool"] --> DB
    MQ <=="RSFN\nNetwork"==> BACEN["BACEN\n00038166"]

    style SITE fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style DB fill:#f4ecf7,stroke:#8e44ad,stroke-width:2px,color:#000
    style BCS fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style MQ fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
    style BACEN fill:#fadbd8,stroke:#e74c3c,stroke-width:2px,color:#000
    style CARGA fill:#fef9e7,stroke:#f39c12,stroke-width:2px,color:#000
```

---

## 2. Outbound Flow: Finvest → BACEN

```mermaid
sequenceDiagram
    participant APP as Application
    participant DB as PostgreSQL
    participant THR as CIFReq Thread
    participant MQ as IBM MQ
    participant BAC as BACEN

    APP->>DB: INSERT spb_local_to_bacen (flag_proc = P)

    loop Poll every 1 second
        THR->>DB: SELECT WHERE flag_proc = P
    end
    DB-->>THR: Pending message

    Note over THR: Sign (finvest.key)<br/>Encrypt (bacen.cer)<br/>Build SECHDR 588B

    rect rgb(230, 255, 230)
        Note over THR,MQ: Atomic Transaction
        THR->>MQ: MQPUT encrypted message
        THR->>DB: UPDATE flag_proc = E
        THR->>DB: INSERT spb_log_bacen
        Note over THR: MQCMIT + DB COMMIT
    end

    MQ->>BAC: via RSFN Network
```

---

## 3. Inbound Flow: BACEN → Finvest

```mermaid
sequenceDiagram
    participant BAC as BACEN
    participant MQ as IBM MQ
    participant THR as CBacenReq Thread
    participant DB as PostgreSQL

    BAC->>MQ: Message via RSFN Network

    loop MQGET wait 30s
        THR->>MQ: MQGET (EXCLUSIVE + syncpoint)
    end
    MQ-->>THR: SECHDR + encrypted payload

    Note over THR: Decrypt (finvest.key)<br/>Verify sig (bacen.cer)<br/>Parse XML

    rect rgb(220, 235, 255)
        Note over THR,DB: Atomic Transaction
        THR->>DB: INSERT spb_bacen_to_local
        THR->>DB: INSERT spb_log_bacen
        Note over THR: MQCMIT + DB COMMIT
    end
```

---

## 4. Complete Request-Response Cycle

```mermaid
sequenceDiagram
    participant APP as Application
    participant DB as PostgreSQL
    participant BCS as BCSrvSqlMq
    participant MQ as IBM MQ
    participant BAC as BACEN

    Note over APP,BAC: PHASE 1 - Send Request
    APP->>DB: INSERT GEN0001 (flag_proc = P)
    BCS->>DB: Poll found pending
    BCS->>MQ: Sign + Encrypt + MQPUT
    BCS->>DB: flag_proc = E + audit log
    MQ->>BAC: via RSFN

    Note over APP,BAC: PHASE 2 - Receive Response
    BAC->>MQ: GEN0002 Response
    BCS->>MQ: MQGET
    BCS->>DB: INSERT response + audit log

    Note over APP,BAC: PHASE 3 - Confirmations
    BAC->>MQ: COA (Confirm Arrival)
    BCS->>DB: INSERT COA + audit log
    BAC->>MQ: COD (Confirm Delivery)
    BCS->>DB: INSERT COD + audit log
```

---

## 5. Eight Worker Threads

### 5a. Outbound Threads (DB → MQ)

```mermaid
graph LR
    DB[(spb_local_to_bacen\nflag_proc = P)] -->|poll 1s| R["CIFReq"]
    DB -->|poll 1s| S["CIFRsp"]
    DB -->|poll 1s| P["CIFRep"]
    DB -->|poll 1s| U["CIFSup"]

    R -->|MQPUT| QR1["QR.REQ...00038166"]
    S -->|MQPUT| QR2["QR.RSP...00038166"]
    P -->|MQPUT| QR3["QR.REP...00038166"]
    U -->|MQPUT| QR4["QR.SUP...00038166"]

    QR1 ==> BAC((BACEN))
    QR2 ==> BAC
    QR3 ==> BAC
    QR4 ==> BAC

    style DB fill:#f4ecf7,stroke:#8e44ad,stroke-width:2px,color:#000
    style BAC fill:#fadbd8,stroke:#e74c3c,stroke-width:2px,color:#000
    style R fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style S fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style P fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
    style U fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
```

### 5b. Inbound Threads (MQ → DB)

```mermaid
graph LR
    BAC((BACEN)) ==> QL1["QL.REQ.00038166..."]
    BAC ==> QL2["QL.RSP.00038166..."]
    BAC ==> QL3["QL.REP.00038166..."]
    BAC ==> QL4["QL.SUP.00038166..."]

    QL1 -->|MQGET| R["CBacenReq"]
    QL2 -->|MQGET| S["CBacenRsp"]
    QL3 -->|MQGET| P["CBacenRep"]
    QL4 -->|MQGET| U["CBacenSup"]

    R -->|INSERT| DB[(spb_bacen_to_local)]
    S -->|INSERT| DB
    P -->|INSERT| DB
    U -->|INSERT| DB

    style DB fill:#f4ecf7,stroke:#8e44ad,stroke-width:2px,color:#000
    style BAC fill:#fadbd8,stroke:#e74c3c,stroke-width:2px,color:#000
    style R fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style S fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style P fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
    style U fill:#d6eaf8,stroke:#2980b9,stroke-width:2px,color:#000
```

---

## 6. Security - Outbound Encryption

```mermaid
graph TD
    A["Raw XML\nLatin-1"] --> B["Encode\nUTF-16BE"]
    B --> C["Generate random\n3DES key 168-bit"]
    C --> D["Encrypt payload\n3DES-CBC"]
    D --> E["Wrap 3DES key\nwith BACEN cert\nRSA-2048"]
    E --> F["Sign hash\nwith Finvest key\nRSA-2048 + SHA-256"]
    F --> G["Build SECHDR\n588 bytes V2"]
    G --> H["SECHDR +\nEncrypted Payload"]

    style A fill:#fff,stroke:#333,stroke-width:2px,color:#000
    style H fill:#d5f5e3,stroke:#27ae60,stroke-width:2px,color:#000
```

## 7. Security - Inbound Decryption

```mermaid
graph TD
    A["SECHDR +\nEncrypted Payload"] --> B["Parse SECHDR\nV1=332B / V2=588B"]
    B --> C["Unwrap 3DES key\nwith Finvest key\nRSA-2048"]
    C --> D["Decrypt payload\n3DES-CBC"]
    D --> E["Verify signature\nwith BACEN cert\nRSA-2048 + SHA-256"]
    E --> F["Decode\nUTF-16BE to Latin-1"]
    F --> G["Decrypted XML"]

    style A fill:#fadbd8,stroke:#e74c3c,stroke-width:2px,color:#000
    style G fill:#fff,stroke:#333,stroke-width:2px,color:#000
```

---

## 8. Database Tables

```mermaid
erDiagram
    spb_local_to_bacen ||--o{ spb_log_bacen : "audit"
    spb_bacen_to_local ||--o{ spb_log_bacen : "audit"
    spb_mensagem ||--o{ spb_msgfield : "fields"
    spb_dicionario ||--o{ spb_msgfield : "type"

    spb_local_to_bacen {
        timestamp db_datetime PK
        varchar cod_msg PK
        varchar nu_ope
        text msg
        char flag_proc
    }

    spb_bacen_to_local {
        timestamp db_datetime PK
        varchar mq_msg_id PK
        varchar nu_ope
        varchar cod_msg
        text msg
        char flag_proc
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

    spb_msgfield {
        varchar CodMsg FK
        varchar Tag FK
        int ordem
    }

    spb_dicionario {
        varchar Tag PK
        varchar Tipologia
    }
```

---

## 9. Deployment View

```mermaid
graph TB
    subgraph LOCAL["Finvest Server"]
        SITE["SPBSite\nFastAPI :8000"]
        BCS["BCSrvSqlMq\nWindows Service"]
        PG["PostgreSQL 16"]
        MQ["IBM MQ 9.3"]
        CERT["Certificates\nRSA-2048"]
    end

    subgraph EXT["External Network"]
        RSFN["RSFN"]
        BACEN["BACEN"]
        SELIC["SELIC"]
    end

    SITE --> PG
    BCS --> PG
    BCS --> MQ
    BCS --> CERT
    MQ <--> RSFN
    RSFN <--> BACEN
    RSFN <--> SELIC

    style LOCAL fill:#eaf2f8,stroke:#2c3e50,stroke-width:2px,color:#000
    style EXT fill:#fdf2e9,stroke:#e67e22,stroke-width:2px,color:#000
```

---

## Queue Reference

| Direction | Type | Queue Name |
|-----------|------|------------|
| **Outbound** | REQ | `QR.REQ.36266751.00038166.01` |
| **Outbound** | RSP | `QR.RSP.36266751.00038166.01` |
| **Outbound** | REP | `QR.REP.36266751.00038166.01` |
| **Outbound** | SUP | `QR.SUP.36266751.00038166.01` |
| **Inbound** | REQ | `QL.REQ.00038166.36266751.01` |
| **Inbound** | RSP | `QL.RSP.00038166.36266751.01` |
| **Inbound** | REP | `QL.REP.00038166.36266751.01` |
| **Inbound** | SUP | `QL.SUP.00038166.36266751.01` |
| **Staging** | IF | `QL.36266751.01.ENTRADA.IF` |
| **Staging** | IF | `QL.36266751.01.SAIDA.IF` |
