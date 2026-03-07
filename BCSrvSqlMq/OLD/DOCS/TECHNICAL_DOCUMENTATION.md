# BCSrvSqlMq - Documentação Técnica Completa 📚

**Versão:** 1.0.5 (C++20 Modernized)
**Data:** 21/02/2026
**Projeto:** Sistema de Mensageria SPB (Sistema de Pagamentos Brasileiro)

---

## 📋 Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Arquitetura Geral](#2-arquitetura-geral)
3. [Hierarquia de Classes](#3-hierarquia-de-classes)
4. [Windows Service Infrastructure](#4-windows-service-infrastructure)
5. [Monitor TCP/IP](#5-monitor-tcpip)
6. [Threads de Processamento MQ](#6-threads-de-processamento-mq)
7. [Classes de Banco de Dados](#7-classes-de-banco-de-dados)
8. [Gerenciamento de Clientes](#8-gerenciamento-de-clientes)
9. [Modelo de Threading](#9-modelo-de-threading)
10. [Fluxo de Dados](#10-fluxo-de-dados)
11. [Configuração](#11-configuração)
12. [Segurança e Criptografia](#12-segurança-e-criptografia)
13. [Referência de API](#13-referência-de-api)

---

## 1. Visão Geral do Sistema

### Propósito

**BCSrvSqlMq** é um serviço Windows NT que gerencia o fluxo bidirecional de mensagens entre dois sistemas:
- **Bacen** (Banco Central do Brasil)
- **IF/Cidade** (Instituição Financeira/Sistema Cidade)

### Funcionalidades Principais

- ✅ Processamento multi-thread de mensagens MQSeries
- ✅ Persistência em SQL Server
- ✅ Criptografia e assinatura digital de mensagens
- ✅ Servidor TCP/IP para monitoramento e administração
- ✅ Log estruturado e auditoria
- ✅ Validação de XML (DTD)
- ✅ Gerenciamento de timeout e retry
- ✅ Suporte a Unicode/ANSI

### Tecnologias

| Componente | Tecnologia |
|------------|------------|
| **Linguagem** | C++20 (modernizado de C++98) |
| **Build** | CMake 3.20+ (Visual Studio 17 2022) |
| **Framework** | MFC (Microsoft Foundation Classes) |
| **Message Queue** | IBM MQ Series 9.x |
| **Database** | SQL Server (via ODBC) |
| **XML** | MSXML (COM) |
| **Crypto** | CryptLib (legado, pendente migração) |
| **Network** | Winsock 2.0 |
| **Threading** | std::thread + Win32 Events (híbrido) |

---

## 2. Arquitetura Geral

### Diagrama de Componentes

```
┌───────────────────────────────────────────────────────────────┐
│                   Windows Service Host                        │
│                                                               │
│  ┌──────────────┐                                            │
│  │  CInitSrv    │  ◄── Herda de CNTService                   │
│  │  (Service)   │      (Windows Service Base)                │
│  └──────┬───────┘                                            │
│         │                                                     │
│         │ cria e gerencia                                     │
│         ↓                                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              CMainSrv                                │   │
│  │         (Orquestrador Principal)                     │   │
│  │                                                       │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Collections (Thread-safe)                  │    │   │
│  │  │  • m_TaskList    - Threads ativos           │    │   │
│  │  │  • m_ClientList  - Clientes TCP             │    │   │
│  │  │  • m_MonitorList - Monitor connections      │    │   │
│  │  │  • m_StopList    - Threads parando          │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │                                                       │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Event Signals                              │    │   │
│  │  │  • TIMER        - Timer periódico           │    │   │
│  │  │  • STOP         - Shutdown                  │    │   │
│  │  │  • PAUSE        - Pausar processamento      │    │   │
│  │  │  • CONTINUE     - Retomar processamento     │    │   │
│  │  │  • MONITOR_STOP - Parar monitor             │    │   │
│  │  │  • TASKSAPP_STOP - Parar threads MQ         │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                     │
│         │ cria e controla                                     │
│         ↓                                                     │
│  ┌──────────────────┬──────────────────┬─────────────────┐  │
│  │                  │                  │                 │  │
│  │   CMonitor       │  8 x CThreadMQ   │    Audit        │  │
│  │   (TCP Server)   │  (MQ Processors) │    Logging      │  │
│  │                  │                  │                 │  │
│  │  • 50 clientes   │  ┌────────────┐  │  • File-based   │  │
│  │  • Port 8080     │  │ CBacenReq  │  │  • Daily rotate │  │
│  │  • Admin ops     │  │ CBacenRsp  │  │  • Binary       │  │
│  │                  │  │ CBacenRep  │  │                 │  │
│  │                  │  │ CBacenSup  │  │                 │  │
│  │                  │  │ CIFReq     │  │                 │  │
│  │                  │  │ CIFRsp     │  │                 │  │
│  │                  │  │ CIFRep     │  │                 │  │
│  │                  │  │ CIFSup     │  │                 │  │
│  │                  │  └────────────┘  │                 │  │
│  └──────────────────┴──────────────────┴─────────────────┘  │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         ↓                  ↓                  ↓
   ┌──────────┐      ┌─────────────┐    ┌──────────┐
   │ IBM MQ   │      │ SQL Server  │    │ TCP/IP   │
   │ Series   │      │ Database    │    │ Clients  │
   └──────────┘      └─────────────┘    └──────────┘
```

### Fluxo de Mensagem (High-Level)

```
1. Chegada de Mensagem:
   MQ Queue → CBacenReq::ProcessaQueue()

2. Processamento:
   • Parse XML
   • Validação DTD
   • Verificação de assinatura digital
   • Descriptografia (se necessário)

3. Persistência:
   • CBacenAppRS→AddNew() - Gravar tabela de aplicação
   • CSTRLogRS→AddNew() - Gravar log estruturado
   • CControleRS→Edit() - Atualizar controle

4. Roteamento:
   • Se precisa resposta: enfileira para CIFReq
   • Se é replicação: enfileira para CIFRep

5. Resposta:
   CIFRsp→ProcessaQueue() ← MQ Queue (resposta)

6. Finalização:
   • Atualizar registros com IDs de correlação
   • Auditoria
   • Limpar buffers
```

---

## 3. Hierarquia de Classes

### Diagrama de Herança

```
CObject (MFC Base)
├─ CNTService (Windows Service Infrastructure)
│  └─ CInitSrv (Application Service Implementation)
│
├─ CThreadMQ (Message Queue Thread Base)
│  ├─ CBacenReq (Bacen Request Processor)
│  ├─ CBacenRsp (Bacen Response Processor)
│  ├─ CBacenRep (Bacen Replication)
│  ├─ CBacenSup (Bacen Support)
│  ├─ CIFReq (Interface Request Sender)
│  ├─ CIFRsp (Interface Response Processor)
│  ├─ CIFRep (Interface Replication)
│  └─ CIFSup (Interface Support)
│
├─ CMonitor (TCP/IP Server)
│
├─ CClientItem (TCP Client Connection)
│
├─ CQueueList (Thread-safe Collection)
│
├─ CRecordset (MFC Database Base)
│  ├─ CBacenAppRS (Bacen Application Data)
│  ├─ CIFAppRS (Interface Application Data)
│  ├─ CControleRS (Control/Status Table)
│  └─ CSTRLogRS (Structured Log Table)
│
└─ CDatabase (MFC Database Base)
   └─ CBCDatabase (Custom Database Wrapper)
```

### Relacionamentos Chave

```
CInitSrv
  ├── owns → CMainSrv
  │          ├── owns → CMonitor
  │          ├── owns → CQueueList (4 instances)
  │          └── creates → CThreadMQ[] (8 instances)
  │                        ├── uses → CBCDatabase[]
  │                        └── uses → CRecordset[]
  │
  └── configures → INI Settings
                   ├── Database connection strings
                   ├── MQ queue names
                   ├── TCP port
                   ├── Crypto settings
                   └── Paths (logs, audit, keys)
```

---

## 4. Windows Service Infrastructure

### CNTService (Base Class)

**Arquivo:** [ntservice.h](ntservice.h), [ntservice.cpp](ntservice.cpp)

#### Responsabilidades

- Gerenciar ciclo de vida do serviço Windows
- Responder a comandos SCM (Service Control Manager)
- Event logging no Windows Event Log
- Instalação/desinstalação do serviço

#### Métodos Principais

##### Instalação e Lifecycle

```cpp
class CNTService : public CObject
{
public:
    // Construtor
    CNTService(
        const char* szServiceName,  // Nome do serviço
        const char* szDependencies  // Dependências (separadas por NULL)
    );

    // Instalação
    BOOL Install();
    BOOL Uninstall();
    BOOL IsInstalled();

    // Execução
    BOOL StartService();
    void Run();  // Main service loop

    // Status
    void SetStatus(DWORD dwState);
    BOOL Initialize();

    // Logging
    void LogEvent(
        WORD wType,        // EVENTLOG_ERROR_TYPE, etc.
        DWORD dwID,        // Event ID
        const char* pszS1, // String 1
        const char* pszS2 = NULL,
        const char* pszS3 = NULL
    );
};
```

##### Virtual Methods (Override em CInitSrv)

```cpp
// Callbacks do ciclo de vida
virtual void OnInit();        // Inicialização
virtual void OnStop();        // Parada
virtual void OnPause();       // Pausar
virtual void OnContinue();    // Retomar
virtual void OnShutdown();    // Shutdown
virtual void OnInterrogate(DWORD& CurrentStatus);
virtual void OnUserControl(DWORD dwOpcode);
```

##### Static Callbacks (Windows Service)

```cpp
// Entry point do serviço
static void WINAPI ServiceMain(
    DWORD dwArgc,
    LPTSTR* lpszArgv
);

// Handler de controle
static void WINAPI Handler(DWORD dwOpcode);

// Handler de console (debug)
static BOOL WINAPI handler_console_routine(
    DWORD dwCtrlType
);
```

#### Data Members

```cpp
protected:
    char m_szServiceName[64];      // Nome do serviço
    char m_szDependencies[254];    // Dependências
    int  m_iMajorVersion;          // Versão major
    int  m_iMinorVersion;          // Versão minor

    SERVICE_STATUS_HANDLE m_hServiceStatus;  // Handle SCM
    SERVICE_STATUS        m_Status;          // Status atual

    BOOL m_bIsRunning;      // Serviço rodando
    BOOL m_bIsDebuging;     // Modo debug
    BOOL m_bIsShutDownNow;  // Shutdown imediato

    HANDLE m_hEventSource;  // Event logging
```

---

### CInitSrv (Service Implementation)

**Arquivo:** [InitSrv.h](InitSrv.h), [InitSrv.cpp](InitSrv.cpp)

#### Responsabilidades

- Implementar callbacks do CNTService
- Carregar configuração (INI + Registry)
- Criar e inicializar CMainSrv
- Gerenciar email notifications

#### Override Methods

```cpp
class CInitSrv : public CNTService
{
public:
    CInitSrv();
    virtual ~CInitSrv();

    // Lifecycle overrides
    virtual void OnInit();     // Carrega config, cria CMainSrv
    virtual void OnStop();     // Para threads, limpa recursos
    virtual void OnShutdown(); // Shutdown rápido

    // Configuration
    void GetKeyAll();  // Parse INI file
    void SetKeyAll();  // Apply settings

    // Registry operations
    void GetKeyRegistryValue(LPCTSTR lpKey, CString& csValue);
    void SetKeyRegistryValue(LPCTSTR lpKey, LPCTSTR lpValue);

    // Utility
    void WriteReg(
        const char* prefixo,
        BOOL bWriteTimeStamp,
        int buflen,
        char* buffer
    );
};
```

#### Configuration Members

```cpp
public:
    // Paths
    CString m_DirTraces;      // Diretório de traces
    CString m_DirAudFile;     // Diretório de audit
    CString m_PrivateKeyFile; // Chave privada

    // Database
    CString m_DBAliasName;    // ODBC DSN
    CString m_DBServer;       // Servidor SQL
    CString m_DBName;         // Database name
    CString m_DbTbControle;   // Tabela de controle
    CString m_DbTbStrLog;     // Tabela de log
    CString m_DbTbBacenCidadeApp;  // Tabela app Bacen→Cidade
    CString m_DbTbCidadeBacenApp;  // Tabela app Cidade→Bacen

    // MQSeries
    CString m_MQServer;       // MQ Server hostname
    CString m_QueueManager;   // Queue Manager name
    CString m_QLBacenCidadeReq/Rsp/Rep/Sup;  // Local queues
    CString m_QRCidadeBacenReq/Rsp/Rep/Sup;  // Remote queues
    int     m_QueueTimeout;   // Timeout (segundos)

    // Service
    CString m_szServiceName;  // Nome do serviço
    int     m_MonitorPort;    // Porta TCP do monitor
    int     m_Trace;          // Nível de trace
    int     m_SrvTimeout;     // Timeout do serviço
    int     m_MaxLenMsg;      // Tamanho máximo da mensagem

    // Email
    CString m_ServerEmail;    // SMTP server
    CString m_SenderEmail;    // From address
    CString m_DestEmail;      // To address
    CString m_CCEmail[5];     // CC addresses

    // Security
    char    m_UnicodeEnable;  // 'Y'/'N' - Unicode
    char    m_SecurityEnable; // 'Y'/'N' - Crypto
    CString m_SecurityDB;     // Cert database
    CString m_PublicKeyLabel; // Public key ID
    CString m_PrivateKeyLabel;// Private key ID
    CString m_KeyPassword;    // Key password
```

---

## 5. Monitor TCP/IP

### CMonitor Class

**Arquivo:** [Monitor.h](Monitor.h), [Monitor.cpp](Monitor.cpp)

#### Responsabilidades

- Servidor TCP/IP para administração e monitoramento
- Aceitar até 50 conexões simultâneas
- Processar comandos de clientes
- Timeout de conexões idle
- Interface para CMainSrv

#### Thread Model

```cpp
class CMonitor
{
public:
    // Threading
    std::unique_ptr<std::thread> m_thread;
    std::thread::id              m_threadId;
    std::atomic<bool>            isBusy;

    // Entry points
    static DWORD WINAPI TaskMonitor(LPVOID MainSrv);  // Static
    void RunMonitor(LPVOID MainSrv);                  // Instance

    // Event handling
    HANDLE m_hEvent[55];  // 55 events total
    /*
     * [0] = TIMER       - Timer periódico
     * [1] = TCP         - Socket event
     * [2] = STOP        - Shutdown
     * [3] = MST         - Multi-server timeout
     * [4] = QUEUE       - Queue processing
     * [5-54] = CLITCP   - 50 client sockets
     */
};
```

#### Socket Management

```cpp
private:
    // Server socket
    SOCKET     SrvSock;              // Listening socket
    SOCKADDR_IN SrvAddrTcp;          // Server address
    char       szSrvPorta[10];       // Port (string)
    char       szSrvHumano[30];      // Human-readable IP

    // Client sockets
    SOCKET     CliSock[50];          // 50 client sockets
    int        iqtdsock;             // Socket count
    int        indexCli;             // Current client index

    // Winsock events
    WSANETWORKEVENTS m_TcpEvents;
```

#### Key Methods

```cpp
public:
    CMonitor();
    ~CMonitor();

private:
    // Lifecycle
    void InitSrvSocket();            // Inicializar server socket

    // Connection management
    void AceitaConexao(int ErrorCode);          // Accept new client
    void RecebeDadosCli(int ErrorCode, int CurrCli);  // Receive data
    bool SendDadosCli(CClientItem* pCurrCLI);   // Send response
    void ForceCloseCli(CClientItem* CurrCLI);   // Force disconnect
    void CheckTimeout();                         // Check idle clients

    // Message processing
    void ProcessaQueue();                        // Process queue
    void ProcessaDadosCli(CClientItem* pCurrCLI); // Process client data
```

#### Data Buffers

```cpp
private:
    // Input buffer
    char    dadosin[8192];  // Receive buffer
    int     qtdRecNow;      // Bytes received
    int     totArec;        // Total to receive
    int     totJarec;       // Already received
    int     faltaArec;      // Remaining

    // Message buffers
    LPMIMSG pMsgRec;        // Received message
    LPMIMSG pMsgSend;       // Send message
    int     TamSend;        // Send size
```

#### Main Loop (RunMonitor)

```cpp
void CMonitor::RunMonitor(LPVOID MainSrv)
{
    auto* pMainSrv = static_cast<CMainSrv*>(MainSrv);
    this->pMainSrv = pMainSrv;

    // Inicializar servidor
    InitSrvSocket();

    // Main event loop
    while (true)
    {
        DWORD dwWait = WaitForMultipleObjects(
            QTD_MONI_EVENTS,  // 55 events
            m_hEvent,
            FALSE,            // Wait any
            INFINITE
        );

        switch (dwWait)
        {
            case MONI_EVENT_TIMER:
                // Timer tick - check timeouts
                CheckTimeout();
                break;

            case MONI_EVENT_TCP:
                // Server socket event - accept connection
                AceitaConexao(m_TcpEvents.iErrorCode[FD_ACCEPT_BIT]);
                break;

            case MONI_EVENT_STOP:
                // Shutdown
                return;

            case MONI_EVENT_QUEUE:
                // Process queue
                ProcessaQueue();
                break;

            default:
                // Client socket event (CLITCP[0-49])
                if (dwWait >= EVENT_CLITCP &&
                    dwWait < EVENT_CLITCP + 50)
                {
                    int indexCli = dwWait - EVENT_CLITCP;
                    RecebeDadosCli(
                        m_TcpEvents.iErrorCode[FD_READ_BIT],
                        indexCli
                    );
                }
                break;
        }
    }
}
```

---

## 6. Threads de Processamento MQ

### CThreadMQ (Base Class)

**Arquivo:** [ThreadMQ.h](ThreadMQ.h), [ThreadMQ.cpp](ThreadMQ.cpp)

#### Responsabilidades

- Classe base abstrata para threads de processamento
- Interface com IBM MQ Series
- Processamento de XML (MSXML)
- Operações criptográficas
- Conversão ANSI/Unicode
- Sincronização de thread

#### Constructor

```cpp
CThreadMQ::CThreadMQ(
    LPCTSTR lpszName,        // Nome da thread
    bool AutomaticThread,    // Auto-start ou manual
    int HandleMQ,            // MQ handle (TASK_BACEN_REQ, etc.)
    CMainSrv *MainSrv        // Ponteiro para serviço principal
)
{
    m_ServiceName = lpszName;
    m_AutomaticThread = AutomaticThread;
    m_HandleMQ = HandleMQ;
    pMainSrv = MainSrv;

    // Inicializar flags atômicas
    m_ServicoIsRunning.store(false);
    m_ThreadIsRunning.store(false);

    // Criar eventos
    m_hEvent[ThreadEvent::TIMER] = CreateWaitableTimer(...);
    m_hEvent[ThreadEvent::STOP] = CreateEvent(...);
    m_hEvent[ThreadEvent::POST] = CreateEvent(...);
}
```

#### Threading Model

```cpp
class CThreadMQ : public CObject
{
public:
    // Threading members
    std::unique_ptr<std::thread> m_thread;
    std::thread::id              m_threadId;
    DWORD                        m_dwThreadId;  // Compat
    std::atomic<bool>            m_ServicoIsRunning;
    std::atomic<bool>            m_ThreadIsRunning;
    std::mutex                   m_mutex;

    // Event synchronization
    HANDLE m_hEvent[3];  // TIMER, STOP, POST

    // Entry points
    static DWORD WINAPI TaskThread(LPVOID MainSrv);
    virtual void RunThread(LPVOID MainSrv);

    // Lifecycle virtuals
    virtual void RunInit();       // Inicialização
    virtual void RunWait();       // Loop principal
    virtual void RunWaitPost();   // Aguardar POST
    virtual void RunTerm();       // Finalização

    // Message processing
    virtual void ProcessaQueue(); // Processar mensagem
};
```

#### MQ Series Interface

```cpp
protected:
    // Connection
    MQHCONN m_Hcon;         // Connection handle
    MQHOBJ  m_Hobj;         // Object handle
    char    m_QMName[50];   // Queue manager name

    // Descriptors
    MQOD    m_od;           // Object descriptor
    MQMD    m_md;           // Message descriptor
    MQGMO   m_gmo;          // Get message options
    MQPMO   m_pmo;          // Put message options

    // Status
    MQLONG  m_CompCode;     // Completion code
    MQLONG  m_Reason;       // Reason code

    // Message buffer
    BYTE*   m_buffermsg;    // Buffer
    MQLONG  m_buflen;       // Buffer length
```

#### XML Processing

```cpp
public:
    // MSXML members
    MSXML::IXMLDOMDocument* m_pDomDoc;
    MSXML::IXMLDOMNode*     m_pDomNode;
    HRESULT                 m_hr;

    // XML operations
    HRESULT LoadDocumentSync(
        MSXML::IXMLDOMDocument* pDoc,
        BSTR pData,
        ULONG ulLen
    );

    HRESULT SaveDocument(
        MSXML::IXMLDOMDocument* pDoc,
        BSTR pBFName
    );

    HRESULT FindTag(
        MSXML::IXMLDOMDocument* pDoc,
        BSTR pwParent,  // Parent node name
        BSTR pwText,    // Tag to find
        BSTR* pwValue   // Output value
    );

    HRESULT SetTag(
        MSXML::IXMLDOMDocument* pDoc,
        BSTR pwText,    // Tag name
        BSTR* pwValue   // Value to set
    );

    HRESULT WalkTree(
        MSXML::IXMLDOMNode* node,
        int level
    );

    HRESULT ReportError(
        MSXML::IXMLDOMParseError* pXMLError
    );
```

#### Cryptographic Operations

```cpp
public:
    // Crypto contexts
    CRYPT_KEYSET  m_cryptKeyset;
    CRYPT_CONTEXT m_cryptPublicContext;
    CRYPT_CONTEXT m_cryptPrivateContext;
    CRYPT_CONTEXT m_crypthashContext;
    CRYPT_CONTEXT m_cryptContext;
    int           m_cryptstatus;

    BYTE m_cryptSerialNumberPrv[32];
    BYTE m_cryptSerialNumberPub[32];

    // Key management
    int ReadPublicKey();
    int ReadPrivatKey();

    // Operations
    int funcAssinar(        // Sign
        LPSECHDR lpSecHeader,
        int& lentmp,
        LPBYTE msg
    );

    int funcVerifyAss(      // Verify signature
        LPSECHDR lpSecHeader,
        int& lentmp,
        LPBYTE msg
    );

    int funcCript(          // Encrypt
        LPSECHDR lpSecHeader,
        int& lentmp,
        LPBYTE msg
    );

    int funcDeCript(        // Decrypt
        LPSECHDR lpSecHeader,
        int& lentmp,
        LPBYTE msg
    );

    int funcLog(            // Logging
        LPSECHDR lpSecHeader,
        int& lentmp,
        LPBYTE msg
    );

    int funcStrLog(         // Structured logging
        LPSECHDR lpSecHeader,
        int& lentmp,
        LPBYTE msg
    );
```

#### Data Encoding

```cpp
public:
    // ANSI ↔ Unicode conversion
    bool AnsiToUnicode(int& lenmsg, LPBYTE msg);
    bool UnicodeToAnsi(int& lenmsg, LPBYTE msg);
    bool UnicodeToAnsi(BSTR psz, LPSTR& pstr);
```

#### Main Loop (RunThread)

```cpp
void CThreadMQ::RunThread(LPVOID MainSrv)
{
    auto* pMainSrv = static_cast<CMainSrv*>(MainSrv);

    // Inicialização
    RunInit();
    m_ServicoIsRunning.store(true);

    // Main event loop
    while (m_ServicoIsRunning.load())
    {
        RunWait();  // Aguardar evento

        // Processar evento
        // (implementado em cada subclasse)
    }

    // Finalização
    RunTerm();
    m_ThreadIsRunning.store(false);
}
```

---

### CBacenReq (Bacen Request Processor)

**Arquivo:** [BacenReq.h](BacenReq.h), [BacenREQ.cpp](BacenREQ.cpp)

#### Propósito

Processar mensagens de **requisição** vindas da rede **Bacen** (Banco Central).

#### Fluxo de Processamento

```
1. MQGet() - Ler mensagem da fila Bacen Request
2. CheckAssDeCryptBufferMQ() - Validar assinatura e decriptar
3. ChecarXml() - Validar XML contra DTD
4. Parse XML - Extrair campos (NU_OPE, COD_MSG, etc.)
5. UpdateDB() - Persistir em SQL Server
   ├─ MontaDbRegApp() → CBacenAppRS
   ├─ MontaDbRegLog() → CSTRLogRS
   └─ AtualizaCtr() → CControleRS
6. Routing - Determinar ação
   ├─ Echo? → GeraEcoR1() → Enfileira resposta
   ├─ Log? → GeraLogR1() → Enfileira resposta
   ├─ UltMsg? → GeraUltMsgR1() → Enfileira resposta
   └─ Normal? → Enfileira para CIFReq
```

#### Key Methods

```cpp
class CBacenReq : public CThreadMQ
{
public:
    CBacenReq(LPCTSTR lpszName, bool AutomaticThread,
              int HandleMQ, CMainSrv* MainSrv);
    ~CBacenReq();

    // Overrides
    virtual void ProcessaQueue();  // Main message handler

private:
    // Validation
    int CheckAssDeCryptBufferMQ();
    int ChecarXml();

    // Database operations
    int UpdateDB();
    int MontaDbRegApp();
    int MontaDbRegLog();
    int AtualizaCtr();
    int ReadCtr();

    // Message type handlers
    int FuncEco();      // Echo operation
    int FuncLog();      // Log operation
    int FuncUltMsg();   // Last message operation

    // Response generators
    int GeraEcoR1();    // Generate Echo R1 XML
    int GeraLogR1();    // Generate Log R1 XML
    int GeraUltMsgR1(); // Generate UltMsg R1 XML
    int GeraReport();   // Generate report

    // Utilities
    void DumpHeader(MQMD* InQmd);
};
```

#### Database References

```cpp
protected:
    // Multiple DB connections (up to 4)
    CBCDatabase* m_pDb1;
    CBCDatabase* m_pDb2;
    CBCDatabase* m_pDb3;
    CBCDatabase* m_pDb4;

    // Recordsets
    CBacenAppRS* m_pRS;      // Main application data
    CSTRLogRS*   m_pRSLog;   // Structured logs
    CControleRS* m_pRSCtr;   // Control/status
    CIFAppRS*    m_pRSApp;   // IF app data (for routing)
```

#### Message Metadata

```cpp
protected:
    CString m_NuOpe;              // Operation number
    CString m_CodMsg;             // Message code
    CString m_TipoIdEmissor;      // Sender ID type
    CString m_IdEmissor;          // Sender ID
    CString m_TipoIdDestinatario; // Receiver ID type
    CString m_IdDestinatario;     // Receiver ID
    CString m_StatusMsg;          // Message status
    SYSTEMTIME m_t;               // Timestamp
```

---

### CBacenRsp (Bacen Response Processor)

**Arquivo:** [BacenRsp.h](BacenRsp.h), [BacenRSP.cpp](BacenRSP.cpp)

#### Propósito

Processar **respostas** enviadas para a rede **Bacen**.

#### Diferenças em relação ao CBacenReq

- Lida com mensagens de **resposta** (R1, R2, etc.)
- Gera respostas para Echo, Log, UltMsg
- Trata erros (FuncErro)
- Mantém correlação com mensagens originais

#### Key Methods Específicos

```cpp
class CBacenRsp : public CThreadMQ
{
public:
    // Response generators
    int FuncEcoR1();    // Echo R1 response
    int FuncLogR1();    // Log R1 response
    int FuncUltMsgR1(); // UltMsg R1 response
    int FuncErro();     // Error handling

protected:
    CString m_CodMsgOr;  // Original message code
};
```

---

### CBacenRep / CBacenSup (Replication & Support)

**Arquivo:** [BacenRep.h](BacenRep.h), [BacenRep.cpp](BacenRep.cpp), [BacenSup.h](BacenSup.h), [BacenSup.cpp](BacenSup.cpp)

#### Propósito

- **CBacenRep:** Mensagens de **replicação** Bacen
- **CBacenSup:** Mensagens **suplementares/suporte** Bacen

Operações simplificadas em relação ao Req/Rsp:
- Menos validações criptográficas
- Foco em persistência
- Sem geração de respostas complexas

---

### CIFReq (Interface Request Sender)

**Arquivo:** [IFReq.h](IFReq.h), [IFREQ.cpp](IFREQ.cpp)

#### Propósito

Enviar mensagens de **requisição** para a rede **Interface/Cidade**.

#### Fluxo

```
1. Ler registro de CIFAppRS (mensagem pendente)
2. MontaBufferMQ() - Montar buffer MQ
3. ChecarXml() - Validar XML
4. Criptografia/assinatura (se habilitado)
5. MQPut() - Enviar para fila
6. UpdateMQeDB() - Atualizar DB com ID MQ
   ├─ UpdateDbRegApp()
   └─ MontaDbRegLog()
```

#### Key Methods

```cpp
class CIFReq : public CThreadMQ
{
public:
    virtual void ProcessaQueue();

private:
    int UpdateMQeDB(CIFAppRS* pRS);
    int UpdateDbRegApp();
    int MontaDbRegLog();
    int MontaBufferMQ();
    int ChecarXml();

    void RunInitDBeMQ();  // Initialize DB & MQ
    void RunTermDBeMQ();  // Terminate DB & MQ

protected:
    CBCDatabase* m_pDb1;
    CBCDatabase* m_pDb2;
    CIFAppRS*    m_pRS;
    CSTRLogRS*   m_pRSLog;
    SYSTEMTIME   m_t;
};
```

---

### CIFRsp / CIFRep / CIFSup

**Arquivo:** [IFRsp.h](IFRsp.h), [IFRSP.cpp](IFRSP.cpp), [IFRep.h](IFRep.h), [IFREP.cpp](IFREP.cpp), [IFSup.h](IFSup.h), [IFSUP.cpp](IFSUP.cpp)

Similaridades com CIFReq, mas:
- **CIFRsp:** Processar respostas vindas de Interface
- **CIFRep:** Replicação para Interface
- **CIFSup:** Suporte/suplementar para Interface

---

## 7. Classes de Banco de Dados

### CBacenAppRS (Bacen Application Recordset)

**Arquivo:** [BacenAppRS.h](BacenAppRS.h), [BacenAppRS.cpp](BacenAppRS.cpp)

#### Propósito

Representar registros da tabela de aplicação Bacen→Cidade.

#### Schema (Campos RFX)

```cpp
class CBacenAppRS : public CRecordset
{
public:
    // Key fields
    CByteArray  m_MQ_MSG_ID;      // Message ID (24 bytes)
    CByteArray  m_MQ_CORREL_ID;   // Correlation ID (24 bytes)

    // Timestamps
    TIMESTAMP_STRUCT m_DB_DATETIME;  // Database timestamp
    TIMESTAMP_STRUCT m_MQ_DATETIME;  // MQ timestamp

    // Status
    CString m_STATUS_MSG;         // Message status
    CString m_FLAG_PROC;          // Processing flag

    // Routing
    CString m_MQ_QN_ORIGEM;       // Origin queue name

    // Headers
    CByteArray m_MQ_HEADER;       // MQ header binary
    CByteArray m_SECURITY_HEADER; // Security header binary

    // Application data
    CString m_NU_OPE;             // Operation number
    CString m_COD_MSG;            // Message code
    CString m_MSG;                // Message body (XML)

    // Query parameters
    CString    m_ParamNU_OPE;
    CByteArray m_ParamMQ_MSG_ID;

    // DDL
    CString m_sDrop;              // DROP TABLE statement
    CString m_sCreate;            // CREATE TABLE statement
    CString m_sPriKey;            // Primary key DDL
    CString m_sIndex1, m_sIndex2; // Indices DDL

    // Connection info
    CString m_sDbName;
    CString m_sMQServer;
    int     m_iPorta;
    int     m_iMaxLenMsg;

    // Overrides
    virtual CString GetDefaultConnect();
    virtual CString GetDefaultSQL();
    virtual void DoFieldExchange(CFieldExchange* pFX);
};
```

#### DoFieldExchange (RFX Binding)

```cpp
void CBacenAppRS::DoFieldExchange(CFieldExchange* pFX)
{
    pFX->SetFieldType(CFieldExchange::outputColumn);

    // Binary fields
    RFX_Binary(pFX, _T("MQ_MSG_ID"), m_MQ_MSG_ID);
    RFX_Binary(pFX, _T("MQ_CORREL_ID"), m_MQ_CORREL_ID);

    // Timestamps
    RFX_Date(pFX, _T("DB_DATETIME"), m_DB_DATETIME);
    RFX_Date(pFX, _T("MQ_DATETIME"), m_MQ_DATETIME);

    // String fields
    RFX_Text(pFX, _T("STATUS_MSG"), m_STATUS_MSG);
    RFX_Text(pFX, _T("FLAG_PROC"), m_FLAG_PROC);
    RFX_Text(pFX, _T("MQ_QN_ORIGEM"), m_MQ_QN_ORIGEM);

    // Headers
    RFX_Binary(pFX, _T("MQ_HEADER"), m_MQ_HEADER);
    RFX_Binary(pFX, _T("SECURITY_HEADER"), m_SECURITY_HEADER);

    // Application data
    RFX_Text(pFX, _T("NU_OPE"), m_NU_OPE);
    RFX_Text(pFX, _T("COD_MSG"), m_COD_MSG);
    RFX_LongBinary(pFX, _T("MSG"), m_MSG);
}
```

---

### CIFAppRS (Interface Application Recordset)

**Arquivo:** [IFAppRS.h](IFAppRS.h), [IFAppRS.cpp](IFAppRS.cpp)

#### Propósito

Representar registros da tabela de aplicação Interface→Bacen.

#### Campos Adicionais (além dos de CBacenAppRS)

```cpp
class CIFAppRS : public CRecordset
{
public:
    // Routing
    CString m_MQ_QN_DESTINO;      // Destination queue

    // Tracking (multiple message IDs for lifecycle)
    TIMESTAMP_STRUCT m_MQ_DATETIME_PUT;  // PUT timestamp

    CByteArray m_MQ_MSG_ID_COA;          // COA message ID
    TIMESTAMP_STRUCT m_MQ_DATETIME_COA;  // COA timestamp

    CByteArray m_MQ_MSG_ID_COD;          // COD message ID
    TIMESTAMP_STRUCT m_MQ_DATETIME_COD;  // COD timestamp

    CByteArray m_MQ_MSG_ID_REP;          // REP message ID
    TIMESTAMP_STRUCT m_MQ_DATETIME_REP;  // REP timestamp

    int m_MSG_LEN;                       // Message length

    // DDL
    CString m_sIndex3;
    CString m_sTrigger;                  // Trigger DDL
};
```

---

### CControleRS (Control/Status Recordset)

**Arquivo:** [ControleRS.h](ControleRS.h), [ControleRS.cpp](ControleRS.cpp)

#### Propósito

Tabela de controle de status por participante ISPB.

#### Schema

```cpp
class CControleRS : public CRecordset
{
public:
    // Primary key
    CString m_ISPB;                // Participant ISPB code

    // Participant info
    CString m_NOME_ISPB;           // Participant name

    // Status tracking
    CString m_STATUS_GERAL;        // Overall status

    // Last echo
    TIMESTAMP_STRUCT m_DTHR_ECO;   // Last echo timestamp

    // Last message
    CString m_ULTMSG;              // Last message code
    TIMESTAMP_STRUCT m_DTHR_ULTMSG;// Last message timestamp

    // Certificate
    CString m_CERTIFICADORA;       // Certificate authority

    // Concurrency control
    BOOL m_islock;                 // Record lock flag

    // Query parameter
    CString m_ParamISPB;

    // Concurrency methods
    BOOL Lock();
    BOOL Unlock();
    BOOL IsLock();
};
```

---

### CSTRLogRS (Structured Log Recordset)

**Arquivo:** [STRLogRS.h](STRLogRS.h), [STRLogRS.cpp](STRLogRS.cpp)

#### Propósito

Tabela de log estruturado (auditoria completa de mensagens).

#### Schema

Similar ao CBacenAppRS, mas foco em logging:

```cpp
class CSTRLogRS : public CRecordset
{
public:
    CByteArray m_MQ_MSG_ID;
    CByteArray m_MQ_CORREL_ID;
    TIMESTAMP_STRUCT m_DB_DATETIME;
    CString m_STATUS_MSG;
    CString m_MQ_QN_ORIGEM;
    TIMESTAMP_STRUCT m_MQ_DATETIME;
    CByteArray m_MQ_HEADER;
    CByteArray m_SECURITY_HEADER;
    CString m_NU_OPE;
    CString m_COD_MSG;
    CString m_MSG;

    // Parameters
    CByteArray m_ParamMQ_MSG_ID;
    CString m_ParamNU_OPE;

    // DDL
    CString m_sDrop;
    CString m_sCreate;
    CString m_sPriKey;
    CString m_sIndex1;
    CString m_sDbName;
    CString m_sMQServer;
    int m_iPorta;
    int m_iMaxLenMsg;
};
```

---

### CBCDatabase (Database Wrapper)

**Arquivo:** [CBCDb.h](CBCDb.h)

#### Propósito

Wrapper simples sobre CDatabase com info de conexão.

```cpp
class CBCDatabase : public CDatabase
{
public:
    CString m_sDbName;
    CString m_sMQServer;
    int     m_iPorta;
    int     m_iMaxLenMsg;

    // Enable transactions
    void SetTransactions();
};
```

---

## 8. Gerenciamento de Clientes

### CClientItem

**Arquivo:** [MainSrv.h](MainSrv.h), [MainSrv.cpp](MainSrv.cpp)

#### Propósito

Representar metadados de uma conexão TCP de cliente.

#### Data Members

```cpp
class CClientItem : public CObject
{
public:
    // Synchronization
    std::mutex m_mutex;

    // Connection info
    SOCKET      m_Sock;          // Socket handle
    SOCKADDR_IN m_AddrCli;       // Address structure
    char        m_CliHumano[30]; // Human-readable IP
    char        m_szPorta[10];   // Port (string)
    CString     m_ComputerName;  // Computer name
    CString     m_UseridName;    // User ID

    // State
    int  m_status;               // ST_CLI_CONNECT, etc.
    bool m_IsActive;             // Is active
    bool m_ForceCli;             // Force active flag
    int  m_index;                // Socket array index
    int  m_timeout;              // Timeout (seconds)

    // Data buffers
    std::unique_ptr<BYTE[]> dadosin;   // Input buffer
    std::unique_ptr<BYTE[]> dadosout;  // Output buffer
    int tamdadosin;
    int tamdadosout;

    // Methods
    CClientItem(char* CliHumano, char* szPorta);
    ~CClientItem();
    BOOL Lock();
    BOOL Unlock();
};
```

---

### CQueueList

**Arquivo:** [MainSrv.h](MainSrv.h), [MainSrv.cpp](MainSrv.cpp)

#### Propósito

Container thread-safe para coleções de objetos (principalmente CClientItem).

#### Data Members

```cpp
class CQueueList : public CObject
{
public:
    CString m_lpszName;          // Collection name
    BOOL    m_bIsTrueList;       // True list vs queue
    int     m_iMaxList;          // Max items seen

protected:
    std::mutex             m_mutex;      // Thread safety
    std::vector<CObject*>  m_QueueList;  // Storage
};
```

#### Methods

```cpp
public:
    CQueueList();
    CQueueList(LPCTSTR NameLock, BOOL bIsTrueList);
    ~CQueueList();

    // Basic operations
    int Add(CObject* obj);               // Add item, return index
    void RemoveAt(int nIndex, int nCount = 1);
    void RemoveAll();
    int GetSize();
    int GetMaxSize();
    CObject* GetAt(int position);
    CObject* GetFirst();

    // Client-specific searches
    CClientItem* LocateSock(SOCKET sock);
    CClientItem* RemoveSock(SOCKET sock);
    CClientItem* LocateSockAddr(char* sockaddr);
    void DepuraSockAddr(CMainSrv* pMainSrv, char* m_szTaskName);
    CClientItem* LocateCliOrigin(BYTE* OriginId);
    void InactiveProcessoId(CClientItem* pCurrCli);
```

#### Implementation Examples

```cpp
// Add with thread safety
int CQueueList::Add(CObject* obj)
{
    std::lock_guard<std::mutex> lock(m_mutex);

    m_QueueList.push_back(obj);
    int rt = static_cast<int>(m_QueueList.size()) - 1;
    int ct = static_cast<int>(m_QueueList.size());

    if (ct > m_iMaxList)
        m_iMaxList = ct;

    return rt;  // Automatic unlock
}

// Search with range-based for loop
CClientItem* CQueueList::LocateSock(SOCKET sock)
{
    std::lock_guard<std::mutex> lock(m_mutex);

    for (auto* obj : m_QueueList)
    {
        auto* pCli = static_cast<CClientItem*>(obj);
        if (pCli->m_Sock == sock)
        {
            pCli->Lock();
            pCli->Unlock();
            return pCli;
        }
    }

    return nullptr;
}

// Remove with std::find_if
CClientItem* CQueueList::RemoveSock(SOCKET sock)
{
    std::lock_guard<std::mutex> lock(m_mutex);

    auto it = std::find_if(m_QueueList.begin(), m_QueueList.end(),
        [sock](CObject* obj) {
            auto* pCli = static_cast<CClientItem*>(obj);
            return pCli->m_Sock == sock;
        });

    if (it != m_QueueList.end())
    {
        auto* pCli = static_cast<CClientItem*>(*it);
        pCli->Lock();
        m_QueueList.erase(it);
        pCli->Unlock();
        return pCli;
    }

    return nullptr;
}
```

---

## 9. Modelo de Threading

### Thread Structure

```
Main Process (BCSrvSqlMq.exe)
│
├─ Main Thread
│  └─ CInitSrv::Run()
│     └─ WaitMultipleObjects(m_hEvent[7], ...)
│
├─ Monitor Thread
│  └─ CMonitor::RunMonitor()
│     ├─ std::unique_ptr<std::thread>
│     ├─ 55 events (TIMER, TCP, STOP, MST, QUEUE, 50xCLITCP)
│     └─ 50 simultaneous TCP clients
│
└─ 8 Message Queue Threads
   ├─ CBacenReq::RunThread()
   ├─ CBacenRsp::RunThread()
   ├─ CBacenRep::RunThread()
   ├─ CBacenSup::RunThread()
   ├─ CIFReq::RunThread()
   ├─ CIFRsp::RunThread()
   ├─ CIFRep::RunThread()
   └─ CIFSup::RunThread()
      └─ Each with 3 events (TIMER, STOP, POST)
```

### Event Signaling

#### CMainSrv Events

```cpp
HANDLE m_hEvent[QTD_EVENTS_FIXED];  // 7 events

// Indices (namespace MainEvent)
constexpr int TIMER = 0;            // Timer tick
constexpr int ACABOU = 1;           // Completion
constexpr int STOP = 2;             // Stop signal
constexpr int PAUSE = 3;            // Pause
constexpr int CONTINUE = 4;         // Continue
constexpr int MONITOR_STOP = 5;     // Monitor stop
constexpr int TASKSAPP_STOP = 6;    // Tasks stop
```

#### CThreadMQ Events

```cpp
HANDLE m_hEvent[QTD_THREAD_EVENTS];  // 3 events

// Indices (namespace ThreadEvent)
constexpr int TIMER = 0;   // Thread timer
constexpr int STOP = 1;    // Thread stop
constexpr int POST = 2;    // Posted message
```

#### CMonitor Events

```cpp
HANDLE m_hEvent[QTD_MONI_EVENTS];  // 55 events

// Indices (namespace MonitorEvent)
constexpr int TIMER = 0;   // Monitor timer
constexpr int TCP = 1;     // TCP socket
constexpr int STOP = 2;    // Monitor stop
constexpr int MST = 3;     // Multi-server timeout
constexpr int QUEUE = 4;   // Queue processing
// EVENT_CLITCP = 5-54 (50 client sockets)
```

### Synchronization Primitives

#### Atomic Flags (lock-free)

```cpp
// In CThreadMQ
std::atomic<bool> m_ServicoIsRunning;
std::atomic<bool> m_ThreadIsRunning;

// In CMonitor
std::atomic<bool> isBusy;

// Usage
m_ServicoIsRunning.store(true, std::memory_order_relaxed);
if (m_ThreadIsRunning.load(std::memory_order_relaxed)) {
    // ...
}
```

#### Mutexes (RAII)

```cpp
// In CThreadMQ, CClientItem, CQueueList
std::mutex m_mutex;

// Usage with RAII
void SomeMethod()
{
    std::lock_guard<std::mutex> lock(m_mutex);
    // Critical section
    // Automatic unlock when lock goes out of scope
}
```

---

## 10. Fluxo de Dados

### Message Flow (Bacen → Interface)

```
┌──────────────────┐
│  Bacen Network   │
│  (Central Bank)  │
└────────┬─────────┘
         │
         │ MQ Queue: QLBacenCidadeReq
         ↓
┌─────────────────────────────────────────────┐
│  CBacenReq Thread                           │
│  ┌────────────────────────────────────────┐ │
│  │ 1. MQGet() - Read message              │ │
│  │ 2. Validate signature & decrypt        │ │
│  │ 3. Parse XML (extract fields)          │ │
│  │ 4. Persist to database                 │ │
│  │    ├─ CBacenAppRS (app table)          │ │
│  │    ├─ CSTRLogRS (log table)            │ │
│  │    └─ CControleRS (control table)      │ │
│  │ 5. Determine routing                   │ │
│  │    ├─ Echo? → CBacenRsp (response)     │ │
│  │    ├─ Log? → CBacenRsp (response)      │ │
│  │    └─ Normal → CIFReq (forward)        │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
         │
         │ Route to Interface
         ↓
┌─────────────────────────────────────────────┐
│  CIFReq Thread                              │
│  ┌────────────────────────────────────────┐ │
│  │ 1. Read CIFAppRS (pending message)     │ │
│  │ 2. Build MQ buffer                     │ │
│  │ 3. Sign & encrypt (if enabled)         │ │
│  │ 4. MQPut() - Send to IF queue          │ │
│  │ 5. Update DB with MQ IDs               │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
         │
         │ MQ Queue: QRCidadeBacenReq
         ↓
┌──────────────────┐
│  Interface Net   │
│  (Cidade System) │
└──────────────────┘
```

### Response Flow (Interface → Bacen)

```
┌──────────────────┐
│  Interface Net   │
└────────┬─────────┘
         │
         │ MQ Queue: QLCidadeBacenRsp
         ↓
┌─────────────────────────────────────────────┐
│  CIFRsp Thread                              │
│  ┌────────────────────────────────────────┐ │
│  │ 1. MQGet() - Read response             │ │
│  │ 2. Validate & decrypt                  │ │
│  │ 3. Parse XML                           │ │
│  │ 4. Update DB (correlation ID)          │ │
│  │    ├─ Update CIFAppRS with response    │ │
│  │    ├─ Log to CSTRLogRS                 │ │
│  │    └─ Update CControleRS status        │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
         │
         │ If response needs forwarding
         ↓
┌─────────────────────────────────────────────┐
│  CBacenRsp Thread                           │
│  ┌────────────────────────────────────────┐ │
│  │ 1. Build response message              │ │
│  │ 2. Sign & encrypt                      │ │
│  │ 3. MQPut() to Bacen response queue     │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
         │
         │ MQ Queue: QRBacenCidadeRsp
         ↓
┌──────────────────┐
│  Bacen Network   │
└──────────────────┘
```

### TCP Client Flow

```
┌──────────────┐
│ TCP Client   │ (Admin/Monitoring application)
└──────┬───────┘
       │
       │ TCP Connect: port 8080
       ↓
┌────────────────────────────────────────┐
│  CMonitor::AceitaConexao()             │
│  ┌──────────────────────────────────┐  │
│  │ 1. accept() new connection       │  │
│  │ 2. Create CClientItem            │  │
│  │ 3. Add to m_ClientList           │  │
│  │ 4. Associate with event slot     │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
       │
       │ Client sends command
       ↓
┌────────────────────────────────────────┐
│  CMonitor::RecebeDadosCli()            │
│  ┌──────────────────────────────────┐  │
│  │ 1. recv() data                   │  │
│  │ 2. Accumulate in buffer          │  │
│  │ 3. Check if complete message     │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
       │
       │ Message complete
       ↓
┌────────────────────────────────────────┐
│  CMonitor::ProcessaDadosCli()          │
│  ┌──────────────────────────────────┐  │
│  │ 1. Parse command                 │  │
│  │ 2. Execute operation             │  │
│  │    ├─ Query status               │  │
│  │    ├─ Retrieve logs              │  │
│  │    └─ Admin commands             │  │
│  │ 3. Build response                │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
       │
       │ Send response
       ↓
┌────────────────────────────────────────┐
│  CMonitor::SendDadosCli()              │
│  ┌──────────────────────────────────┐  │
│  │ 1. send() response data          │  │
│  │ 2. Update client status          │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
       │
       ↓
┌──────────────┐
│ TCP Client   │ (receives response)
└──────────────┘
```

---

## 11. Configuração

### INI File Structure

**Arquivo:** BCSrvSqlMq.ini (no mesmo diretório do executável)

```ini
[Diretorios]
DirTraces=C:\Logs\BCSrvSqlMq\Traces
DirAudFile=C:\Logs\BCSrvSqlMq\Audit

[DataBase]
DBAliasName=BCSrvDB
DBServer=localhost
DBName=SPBDB
DbTbControle=TbControle
DbTbStrLog=TbStrLog
DbTbBacenCidadeApp=TbBacenApp
DbTbCidadeBacenApp=TbCidadeApp

[MQSeries]
MQServer=localhost
QueueManager=QM1

# Bacen→Cidade (Incoming from Bacen)
QLBacenCidadeReq=BACEN.CIDADE.REQ
QLBacenCidadeRsp=BACEN.CIDADE.RSP
QLBacenCidadeRep=BACEN.CIDADE.REP
QLBacenCidadeSup=BACEN.CIDADE.SUP

# Cidade→Bacen (Outgoing to Bacen)
QRCidadeBacenReq=CIDADE.BACEN.REQ
QRCidadeBacenRsp=CIDADE.BACEN.RSP
QRCidadeBacenRep=CIDADE.BACEN.REP
QRCidadeBacenSup=CIDADE.BACEN.SUP

QueueTimeout=30

[Servico]
ServiceName=BCSrvSqlMQ
MonitorPort=8080
Trace=1
SrvTimeout=300
MaxLenMsg=1048576

[E-Mail]
ServerEmail=smtp.example.com
SenderEmail=bcsrv@example.com
DestEmail=admin@example.com
CCEmail1=support@example.com
CCEmail2=
CCEmail3=
CCEmail4=
CCEmail5=

[Security]
UnicodeEnable=Y
SecurityEnable=Y
SecurityDB=CertDB
PrivateKeyFile=C:\Keys\private.key
PublicKeyLabel=PubKey_Bacen
PrivateKeyLabel=PrivKey_Cidade
KeyPassword=********
```

### Configuration Loading

```cpp
void CInitSrv::GetKeyAll()
{
    CString csSect, csKey, csVal;

    // [Diretorios]
    csSect = "Diretorios";
    GetPrivateProfileString(csSect, "DirTraces", "",
                           m_DirTraces.GetBuffer(256), 256, m_szIniFile);
    GetPrivateProfileString(csSect, "DirAudFile", "",
                           m_DirAudFile.GetBuffer(256), 256, m_szIniFile);

    // [DataBase]
    csSect = "DataBase";
    GetPrivateProfileString(csSect, "DBAliasName", "",
                           m_DBAliasName.GetBuffer(256), 256, m_szIniFile);
    // ... etc

    // [MQSeries]
    csSect = "MQSeries";
    GetPrivateProfileString(csSect, "MQServer", "",
                           m_MQServer.GetBuffer(256), 256, m_szIniFile);
    // ... etc

    // [Servico]
    m_MonitorPort = GetPrivateProfileInt("Servico", "MonitorPort", 8080, m_szIniFile);
    m_Trace = GetPrivateProfileInt("Servico", "Trace", 1, m_szIniFile);
    // ... etc
}
```

---

## 12. Segurança e Criptografia

### CryptLib Integration

#### Key Management

```cpp
// In CThreadMQ::RunInit()
int CThreadMQ::ReadPublicKey()
{
    // Load public key from file
    m_cryptstatus = cryptKeysetOpen(
        &m_cryptKeyset,
        CRYPT_UNUSED,
        CRYPT_KEYSET_FILE,
        pMainSrv->pInitSrv->m_PublicKeyFile,
        CRYPT_KEYOPT_READONLY
    );

    if (cryptStatusOK(m_cryptstatus))
    {
        m_cryptstatus = cryptGetPublicKey(
            m_cryptKeyset,
            &m_cryptPublicContext,
            CRYPT_KEYID_NAME,
            pMainSrv->pInitSrv->m_PublicKeyLabel
        );
    }

    return m_cryptstatus;
}

int CThreadMQ::ReadPrivatKey()
{
    // Load private key from file
    m_cryptstatus = cryptKeysetOpen(
        &m_cryptKeyset,
        CRYPT_UNUSED,
        CRYPT_KEYSET_FILE,
        pMainSrv->pInitSrv->m_PrivateKeyFile,
        CRYPT_KEYOPT_NONE
    );

    if (cryptStatusOK(m_cryptstatus))
    {
        m_cryptstatus = cryptGetPrivateKey(
            m_cryptKeyset,
            &m_cryptPrivateContext,
            CRYPT_KEYID_NAME,
            pMainSrv->pInitSrv->m_PrivateKeyLabel,
            pMainSrv->pInitSrv->m_KeyPassword
        );
    }

    return m_cryptstatus;
}
```

#### Digital Signature

```cpp
int CThreadMQ::funcAssinar(
    LPSECHDR lpSecHeader,  // Security header
    int& lentmp,           // Message length
    LPBYTE msg             // Message buffer
)
{
    // Create signature context
    cryptCreateContext(&m_crypthashContext, CRYPT_UNUSED, CRYPT_ALGO_SHA1);

    // Hash the message
    cryptEncrypt(m_crypthashContext, msg, lentmp);
    cryptEncrypt(m_crypthashContext, msg, 0);  // Finalize

    // Sign the hash
    cryptCreateSignature(
        lpSecHeader->Assinatura,  // Output signature
        sizeof(lpSecHeader->Assinatura),
        &lpSecHeader->lenAssinatura,
        m_cryptPrivateContext,
        m_crypthashContext
    );

    // Cleanup
    cryptDestroyContext(m_crypthashContext);

    return CRYPT_OK;
}
```

#### Signature Verification

```cpp
int CThreadMQ::funcVerifyAss(
    LPSECHDR lpSecHeader,
    int& lentmp,
    LPBYTE msg
)
{
    // Create hash context
    cryptCreateContext(&m_crypthashContext, CRYPT_UNUSED, CRYPT_ALGO_SHA1);

    // Hash the message
    cryptEncrypt(m_crypthashContext, msg, lentmp);
    cryptEncrypt(m_crypthashContext, msg, 0);

    // Verify signature
    m_cryptstatus = cryptCheckSignature(
        lpSecHeader->Assinatura,
        lpSecHeader->lenAssinatura,
        m_cryptPublicContext,
        m_crypthashContext
    );

    // Cleanup
    cryptDestroyContext(m_crypthashContext);

    return m_cryptstatus;
}
```

#### Encryption

```cpp
int CThreadMQ::funcCript(
    LPSECHDR lpSecHeader,
    int& lentmp,
    LPBYTE msg
)
{
    // Create envelope (encryption context)
    cryptCreateEnvelope(&m_cryptContext, CRYPT_UNUSED, CRYPT_FORMAT_CRYPTLIB);

    // Add recipient's public key
    cryptSetAttribute(m_cryptContext, CRYPT_ENVINFO_PUBLICKEY, m_cryptPublicContext);

    // Encrypt data
    int outLen;
    cryptPushData(m_cryptContext, msg, lentmp, &outLen);
    cryptFlushData(m_cryptContext);

    // Get encrypted data
    cryptPopData(m_cryptContext, lpSecHeader->DadosCriptografados,
                 sizeof(lpSecHeader->DadosCriptografados),
                 &lpSecHeader->lenDadosCriptografados);

    // Cleanup
    cryptDestroyEnvelope(m_cryptContext);

    return CRYPT_OK;
}
```

#### Decryption

```cpp
int CThreadMQ::funcDeCript(
    LPSECHDR lpSecHeader,
    int& lentmp,
    LPBYTE msg
)
{
    // Create envelope for decryption
    cryptCreateEnvelope(&m_cryptContext, CRYPT_UNUSED, CRYPT_FORMAT_CRYPTLIB);

    // Push encrypted data
    int outLen;
    cryptPushData(m_cryptContext,
                  lpSecHeader->DadosCriptografados,
                  lpSecHeader->lenDadosCriptografados,
                  &outLen);

    // Add private key for decryption
    cryptSetAttribute(m_cryptContext, CRYPT_ENVINFO_PRIVATEKEY, m_cryptPrivateContext);

    // Get decrypted data
    cryptPopData(m_cryptContext, msg, lentmp, &lentmp);

    // Cleanup
    cryptDestroyEnvelope(m_cryptContext);

    return CRYPT_OK;
}
```

---

## 13. Referência de API

### Main Classes Quick Reference

| Class | Arquivo | Propósito | Herda de |
|-------|---------|-----------|----------|
| **CNTService** | ntservice.h | Windows Service base | CObject |
| **CInitSrv** | InitSrv.h | Service implementation | CNTService |
| **CMainSrv** | MainSrv.h | Main service orchestrator | CObject |
| **CMonitor** | Monitor.h | TCP/IP server | CObject |
| **CThreadMQ** | ThreadMQ.h | MQ thread base | CObject |
| **CBacenReq** | BacenReq.h | Bacen request processor | CThreadMQ |
| **CBacenRsp** | BacenRsp.h | Bacen response processor | CThreadMQ |
| **CBacenRep** | BacenRep.h | Bacen replication | CThreadMQ |
| **CBacenSup** | BacenSup.h | Bacen support | CThreadMQ |
| **CIFReq** | IFReq.h | IF request sender | CThreadMQ |
| **CIFRsp** | IFRsp.h | IF response processor | CThreadMQ |
| **CIFRep** | IFRep.h | IF replication | CThreadMQ |
| **CIFSup** | IFSup.h | IF support | CThreadMQ |
| **CClientItem** | MainSrv.h | TCP client metadata | CObject |
| **CQueueList** | MainSrv.h | Thread-safe collection | CObject |
| **CBacenAppRS** | BacenAppRS.h | Bacen app recordset | CRecordset |
| **CIFAppRS** | IFAppRS.h | IF app recordset | CRecordset |
| **CControleRS** | ControleRS.h | Control recordset | CRecordset |
| **CSTRLogRS** | STRLogRS.h | Log recordset | CRecordset |
| **CBCDatabase** | CBCDb.h | Database wrapper | CDatabase |

---

## Conclusão

Este documento fornece uma referência técnica completa do sistema BCSrvSqlMq, cobrindo:

✅ Arquitetura geral e hierarquia de classes
✅ Infraestrutura de Windows Service
✅ Servidor TCP/IP de monitoramento
✅ Threads de processamento MQ (8 threads especializadas)
✅ Classes de banco de dados (recordsets)
✅ Gerenciamento de clientes TCP
✅ Modelo de threading e sincronização
✅ Fluxo de dados e mensagens
✅ Configuração do sistema
✅ Segurança e criptografia
✅ Referência de API

### Para Mais Informações

- **README.md** - Guia de build e configuração
- **MODERNIZATION_PHASE2.md** - Modernização de memória
- **MODERNIZATION_PHASE3.md** - Modernização de threading
- **MODERNIZATION_PHASE4.md** - Containers STL
- **MODERNIZATION_PHASE5.md** - Sintaxe C++ moderna
- **CLEANUP.md** - Limpeza de arquivos legados

---

**Última Atualização:** 21/02/2026
**Versão:** 1.0.5 (C++20 Modernized)
**Autor:** Claude Sonnet 4.5
