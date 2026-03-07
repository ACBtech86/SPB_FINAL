# SPBSite — Test Plan

## Overview

Comprehensive test plan for the SPBSite FastAPI application converted from Classic ASP.
Stack: FastAPI + SQLAlchemy async + PostgreSQL + Jinja2 + SessionMiddleware.
Test stack: pytest-asyncio + httpx.AsyncClient + SQLite in-memory (aiosqlite).

**Total test cases: 89**

---

## 1. Authentication (14 tests)

### 1.1 Login Page Rendering
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 1 | `GET /login` | Returns 200, HTML contains "Finvest DTVM SPB" |
| 2 | `GET /login` when already logged in | Returns 200 (login page still accessible) |

### 1.2 Login Validation
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 3 | `POST /login` with valid credentials | 303 redirect to `/monitoring/control/local`, session contains `user_id` |
| 4 | `POST /login` with wrong password | 401, re-renders login with "Usuario ou senha invalidos" |
| 5 | `POST /login` with nonexistent username | 401, same error message |
| 6 | `POST /login` with empty username | 401 |
| 7 | `POST /login` with empty password | 401 |
| 8 | `POST /login` with inactive user (`is_active=False`) | 401, user cannot login |

### 1.3 Session & Logout
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 9 | `GET /logout` | 303 redirect to `/login`, session cleared |
| 10 | Access protected route without session | 303 redirect to `/login` |
| 11 | Access protected route with invalid `user_id` in session | 303 redirect to `/login`, session cleared |
| 12 | Access protected route with deleted user's `user_id` | 303 redirect to `/login` |

### 1.4 Root Redirect
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 13 | `GET /` unauthenticated | 303 redirect chain → `/login` |
| 14 | `GET /` authenticated | 303 redirect to `/monitoring/control/local` |

---

## 2. Monitoring Routes (16 tests)

### 2.1 Control Table Views
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 15 | `GET /monitoring/control/local` (authenticated, with data) | 200, HTML contains "Controle do STR Local", table rows rendered |
| 16 | `GET /monitoring/control/bacen` (authenticated, with data) | 200, HTML contains "Controle do STR BACEN" |
| 17 | `GET /monitoring/control/local` (empty table) | 200, table rendered with zero rows |
| 18 | `GET /monitoring/control/invalid` | Defaults to "local" channel |
| 19 | Status color coding: row with `status_geral='N'` | Row has CSS class `status-normal` (green) |
| 20 | Status color coding: row with `status_geral='I'` | Row has CSS class `status-warning` (yellow) |
| 21 | Status color coding: row with `status_geral='E'` | Row has CSS class `status-error` (red) |

### 2.2 Message Browse Views
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 22 | `GET /monitoring/messages/inbound/all` | 200, title "Mensagens Recebidas do SPB", combines BACEN+SELIC tables |
| 23 | `GET /monitoring/messages/inbound/bacen` | 200, only BACEN inbound messages |
| 24 | `GET /monitoring/messages/inbound/selic` | 200, only SELIC inbound messages |
| 25 | `GET /monitoring/messages/outbound/all` | 200, title "Mensagens Enviadas para o SPB" |
| 26 | `GET /monitoring/messages/outbound/bacen` | 200, only BACEN outbound messages |
| 27 | `GET /monitoring/messages/outbound/selic` | 200, only SELIC outbound messages |
| 28 | Invalid direction defaults to "inbound" | `GET /monitoring/messages/invalid/all` → treats as inbound |
| 29 | Invalid channel defaults to "all" | `GET /monitoring/messages/inbound/invalid` → treats as all |
| 30 | Statistics sidebar: REQ/RSP counts | Stats show correct counts based on `MQ_QN_*` field substring [3:6] |

---

## 3. Log Routes (5 tests)

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 31 | `GET /logs/all` | 200, title "Log do Sistema SPB", combines both tables |
| 32 | `GET /logs/bacen` | 200, only BACEN log entries |
| 33 | `GET /logs/selic` | 200, only SELIC log entries |
| 34 | `GET /logs/invalid` | Defaults to "all" |
| 35 | Log statistics: REQ/REP/GerN/GerS counts | Correct counts in sidebar |

---

## 4. Message Processing Routes (12 tests)

### 4.1 Message Selector
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 36 | `GET /messages/select` | 200, dropdown with all `SPBMensagem` types from DB |
| 37 | `GET /messages/select` (empty DB) | 200, empty dropdown |

### 4.2 Dynamic Form Rendering
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 38 | `GET /messages/form/{valid_msg_id}` | 200, form rendered with fields from `SPB_MSGFIELD` + `SPB_DICIONARIO` |
| 39 | `GET /messages/form/{invalid_msg_id}` | 200, error "Mensagem nao encontrada" |
| 40 | Form shows required fields with `*` indicator | Fields with `MSG_CPOOBRIG='S'` show required marker |
| 41 | Form shows correct input types | Date fields have `dd/mm/aaaa` placeholder, time fields `HH:MM:SS` |
| 42 | Group fields render as `<fieldset>` | Fields with `Grupo_` prefix create nested fieldsets |

### 4.3 Form Submission & XML Generation
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 43 | `POST /messages/submit` with valid data | 200, success message with NU_OPE, dest_table, queue_name |
| 44 | `POST /messages/submit` with missing required field | 200, error "Campo obrigatorio: {field}" |
| 45 | `POST /messages/submit` with invalid date format | 200, error "Data invalida: {field}" |
| 46 | `POST /messages/submit` with empty `formName` | 303 redirect to `/messages/select` |
| 47 | XML inserted into correct table (`spb_local_to_bacen` vs `spb_local_to_selic`) | Based on `COD_GRADE`: SEL01 → selic, else → bacen |

---

## 5. Queue Management Routes (8 tests)

### 5.1 Queue Display
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 48 | `GET /queue` with pending messages | 200, table with checkboxes, total value, balance summary |
| 49 | `GET /queue` with empty queue | 200, empty table, zeros for totals |
| 50 | Balance summary shows STR/COMPE/CIP/Total | Values from `Camaras` table, formatted as BRL |

### 5.2 Queue Processing
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 51 | `POST /queue/process` with valid seq IDs | 303 redirect to `/queue`, selected messages updated to status "E" |
| 52 | `POST /queue/process` with empty processados | 303 redirect, no changes |
| 53 | `POST /queue/process` with "d" entries (deselected) | "d" entries are filtered out, only valid IDs processed |
| 54 | `POST /queue/process` with non-numeric entries | Non-numeric entries ignored |

### 5.3 Message XML Viewer
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 55 | `GET /queue/message/{valid_seq}` | 200, XML tree rendered, raw XML displayed |
| 56 | `GET /queue/message/{invalid_seq}` | 200, "Nenhuma mensagem XML encontrada" |

---

## 6. XML Viewer Routes (5 tests)

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 57 | `GET /viewer/spb_bacen_to_local/{id}` | 200, fetches `msg` column, renders XML tree |
| 58 | `GET /viewer/fila/{seq}` | 200, fetches `msg_xml` column, renders tree |
| 59 | `GET /viewer/invalid_table/{id}` | 200, error "Tabela nao permitida" |
| 60 | `GET /viewer/{table}/{id}` with no XML content | 200, shows warning |
| 61 | Allowed tables whitelist enforced | Only 5 tables allowed: `spb_bacen_to_local`, `spb_selic_to_local`, `spb_local_to_bacen`, `spb_local_to_selic`, `fila` |

---

## 7. Service Layer — Unit Tests (30 tests)

### 7.1 xml_utils.py (8 tests)
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 62 | `parse_xml("<root><child/></root>")` | Returns Element with tag "root" |
| 63 | `parse_xml("")` | Returns `None` |
| 64 | `parse_xml(None)` | Returns `None` |
| 65 | `parse_xml("not xml")` | Returns `None` |
| 66 | `xml_to_tree(element)` | Returns dict with tag, text, attributes, children, level |
| 67 | `format_datetime_br("20010322143000")` | Returns `"22/03/2001.14:30:00"` |
| 68 | `format_datetime_br(datetime(2001,3,22,14,30))` | Returns `"22/03/2001.14:30:00"` |
| 69 | `format_datetime_br(None)` | Returns `""` |
| 70 | `format_currency_br(1234567.89)` | Returns `"1.234.567,89"` |
| 71 | `format_currency_br(0)` | Returns `"0,00"` |
| 72 | `format_currency_br(None)` | Returns `"0,00"` |

### 7.2 operation_number.py (4 tests)
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 73 | `generate_operation_number()` | Returns 23-char string starting with "61377677" |
| 74 | Date portion matches today | Characters [8:16] = today's YYYYMMDD |
| 75 | Sequence increments | Two consecutive calls produce different numbers |
| 76 | 100 calls produce 100 unique numbers | Thread-safe uniqueness |

### 7.3 xml_builder.py (6 tests)
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 77 | `_convert_date("22/03/2001")` | Returns `"20010322"` |
| 78 | `_convert_datetime("22/03/2001 14:30:00")` | Returns `"20010322143000"` |
| 79 | `_convert_time("14:30:00")` | Returns `"143000"` |
| 80 | `_determine_destination("SEL01")` | Returns `("00038121", "selic")` |
| 81 | `_determine_destination("BCN01")` | Returns `("00038166", "bacen")` |
| 82 | `_determine_queue_name("STR0001R1", "00038166")` | Contains "QR.RSP" (response queue) |
| 83 | `_determine_queue_name("STR0001", "00038166")` | Contains "QR.REQ" (request queue) |

### 7.4 form_engine.py (5 tests)
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 84 | `load_form(db, valid_id)` | Returns `FormDefinition` with fields |
| 85 | `load_form(db, invalid_id)` | Returns `None` |
| 86 | `validate_form(form_def, {complete data})` | `is_valid=True`, empty errors |
| 87 | `validate_form(form_def, {missing required})` | `is_valid=False`, error contains "Campo obrigatorio" |
| 88 | `validate_form(form_def, {bad date format})` | `is_valid=False`, error contains "Data invalida" |

### 7.5 queue_manager.py (1 test)
| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 89 | `process_selected(db, [seq_ids])` | Updates Fila.status to "E", returns count |

---

## 8. Test Execution Strategy

### 8.1 Test Pyramid

```
         /  E2E  \          5 tests  — Full login → browse → submit flow
        / Integr. \        30 tests  — Route handlers with test DB
       /   Unit    \       54 tests  — Pure functions, service layer
```

### 8.2 Test Data Fixtures Required

| Fixture | Seed Data |
|---------|-----------|
| `admin_user` | User(username="admin", password_hash=bcrypt("admin"), is_active=True) |
| `inactive_user` | User(username="disabled", is_active=False) |
| `control_data` | 3 SPBControle rows (status N, I, E) + 2 BacenControle rows |
| `inbound_messages` | 5 SPBBacenToLocal + 3 SPBSelicToLocal with mixed statuses |
| `outbound_messages` | 4 SPBLocalToBacen + 2 SPBLocalToSelic with MQ timestamps |
| `log_entries` | 4 SPBLogBacen + 3 SPBLogSelic |
| `message_catalog` | 3 SPBMensagem (STR0001, STR0001R1, SEL0001) |
| `field_definitions` | 5 SPBMsgField rows for STR0001 (1 group + 3 fields + 1 close) |
| `field_dictionary` | 3 SPBDicionario entries (alfanumerico, numerico, data) |
| `queue_data` | 4 Fila rows + 1 Camaras row |

### 8.3 Priority Order

| Priority | Category | Count | Rationale |
|----------|----------|-------|-----------|
| P0 — Critical | Auth (login/session/redirect) | 14 | Gate to entire app |
| P0 — Critical | XML builder (correct XML output) | 6 | Core business logic |
| P1 — High | Monitoring routes (data display) | 16 | Most-used pages |
| P1 — High | Queue processing (state mutation) | 8 | Financial operations |
| P2 — Medium | Message form engine | 12 | Complex but less frequent |
| P2 — Medium | Utility functions | 12 | Date/currency formatting |
| P3 — Low | Viewer/Logs (read-only) | 10 | Display only |
| P3 — Low | Edge cases (invalid params) | 11 | Defensive checks |

### 8.4 Commands

```bash
# Run all tests
pytest tests/ -v

# Run by priority
pytest tests/test_auth.py -v                     # P0
pytest tests/test_monitoring.py -v               # P1
pytest tests/test_messages.py -v                 # P2

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run only unit tests (fast, no DB)
pytest tests/test_monitoring.py tests/test_messages.py -v -k "not async"
```

---

## 9. Acceptance Criteria

The conversion is considered complete when:

- [ ] All 89 test cases pass
- [ ] Login/logout flow works end-to-end
- [ ] All 12 original monitoring views render (2 control + 6 message + 3 log + 1 dashboard)
- [ ] Status color-coding matches original (N=green, I/P=yellow, E/R=red)
- [ ] Date formatting matches original Brazilian format (dd/mm/yyyy.HH:MM:SS)
- [ ] Currency formatting matches original BRL format (X.XXX,XX)
- [ ] XML message generation produces valid SPBDOC structure
- [ ] Queue selection/deselection JS works (total updates in real-time)
- [ ] Operation number is unique per call (23 chars: ISPB + date + sequence)
- [ ] No SQL injection possible via viewer table parameter (whitelist enforced)
- [ ] Unauthenticated access always redirects to `/login`
