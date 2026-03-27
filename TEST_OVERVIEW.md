# SPB Final - Test Suite Overview

## Test Architecture

```mermaid
graph TB
    subgraph "Test Pyramid"
        E2E["E2E Tests<br/>4 files"]
        INT["Integration Tests<br/>5 files"]
        SMOKE["Smoke Tests<br/>1 file"]
        API["Async API Tests<br/>6 files"]
        UNIT["Unit Tests<br/>5 files"]
        SCRIPTS["Functional Scripts<br/>2 files"]
    end

    E2E --> INT
    INT --> SMOKE
    SMOKE --> API
    API --> UNIT
    UNIT --> SCRIPTS

    style E2E fill:#ff6b6b,color:#fff
    style INT fill:#ffa94d,color:#fff
    style SMOKE fill:#ffd43b,color:#333
    style API fill:#69db7c,color:#333
    style UNIT fill:#4dabf7,color:#fff
    style SCRIPTS fill:#b197fc,color:#fff
```

## Project Test Map

```mermaid
graph LR
    subgraph ROOT["SPB_FINAL"]
        direction TB
        subgraph TS["test_scripts/"]
            comprehensive_e2e["comprehensive_e2e_test.py"]
            e2e_full["e2e_full_system_test.py"]
            e2e_v2["e2e_test_v2.py"]
            quick["quick_test.sh"]
        end

        subgraph SITE["spbsite/tests/"]
            conftest_site["conftest.py"]
            t_auth["test_auth.py"]
            t_mon["test_monitoring.py"]
            t_msg["test_messages.py"]
            t_queue["test_queue.py"]
            t_logs["test_logs.py"]
            t_viewer["test_viewer.py"]
        end

        subgraph BC["BCSrvSqlMq/python/tests/"]
            conftest_bc["conftest.py"]
            subgraph UNIT_DIR["unit/"]
                t_main["test_main_srv.py"]
                t_log["test_logging_module.py"]
                t_msgsgr["test_msg_sgr.py"]
                t_thread["test_thread_mq.py"]
                t_ssl["test_openssl_wrapper.py"]
            end
            subgraph INT_DIR["integration/"]
                t_smoke["test_smoke.py"]
                t_db["test_database.py"]
                t_monitor["test_monitor.py"]
                t_mq["test_mq_integration.py"]
                t_init["test_init_srv.py"]
            end
        end

        subgraph SCRIPTS_DIR["BCSrvSqlMq/python/scripts/"]
            s_db["test_db_insert.py"]
            s_mon["test_monitor_client.py"]
        end
    end

    style TS fill:#ff6b6b,color:#fff
    style SITE fill:#69db7c,color:#333
    style UNIT_DIR fill:#4dabf7,color:#fff
    style INT_DIR fill:#ffa94d,color:#fff
    style SCRIPTS_DIR fill:#b197fc,color:#fff
```

## Test Types Summary

| Type | Files | Framework | Description |
|------|-------|-----------|-------------|
| **Unit** | 5 | pytest | Isolated class/function tests, no external services |
| **Integration** | 5 | pytest | Require PostgreSQL, IBM MQ, or network |
| **Smoke** | 1 | pytest | Module import verification |
| **Async/API** | 6 | pytest + pytest-asyncio | FastAPI endpoint testing with DB fixtures |
| **E2E** | 4 | Python scripts + Bash | Full system flow across all services |
| **Functional Scripts** | 2 | Direct Python | Manual service interaction utilities |

**Total: 23 test files + 2 functional scripts + 1 bash orchestrator = 26 items**

---

## 1. Unit Tests (BCSrvSqlMq)

```mermaid
graph TD
    subgraph "Unit Tests - BCSrvSqlMq"
        A["test_main_srv.py<br/>Queue mgmt, thread safety"]
        B["test_logging_module.py<br/>File I/O, timestamps"]
        C["test_msg_sgr.py<br/>Binary structures COMHDR/SECHDR"]
        D["test_thread_mq.py<br/>Encoding ANSI/Unicode, XML ops"]
        E["test_openssl_wrapper.py<br/>RSA, signatures, encryption"]
    end

    A -->|CQueueList| F["Thread-safe queue add/get/remove"]
    A -->|CClientItem| G["Client item lifecycle"]
    C -->|COMHDR| H["Pack/unpack binary headers"]
    C -->|SECHDR| I["Security header structures"]
    E -->|RSA| J["Key loading, cert generation"]
    E -->|Crypto| K["Digital signatures, AES encryption"]

    style A fill:#4dabf7,color:#fff
    style B fill:#4dabf7,color:#fff
    style C fill:#4dabf7,color:#fff
    style D fill:#4dabf7,color:#fff
    style E fill:#4dabf7,color:#fff
```

| File | Classes/Tests | What It Covers |
|------|--------------|----------------|
| `test_main_srv.py` | TestCQueueList, TestCClientItem | Thread-safe queue operations, client item lifecycle |
| `test_logging_module.py` | Logging init, file I/O | Log file creation, timestamp formatting |
| `test_msg_sgr.py` | COMHDR, SECHDR structures | Binary message pack/unpack, field validation |
| `test_thread_mq.py` | Encoding, XML | ANSI/Unicode roundtrip, lxml document ops |
| `test_openssl_wrapper.py` | RSA, X.509, AES | Key loading, digital signatures, symmetric encryption |

---

## 2. Integration Tests (BCSrvSqlMq)

```mermaid
graph TD
    subgraph "Integration Tests"
        S["test_smoke.py<br/>Import verification"]
        DB["test_database.py<br/>PostgreSQL connectivity"]
        MON["test_monitor.py<br/>TCP monitor port"]
        MQ["test_mq_integration.py<br/>IBM MQ operations"]
        INI["test_init_srv.py<br/>INI config parsing"]
    end

    DB -->|psycopg2| PG["PostgreSQL<br/>banuxSPB"]
    MON -->|socket| TCP["TCP Port 14499"]
    MQ -->|pymqi| IBM["IBM MQ<br/>Queue Manager"]

    MQ --> Q1["PUT/GET/BROWSE"]
    MQ --> Q2["Remote queues"]
    MQ --> Q3["Correlation IDs"]
    MQ --> Q4["Purge & verify"]

    style S fill:#ffd43b,color:#333
    style DB fill:#ffa94d,color:#fff
    style MON fill:#ffa94d,color:#fff
    style MQ fill:#ffa94d,color:#fff
    style INI fill:#ffa94d,color:#fff
    style PG fill:#336791,color:#fff
    style IBM fill:#054ADA,color:#fff
```

| File | External Dependency | What It Covers |
|------|-------------------|----------------|
| `test_smoke.py` | None | All modules import without errors (pymqi optional) |
| `test_database.py` | PostgreSQL | Connection, CRUD operations via psycopg2 |
| `test_monitor.py` | Network/Socket | TCP communication with COMHDR protocol |
| `test_mq_integration.py` | IBM MQ | Queue manager connect, PUT/GET/BROWSE, remote queues, correlation IDs |
| `test_init_srv.py` | File system | INI configuration loading and validation |

---

## 3. Async API Tests (SPBSite)

```mermaid
graph TD
    subgraph "SPBSite Async API Tests"
        AUTH["test_auth.py<br/>14 tests"]
        MON["test_monitoring.py<br/>16+ tests"]
        MSG["test_messages.py<br/>12+ tests"]
        QUE["test_queue.py<br/>8+ tests"]
        LOG["test_logs.py<br/>5 tests"]
        VIEW["test_viewer.py<br/>5 tests"]
    end

    subgraph "Fixtures (conftest.py)"
        SESS["db_session<br/>AsyncSession"]
        CLI["client<br/>AsyncClient"]
        ADM["admin_user"]
        ACLI["authenticated_client"]
        SEED["Seed Data Fixtures"]
    end

    AUTH --> CLI
    AUTH --> ADM
    MON --> ACLI
    MON --> SEED
    MSG --> ACLI
    MSG --> SEED
    QUE --> ACLI
    QUE --> SEED
    LOG --> ACLI
    VIEW --> ACLI

    SESS -->|AsyncSession| PGTEST["PostgreSQL<br/>BanuxSPB_TEST"]
    CLI -->|ASGITransport| FAST["FastAPI App"]

    style AUTH fill:#69db7c,color:#333
    style MON fill:#69db7c,color:#333
    style MSG fill:#69db7c,color:#333
    style QUE fill:#69db7c,color:#333
    style LOG fill:#69db7c,color:#333
    style VIEW fill:#69db7c,color:#333
    style PGTEST fill:#336791,color:#fff
    style FAST fill:#009688,color:#fff
```

| File | Tests | What It Covers |
|------|-------|----------------|
| `test_auth.py` | ~14 | Login page, session management, CSRF, inactive accounts, bcrypt |
| `test_monitoring.py` | ~16 | Control tables (BACEN/SELIC), status color coding, statistics |
| `test_messages.py` | ~12 | Dynamic form rendering, field validation, XML generation, queue routing |
| `test_queue.py` | ~8 | Queue display, balance summary (STR/COMPE/CIP), flag processing P->E |
| `test_logs.py` | ~5 | Log viewing routes by channel |
| `test_viewer.py` | ~5 | XML viewer rendering |

---

## 4. End-to-End Tests

```mermaid
sequenceDiagram
    participant Test as E2E Test Runner
    participant Site as SPBSite (FastAPI)
    participant DB as PostgreSQL
    participant Srv as BCSrvSqlMq
    participant MQ as IBM MQ
    participant Sim as BACEN Simulator

    Test->>DB: 1. Check DB connectivity
    Test->>MQ: 2. Check MQ availability
    Test->>Site: 3. Check HTTP endpoints
    Test->>Srv: 4. Check monitor port (14499)

    Note over Test,Sim: Message Flow Test
    Test->>Site: 5. Submit test message via API
    Site->>DB: 6. Insert into SPBLocalToBacen (flag=P)
    Srv->>DB: 7. Pick up message (flag P->E)
    Srv->>MQ: 8. Send to IBM MQ queue
    MQ->>Sim: 9. BACEN simulator receives
    Sim->>MQ: 10. Response message
    MQ->>Srv: 11. BCSrvSqlMq receives response
    Srv->>DB: 12. Insert into SPBBacenToLocal
    Test->>DB: 13. Verify all tables updated
```

| File | Type | What It Covers |
|------|------|----------------|
| `comprehensive_e2e_test.py` | Python | Full flow: SPBSite -> BCSrvSqlMq -> MQ -> BACEN Simulator -> reverse |
| `e2e_full_system_test.py` | Python | Complete message flow across all 5 services with verification |
| `e2e_test_v2.py` | Python | Service connectivity testing with results recording |
| `quick_test.sh` | Bash | Orchestrated E2E runner with service health checks |

---

## 5. Functional Test Scripts

```mermaid
graph LR
    subgraph "Manual Test Utilities"
        DBI["test_db_insert.py"]
        MONC["test_monitor_client.py"]
    end

    DBI -->|INSERT| PG["PostgreSQL<br/>Simulates IF side"]
    MONC -->|TCP socket| MON["Monitor Port 14499<br/>COMHDR protocol"]

    style DBI fill:#b197fc,color:#fff
    style MONC fill:#b197fc,color:#fff
```

---

## Test Infrastructure

### Frameworks & Libraries

```mermaid
graph TD
    subgraph "Test Stack"
        PY["pytest >= 8.0"]
        ASYNC["pytest-asyncio >= 0.24"]
        HTTPX["httpx (AsyncClient)"]
        SQLA["SQLAlchemy 2.0 (AsyncSession)"]
        PSYC["psycopg2-binary / asyncpg"]
        PYMQI["pymqi >= 1.12.0 (optional)"]
        CRYPTO["cryptography >= 41.0"]
        LXML["lxml >= 4.9"]
    end

    PY --> ASYNC
    ASYNC --> HTTPX
    HTTPX --> SQLA
    SQLA --> PSYC
    PY --> PYMQI
    PY --> CRYPTO
    PY --> LXML

    style PY fill:#0D47A1,color:#fff
    style ASYNC fill:#1565C0,color:#fff
    style HTTPX fill:#1976D2,color:#fff
```

### Database Configuration

| Context | Database | Connection |
|---------|----------|------------|
| SPBSite tests | `BanuxSPB_TEST` | `postgresql+asyncpg://postgres:***@localhost:5432/BanuxSPB_TEST` |
| BCSrvSqlMq integration | `banuxSPB` | `postgresql://postgres:***@localhost:5432/banuxSPB` |
| SPBSite tests isolation | Function-scoped | Tables created/dropped per test |
| BCSrvSqlMq tests isolation | Transaction rollback | Changes rolled back after each test |

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `pytest.ini` | `BCSrvSqlMq/python/` | Markers (`integration`), test discovery patterns |
| `pyproject.toml` | `spbsite/` | asyncio_mode=auto, test paths |
| `conftest.py` | `spbsite/tests/` | 328 lines: DB sessions, users, seed data fixtures |
| `conftest.py` | `BCSrvSqlMq/python/tests/` | tmp_dir, sample_ini, rsa_keypair fixtures |

---

## Test Execution Commands

```bash
# SPBSite - all tests
pytest spbsite/tests/ -v

# SPBSite - single test
pytest spbsite/tests/test_auth.py::test_login_valid_credentials -v

# BCSrvSqlMq - unit tests only
pytest BCSrvSqlMq/python/tests/unit/ -v

# BCSrvSqlMq - integration tests
pytest BCSrvSqlMq/python/tests/integration/ -v -m integration

# BCSrvSqlMq - skip integration
pytest BCSrvSqlMq/python/tests/ -m "not integration"

# E2E tests
python test_scripts/comprehensive_e2e_test.py
bash test_scripts/quick_test.sh
```

---

## Coverage by Domain

```mermaid
pie title Test Distribution by Type
    "Unit Tests" : 5
    "Integration Tests" : 5
    "Smoke Tests" : 1
    "Async API Tests" : 6
    "E2E Tests" : 4
    "Functional Scripts" : 2
```

```mermaid
pie title Test Distribution by Project
    "SPBSite (API)" : 6
    "BCSrvSqlMq (Unit)" : 5
    "BCSrvSqlMq (Integration)" : 5
    "BCSrvSqlMq (Scripts)" : 2
    "System E2E" : 4
```

---

## Key Pytest Markers

| Marker | Defined In | Usage |
|--------|-----------|-------|
| `integration` | `BCSrvSqlMq/python/pytest.ini` | Tests requiring PostgreSQL, IBM MQ, or network access |
| `asyncio` | `spbsite/pyproject.toml` | Auto-mode: all async tests detected automatically |

---

*Generated on 2026-03-17 | 26 test items across 2 projects*
