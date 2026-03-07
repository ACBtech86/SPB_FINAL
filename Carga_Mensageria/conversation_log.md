# Carga Mensageria — Conversation Log

## 1. Project Documentation

The project was fully documented in `README.md`. It covers:

- **Origin**: Migrated from VB6/SQL Server to Python/SQLite
- **Purpose**: ETL tool for loading and processing SPB (Sistema de Pagamentos Brasileiro) messages
- **Entry point**: `python main.py` (Tkinter GUI)
- **Files**:
  - `main.py` — GUI (Tkinter), replicates the VB6 `Etapas_Carga.frm`
  - `etapas.py` — Core business logic for all ETL steps (0A through C)
  - `db_connection.py` — SQLite connection manager (replaces ADODB from VB6)
  - `init_database.py` — Database schema creation (input + output tables)
  - `import_from_mdb.py` — Legacy import from Access `.mdb` files
  - `import_from_xsd.py` — Import from BCB XSD schemas (`spb_schemas.zip`)
  - `xml_generator.py` — XML/XSL schema generation for message forms
  - `spbmodelo.xsl` — Base XSL template for form generation
  - `emissor.txt` — List of valid emitter entity types
  - `BCSPBSTR.db` — SQLite database (generated/populated by the app)

---

## 2. Inputs Used in Each Etapa

### Etapas de Configuração

| Etapa | Inputs | Saída |
|---|---|---|
| **0A** | Constante `GRADE_SCHEDULES` (hardcoded em `etapas.py`) | `PLAN_Grade` |
| **0** | Constante `GRADE_MSG_MAPPINGS` (hardcoded em `etapas.py`) | `PLAN_Grade_X_Msg` |

### Etapas de Geração de Tabelas

| Etapa | Inputs | Saída |
|---|---|---|
| **1** | `PLAN_Grade` + `SPB_DOMINIOS` + constante `ISPB_DESTINO_MAP` | `SPB_CODGRADE` |
| **2** | `SPB_CODGRADE` + `PLAN_Grade_X_Msg` + `SPB_MENSAGEM` + constantes `VALID_EMITTER_TYPES` e regras especiais por grade (GEN02, LDL01, LTR01) | `APP_CODGRADE_X_MSG` |
| **3** | `PLAN_MENSAGEM` + `PLAN_EVENTO` | `SPB_MENSAGEM` |
| **4** | `PLAN_DADOS` + `PLAN_TIPOLOGIA` + `SPB_DOMINIOS` (para contagem de itens) | `SPB_DICIONARIO` |
| **5** | `PLAN_Mensagem_Dados` + `PLAN_MENSAGEM` + `PLAN_DADOS` | `SPB_MSGFIELD` |

### Etapas de Geração de Artefatos

| Etapa | Inputs | Saída |
|---|---|---|
| **A** | `SPB_MSGFIELD` + `SPB_DICIONARIO` + `SPB_DOMINIOS` + template `spbmodelo.xsl` + parâmetro opcional `Código Msg` | `SPB_XMLXSL` |
| **B** | `SPB_DOMINIOS` | Arquivos `*.htm` no diretório HTML |
| **C** | `SPB_ISPB` | `ISPB.htm` |

### Dependency Chain

```
Importação (mdb/xsd) → popula tabelas PLAN_* e SPB_DOMINIOS/SPB_ISPB
  ├─ 0A → 0 → 1 → 2  (cadeia de grades/roteamento)
  ├─ 3                 (mensagens, independente)
  ├─ 4                 (dicionário, independente)
  ├─ 5                 (campos, independente)
  ├─ A                 (depende de 4 e 5: usa SPB_MSGFIELD + SPB_DICIONARIO)
  ├─ B                 (independente, usa SPB_DOMINIOS direto)
  └─ C                 (independente, usa SPB_ISPB direto)
```

---

## 3. Message Source — XSD Files

Messages are generated from XSD files in `spb_schemas.zip` (provided by Banco Central). Each XSD defines one or more SPB messages using XML Schema with BCB-specific annotations (`cat:` namespace).

### What is extracted from each XSD:

1. **Messages** — from `SISMSGComplexType` choice elements, with metadata from `cat:InfMensagem` annotations
2. **Events** — from `DOC` element's `cat:InfEvento` annotation
3. **Field structure** — by recursively flattening `xs:sequence`/`xs:choice`, including nested groups (`Grupo_`, `Repet_`)
4. **Data dictionary** — from `xs:simpleType` definitions with restriction facets

### Alternative import path:

`import_from_mdb.py` imports from legacy Access `.mdb` files (`bdnew.mdb` and `Spb.mdb`). Both paths populate the same tables.

---

## 4. Files That Can Be Deleted

The database (`BCSPBSTR.db`) is already fully populated:

| Table | Rows |
|---|---|
| PLAN_MENSAGEM | 1093 |
| PLAN_EVENTO | 1093 |
| PLAN_DADOS | 2363 |
| PLAN_TIPOLOGIA | 1128 |
| PLAN_Mensagem_Dados | 14489 |
| SPB_MENSAGEM | 1093 |
| SPB_DICIONARIO | 2363 |
| SPB_MSGFIELD | 14489 |
| SPB_XMLXSL | 1093 |
| SPB_ISPB | 2335 |
| SPB_DOMINIOS | (empty) |

### Can be deleted (only needed to rebuild DB from scratch):
- `import_from_xsd.py`
- `import_from_mdb.py`
- `init_database.py`

### Must keep (used at runtime):
- `main.py`, `etapas.py`, `db_connection.py`, `xml_generator.py`
- `spbmodelo.xsl`, `BCSPBSTR.db`, `emissor.txt`

---

## 5. Code Fix Applied

`import_from_xsd.py` — changed `DEFAULT_ZIP_PATH` to look for `spb_schemas.zip` in the project folder instead of the old path (`../SPBCidade/SPB1/SPB Fontes Producao/GeraMsgDB/`).

---

## 6. Detailed Explanation of `import_from_xsd.py`

### Phase 1 — Setup (lines 1–39)
- Imports and namespace constants (`XS` for W3C XML Schema, `CAT` for BCB catalog)

### Phase 2 — XSD Parsing Helpers (lines 42–292)

- **`_parse_simple_types(root)`** — Parses all `xs:simpleType` definitions. Extracts base type, facets (maxLength, totalDigits, fractionDigits, pattern), enumeration count, and description. Derives format (Alfanumérico/Numérico/Data/DataHora) and size from base type.

- **`_index_complex_types(root)`** — Builds lookup dict of `xs:complexType` by name. These represent message bodies or field groups.

- **`_flatten_sequence(seq_elem, complex_types, fields)`** — Recursively walks `xs:sequence`, handling `xs:element` and `xs:choice` (all choice alternatives treated as optional).

- **`_process_element(elem, complex_types, fields)`** — Processes a single `xs:element`: reads name/type/minOccurs, extracts `cat:InfCampo` annotation, and recurses into complexTypes for nested groups.

- **`parse_xsd(content, filename)`** — Main per-file parser:
  1. Parses simpleTypes and complexTypes
  2. Extracts event metadata from `DOC > cat:InfEvento`
  3. Finds messages in `SISMSGComplexType > xs:choice`, flattens each message's fields

- **`get_type_info(type_name, all_types)`** — Resolves a field's type to format/size info with fallback to built-in XSD type heuristics.

### Phase 3 — Parse All XSDs (lines 298–380)
1. Opens `spb_schemas.zip`, finds all `.XSD` files (sorted alphabetically)
2. Parses each with `parse_xsd()`
3. Deduplicates messages (E-variants like `BMC0102E.XSD` are skipped if base was already processed)
4. Merges simpleTypes globally (first occurrence wins)
5. Builds unique field dictionary (prefers entries with field names)

### Phase 4 — Populate Database (lines 384–534)
Inside a transaction:
1. Clears 9 target tables
2. Inserts `SPB_MENSAGEM` (1 row per unique message)
3. Inserts `PLAN_MENSAGEM` + `PLAN_EVENTO` (input tables for Etapa 3)
4. Inserts `SPB_DICIONARIO` + `PLAN_DADOS` + `PLAN_TIPOLOGIA` (field dictionary)
5. Inserts `SPB_MSGFIELD` + `PLAN_Mensagem_Dados` (flat field structure with sequential numbering)

### Phase 5 — Generate XML/XSL (lines 549–556)
Runs Etapa A automatically to populate `SPB_XMLXSL`.

### Phase 6 — Summary (lines 561–577)
Prints row counts for all populated tables.

### Data Flow

```
spb_schemas.zip
  └─ *.XSD files
       ├─ xs:simpleType      → SPB_DICIONARIO + PLAN_DADOS + PLAN_TIPOLOGIA
       ├─ SISMSGComplexType  → SPB_MENSAGEM + PLAN_MENSAGEM + PLAN_EVENTO
       ├─ xs:sequence fields → SPB_MSGFIELD + PLAN_Mensagem_Dados
       └─ (Etapa A runs)    → SPB_XMLXSL
```
