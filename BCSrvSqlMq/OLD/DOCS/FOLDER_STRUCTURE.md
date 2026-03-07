# Estrutura de Pastas do Projeto BCSrvSqlMq

## 📁 Diretório Principal
`c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\`

```
BCSrvSqlMq/
├── DOCS/                          # 📚 Documentação
│   ├── README.md                  # Visão geral do projeto
│   ├── CONFIGURACAO.md            # Guia de configuração
│   ├── QUICK_START.md             # Início rápido
│   ├── CONFIG_GUIDE.md            # Guia de configuração detalhado
│   ├── POSTGRESQL_SETUP_GUIDE.md  # Setup PostgreSQL
│   ├── IBM_MQ_SETUP_COMPLETE.md   # Setup IBM MQ
│   └── ... (outros docs)
│
├── Scripts/                       # 🔧 Scripts de instalação e teste
│   ├── INSTALAR.bat               # Instalação principal
│   ├── TESTAR-BD.bat              # Teste de database
│   ├── TESTAR-ODBC.bat            # Teste ODBC
│   ├── DIAGNOSTICO.bat            # Diagnóstico completo
│   └── ... (outros scripts)
│
├── src/                           # 💻 Código-fonte C++
│   ├── MainSrv.cpp
│   ├── InitSrv.cpp
│   ├── ThreadMQ.cpp
│   └── ... (arquivos .cpp/.h)
│
├── build/                         # 🔨 Arquivos de build
│   ├── CMakeCache.txt
│   ├── Release/
│   └── ... (saída do build)
│
└── CMakeLists.txt                 # ⚙️ Configuração CMake
```

## 📁 Diretório de Execução
`C:\BCSrvSqlMq\bin\`

```
C:\BCSrvSqlMq\
├── bin/                           # Executáveis e DLLs
│   ├── Scripts/                   # Scripts de manutenção
│   │   ├── TESTAR-EXE-ORIGINAL.bat
│   │   ├── TESTE-FINAL-COMPLETO.bat
│   │   ├── INICIAR-AGORA.bat
│   │   └── ... (outros scripts)
│   │
│   ├── BCSrvSqlMq.exe            # Executável principal (2001)
│   ├── BCSrvSqlMq.exe.NEW        # Executável modernizado (2026)
│   ├── BCSrvSqlMq.ini            # Configuração
│   │
│   ├── BCMsgSqlMq.dll            # DLL de logging (36KB)
│   ├── BCSMAIL.dll               # DLL de email (28KB)
│   ├── CL32.dll                  # CryptLib 3.2 (672KB)
│   ├── libcrypto-3.dll           # OpenSSL 3.6.1 (3.3MB)
│   ├── libssl-3.dll              # OpenSSL 3.6.1 (701KB)
│   ├── mqm.dll                   # IBM MQ (45KB)
│   └── pugixml.dll               # XML parser (167KB)
│
├── Traces/                        # 📊 Logs do serviço
│   └── TRACE_SPB_02_27.log       # Log atual
│
├── AuditFiles/                    # 🗃️ Arquivos de auditoria
│
└── certificates/                  # 🔐 Certificados SSL
```

## 📝 Organização de Arquivos

### Documentação (DOCS/)
Toda documentação técnica, guias de instalação, troubleshooting e relatórios.

### Scripts (Scripts/)
Todos os arquivos .bat e .ps1 para instalação, teste e manutenção.

### Código-Fonte (src/)
Arquivos .cpp, .h do projeto.

### Build (build/)
Saída da compilação, arquivos temporários do CMake.

### Executáveis (C:\BCSrvSqlMq\bin/)
Diretório de produção com executáveis, DLLs e configurações.

## 🔄 Versões do Executável

- **BCSrvSqlMq.exe** (204KB, 2001): Versão original em uso
- **BCSrvSqlMq.exe.NEW** (222KB, 2026): Versão modernizada C++20 (backup)

## ⚙️ Arquivos de Configuração

- **BCSrvSqlMq.ini**: Configuração principal do serviço
- **pg_hba.conf**: Autenticação PostgreSQL (modificado para md5)

## 📊 Logs e Traces

Todos os logs são criados em `C:\BCSrvSqlMq\Traces\` com o formato:
```
TRACE_SPB_MM_DD.log
```

---

Data de criação: 27/02/2026
Última atualização: 27/02/2026
