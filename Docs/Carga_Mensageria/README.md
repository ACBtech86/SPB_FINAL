# Carga Mensageria

Ferramenta ETL para carga e processamento de mensagens do **Sistema de Pagamentos Brasileiro (SPB)**. Migrada de uma aplicação VB6/SQL Server original para Python/PostgreSQL.

## Visão Geral

A aplicação executa uma série de etapas (steps) que transformam catálogos de mensagens SPB em tabelas normalizadas, esquemas XML/XSL e arquivos HTML de referência. Os dados de entrada são importados de arquivos `.xsd` (XML Schema) oficiais do Banco Central do Brasil.

## Estrutura do Projeto

| Arquivo | Descrição |
|---|---|
| `main.py` | Interface gráfica (Tkinter) — ponto de entrada da aplicação |
| `etapas.py` | Lógica de negócio de todas as etapas ETL (0A a C) |
| `db_connection.py` | Gerenciador de conexão PostgreSQL (substitui ADODB do VB6) |
| `config.py` | Configuração do banco de dados e constantes |
| `init_database.py` | Criação do schema do banco — tabelas de entrada e saída |
| `import_from_xsd.py` | Importação de dados a partir de XSD schemas do BCB |
| `xml_generator.py` | Geração de esquemas XML/XSL para formulários de mensagens |
| `spbmodelo.xsl` | Template XSL base para geração de formulários |
| `emissor.txt` | Lista de tipos de entidades emissoras válidas |
| `spb_schemas.zip` | Arquivo ZIP com os esquemas XSD oficiais do BCB |
| `.env.example` | Template para configuração de ambiente |
| `requirements.txt` | Dependências Python do projeto |

## Requisitos

- Python 3.8+
- PostgreSQL 12+ (servidor de banco de dados)
- Bibliotecas Python:
  - `psycopg` (driver PostgreSQL) — instalar via `pip install -r requirements.txt`
  - `tkinter` (interface gráfica) — incluído no Python padrão
  - `xml.etree.ElementTree`, `xml.dom.minidom` — biblioteca padrão

## Como Usar

### 0. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 1. Configurar Conexão com PostgreSQL

Edite o arquivo `config.py` ou configure variáveis de ambiente:

```bash
# Opção 1: Editar config.py diretamente
# Opção 2: Criar arquivo .env (copie de .env.example)
cp .env.example .env
# Edite .env com suas credenciais PostgreSQL
```

### 2. Inicializar o Banco de Dados

```bash
python init_database.py
```

Isso criará todas as tabelas necessárias no PostgreSQL.

### 3. Importar Dados

Importa os esquemas XSD oficiais do Banco Central:

```bash
python import_from_xsd.py
python import_from_xsd.py caminho/spb_schemas.zip  # caminho opcional
```

Este comando popula todas as tabelas de entrada necessárias (`PLAN_*` e `SPB_*`) a partir dos arquivos XSD contidos no ZIP.

### 4. Executar a Interface Gráfica

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

## Histórico de Migração

- **VB6 → Python:** Código original migrado de Visual Basic 6 com SQL Server para Python
- **SQL Server → SQLite → PostgreSQL:** Evolução do banco de dados para melhor performance e suporte multi-usuário (2025)
- **Access → XSD:** Importação de dados migrada de arquivos `.mdb` legados (Access) para esquemas `.xsd` oficiais do BCB (2025)
- A importação via `.mdb` foi descontinuada e removida em favor da solução baseada em XSD, que é mais mantível e reflete o catálogo atual do SPB
