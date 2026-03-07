# BCSrvSqlMq - Guia de Configuração

## 📋 Visão Geral

O **BCSrvSqlMq** é um serviço Windows que integra sistemas bancários através de:
- **PostgreSQL** - Banco de dados para persistência
- **IBM MQ** - Middleware de mensageria
- **Cryptlib** - Criptografia e assinatura digital

---

## 🚀 Início Rápido

### 1. Executar o Script de Teste

```batch
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq"
TestarServico.bat
```

O script irá:
- ✅ Verificar todas as dependências
- ✅ Criar diretórios necessários
- ✅ Oferecer menu interativo para instalação

### 2. Instalação Manual

```batch
# Como Administrador
BCSrvSqlMq.exe -i        # Instala o serviço
net start BCSrvSqlMq     # Inicia o serviço
```

---

## ⚙️ Configuração do BCSrvSqlMq.ini

### [Servico] - Configurações do Serviço

```ini
[Servico]
ServiceName=BCSrvSqlMq    # Nome do serviço Windows
Trace=D                   # Nível de trace (D=Debug, I=Info, W=Warning, E=Error)
MonitorPort=14499         # Porta TCP para monitoramento
SrvTimeout=120            # Timeout em segundos
MaxLenMsg=32768           # Tamanho máximo de mensagem (32KB)
```

### [Diretorios] - Caminhos de Trabalho

```ini
[Diretorios]
DirTraces=C:\BCSrvSqlMq\Traces        # Logs de debug/trace
DirAudFile=C:\BCSrvSqlMq\AuditFiles   # Arquivos de auditoria
```

**⚠️ IMPORTANTE:** Estes diretórios são criados automaticamente pelo script.

### [DataBase] - Conexão PostgreSQL (DSN-less)

```ini
[DataBase]
# Não requer configuração ODBC DSN!
DBAliasName=BCSPBSTR      # Nome do banco de dados
DBServer=localhost        # Servidor PostgreSQL
DBPort=5432               # Porta padrão PostgreSQL
DBUserName=postgres       # Usuário do banco
DBPassword=Rama1248       # ⚠️ Senha - ALTERE EM PRODUÇÃO!

# Tabelas (use lowercase ou "quoted identifiers")
DbTbStrLog=spb_log_bacen              # Log de transações
DbTbBacenCidadeApp=spb_bacen_to_local # Mensagens Bacen→Local
DbTbCidadeBacenApp=spb_local_to_bacen # Mensagens Local→Bacen
DbTbControle=spb_controle             # Tabela de controle
```

**📝 Notas:**
- A conexão usa ODBC DSN-less (sem configuração manual)
- String de conexão: `DRIVER={PostgreSQL Unicode};SERVER=...`
- Senha é registrada no log (sem o valor real)

**🔧 Para testar:**
```batch
psql -h localhost -p 5432 -U postgres -d bcspbstr
```

### [MQSeries] - IBM MQ

```ini
[MQSeries]
MQServer=localhost                      # Servidor IBM MQ
QueueManager=QM.61377677.01             # Nome do Queue Manager
QueueTimeout=30                         # Timeout em segundos

# Filas Locais (Local Queues)
QLBacenCidadeReq=QL.61377677.01.ENTRADA.BACEN  # Entrada Bacen
QLBacenCidadeRsp=QL.61377677.01.SAIDA.BACEN    # Saída Bacen
QLIFCidadeReq=QL.61377677.01.ENTRADA.IF        # Entrada IF
QLIFCidadeRsp=QL.61377677.01.SAIDA.IF          # Saída IF

# Filas Remotas (Remote Queues)
QRCidadeBacenReq=QR.61377677.01.ENTRADA.BACEN  # Para Bacen
QRCidadeBacenRsp=QR.61377677.01.SAIDA.BACEN    # De Bacen
QRCidadeIFReq=QR.61377677.01.ENTRADA.IF        # Para IF
QRCidadeIFRsp=QR.61377677.01.SAIDA.IF          # De IF
```

**🔧 Para testar:**
```batch
# Verificar Queue Managers
dspmq

# Verificar filas
echo "DISPLAY QMGR" | runmqsc QM.61377677.01
echo "DISPLAY QLOCAL(*)" | runmqsc QM.61377677.01
```

### [E-Mail] - Notificações

```ini
[E-Mail]
ServerEmail=smtp.yourserver.com           # Servidor SMTP
SenderEmail=bcsrvsqlmq@yourcompany.com    # Email remetente
SenderName=BCSrvSqlMq Service             # Nome remetente
DestEmail=admin@yourcompany.com           # Email destino
DestName=Administrator                    # Nome destino
# CC1-CC5: Cópias (opcional)
```

**⚠️ Configurar para receber notificações de erros!**

### [Security] - Segurança e Criptografia

```ini
[Security]
UnicodeEnable=S                           # S=Sim, N=Não
SecurityEnable=N                          # Habilita criptografia
SecurityDB=Public Keys                    # KeyStore
PublicKeyLabel=yourserver.spb.net.br      # Label chave pública
PrivateKeyFile=C:\BCSrvSqlMq\certificates\private.key
PrivateKeyLabel=SPB Key                   # Label chave privada
KeyPassword=changeme                      # ⚠️ Senha - ALTERE!
```

**🔐 Importante:**
- `SecurityEnable=N` desabilita criptografia (apenas para desenvolvimento)
- Em **produção**, configure certificados válidos

---

## 📂 Estrutura de Diretórios

```
C:\BCSrvSqlMq\
├── Traces\              # Logs de debug
│   └── BCSrvSqlMq_DD_MM_YYYY.log
├── AuditFiles\          # Auditoria de mensagens
│   └── BCSrvSqlMq_DD_MM_YYYY.Audit
└── certificates\        # Certificados (se SecurityEnable=S)
    └── private.key
```

---

## 🔍 Monitoramento

### Porta de Monitoramento

O serviço escuta na porta **14499** (configurável no INI) para:
- Status das tasks
- Estatísticas de filas
- Health check

### Logs

**Event Viewer:**
- Aplicativo: `BCSrvSqlMq`
- Eventos de inicialização, paradas e erros

**Arquivos de Log:**
- `C:\BCSrvSqlMq\Traces\BCSrvSqlMq_*.log` - Debug detalhado
- `C:\BCSrvSqlMq\AuditFiles\BCSrvSqlMq_*.Audit` - Auditoria de mensagens

---

## 🐛 Troubleshooting

### Serviço não inicia

1. **Verificar Event Viewer:**
   ```
   eventvwr.msc → Windows Logs → Application
   ```

2. **Verificar PostgreSQL:**
   ```batch
   psql -h localhost -U postgres -d bcspbstr
   ```

3. **Verificar IBM MQ:**
   ```batch
   dspmq
   ```

4. **Verificar DLLs:**
   - `libcrypto-3.dll`, `libssl-3.dll`, `pugixml.dll` devem estar no diretório do executável
   - IBM MQ DLLs devem estar no PATH

### Erro "DLL não encontrada"

```batch
# Copiar DLLs necessárias
copy "C:\dev\vcpkg\installed\x86-windows\bin\*.dll" .
```

### Erro de conexão PostgreSQL

Verificar:
- PostgreSQL está rodando?
- Firewall bloqueando porta 5432?
- Usuário/senha corretos no INI?
- Banco `bcspbstr` existe?

### Erro de conexão IBM MQ

Verificar:
- Queue Manager está ativo? (`dspmq`)
- Filas existem? (`echo "DISPLAY QLOCAL(*)" | runmqsc QM.61377677.01`)
- Permissões de acesso configuradas?

---

## 📊 Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                   BCSrvSqlMq                        │
│  ┌──────────────────────────────────────────────┐   │
│  │  Main Service (Monitor Port 14499)          │   │
│  └──────────────────────────────────────────────┘   │
│           │                 │                       │
│    ┌──────┴──────┐   ┌─────┴──────┐               │
│    │   Bacen     │   │     IF     │               │
│    │   Tasks     │   │   Tasks    │               │
│    │  Req/Rsp    │   │  Req/Rsp   │               │
│    │  Rep/Sup    │   │  Rep/Sup   │               │
│    └──────┬──────┘   └─────┬──────┘               │
└───────────┼──────────────────┼────────────────────┘
            │                  │
     ┌──────┴──────┐    ┌─────┴──────┐
     │   IBM MQ    │    │ PostgreSQL │
     │  Queues     │    │  Database  │
     └─────────────┘    └────────────┘
```

---

## ✅ Checklist de Produção

- [ ] Alterar senha do PostgreSQL (`DBPassword`)
- [ ] Configurar email de notificações
- [ ] Habilitar segurança se necessário (`SecurityEnable=S`)
- [ ] Configurar certificados válidos
- [ ] Testar conectividade PostgreSQL
- [ ] Testar conectividade IBM MQ
- [ ] Verificar permissões de diretórios
- [ ] Configurar backup dos logs/audit
- [ ] Documentar procedimentos operacionais
- [ ] Testar recovery após falhas

---

## 📞 Suporte

- **Logs:** `C:\BCSrvSqlMq\Traces\`
- **Event Viewer:** Aplicativo → BCSrvSqlMq
- **Porta Monitor:** 14499

**Build Info:**
- Versão: 1.0.6
- Arquitetura: 32-bit (x86)
- C++ Standard: C++20
- Compilador: MSVC 19.50
- Data: 2026-02-27
