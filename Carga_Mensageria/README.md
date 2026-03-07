# Carga Mensageria

Ferramenta ETL para carga e processamento de mensagens do **Sistema de Pagamentos Brasileiro (SPB)**. Migrada de uma aplicação VB6/SQL Server original para Python/SQLite.

## Visão Geral

A aplicação executa uma série de etapas (steps) que transformam catálogos de mensagens SPB em tabelas normalizadas, esquemas XML/XSL e arquivos HTML de referência. Os dados de entrada podem ser importados de arquivos `.mdb` (Access) legados ou de arquivos `.xsd` (XML Schema) do Banco Central.

## Estrutura do Projeto

| Arquivo | Descrição |
|---|---|
| `main.py` | Interface gráfica (Tkinter) — ponto de entrada da aplicação |
| `etapas.py` | Lógica de negócio de todas as etapas ETL (0A a C) |
| `db_connection.py` | Gerenciador de conexão SQLite (substitui ADODB do VB6) |
| `init_database.py` | Criação do schema do banco — tabelas de entrada e saída |
| `import_from_mdb.py` | Importação de dados de arquivos Access `.mdb` legados |
| `import_from_xsd.py` | Importação de dados a partir de XSD schemas do BCB |
| `xml_generator.py` | Geração de esquemas XML/XSL para formulários de mensagens |
| `spbmodelo.xsl` | Template XSL base para geração de formulários |
| `emissor.txt` | Lista de tipos de entidades emissoras válidas |
| `BCSPBSTR.db` | Banco de dados SQLite (gerado/populado pela aplicação) |

## Requisitos

- Python 3.8+
- Bibliotecas padrão: `tkinter`, `sqlite3`, `xml.etree.ElementTree`, `xml.dom.minidom`
- Para importação de `.mdb` (opcional): `access-parser`, `pyodbc`

## Como Usar

### 1. Inicializar o Banco de Dados

```bash
python init_database.py                # cria BCSPBSTR.db no diretório atual
python init_database.py caminho.db     # cria em caminho específico
```

### 2. Importar Dados

**A partir de arquivos XSD (recomendado):**
```bash
python import_from_xsd.py
python import_from_xsd.py caminho.db caminho/spb_schemas.zip
```

**A partir de arquivos Access legados:**
```bash
python import_from_mdb.py
```

### 3. Executar a Interface Gráfica

```bash
python main.py
```

## Etapas de Processamento

### Etapas de Configuração (0A–0)
| Etapa | Descrição | Tabela de Saída |
|---|---|---|
| **0A** | Carrega horários das grades de operação | `PLAN_Grade` |
| **0** | Associa mensagens às grades | `PLAN_Grade_X_Msg` |

### Etapas de Geração de Tabelas (1–5)
| Etapa | Descrição | Tabela de Saída |
|---|---|---|
| **1** | Gera códigos de grade com roteamento ISPB | `SPB_CODGRADE` |
| **2** | Mapeia grade × mensagem × destino (com regras de filtragem) | `APP_CODGRADE_X_MSG` |
| **3** | Consolida catálogo de mensagens com eventos | `SPB_MENSAGEM` |
| **4** | Gera dicionário de dados com contagem de domínios | `SPB_DICIONARIO` |
| **5** | Desnormaliza estrutura de campos por mensagem | `SPB_MSGFIELD` |

### Etapas de Geração de Artefatos (A–C)
| Etapa | Descrição | Saída |
|---|---|---|
| **A** | Gera esquemas XML/XSL para formulários de mensagens | `SPB_XMLXSL` |
| **B** | Gera arquivos HTML das listas de domínios | `*.htm` em diretório HTML |
| **C** | Gera arquivo HTML do cadastro ISPB | `ISPB.htm` |

## Modelo de Dados

### Tabelas de Entrada (populadas via importação)
- `PLAN_MENSAGEM` — Catálogo de mensagens SPB
- `PLAN_EVENTO` — Descrições de eventos associados
- `PLAN_DADOS` — Dicionário de campos (tags)
- `PLAN_TIPOLOGIA` — Definições de tipos (formato e tamanho)
- `PLAN_Mensagem_Dados` — Estrutura de campos por mensagem (com sequência)
- `SPB_DOMINIOS` — Listas de valores de domínio
- `SPB_ISPB` — Cadastro de instituições (código ISPB)

### Tabelas de Saída (geradas pelas etapas)
- `PLAN_Grade` / `PLAN_Grade_X_Msg` — Configuração de grades
- `SPB_CODGRADE` — Grades com roteamento ISPB
- `APP_CODGRADE_X_MSG` — Mapeamento grade × mensagem × destino
- `SPB_MENSAGEM` — Catálogo consolidado de mensagens
- `SPB_DICIONARIO` — Dicionário de dados consolidado
- `SPB_MSGFIELD` — Estrutura desnormalizada de campos
- `SPB_XMLXSL` — Esquemas XML e XSL gerados

## Contexto

O ISPB do Banco Cidade (emissor padrão) utilizado é `61377677`. As grades de operação, mapeamentos e regras de roteamento estão codificados em `etapas.py`, refletindo a configuração operacional do participante no SPB.
