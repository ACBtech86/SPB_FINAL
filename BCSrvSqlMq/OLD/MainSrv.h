// MainSrv.h

#ifndef _MAINSRV_H_
#define _MAINSRV_H_

#include <memory>
#include <mutex>
#include <vector>

// Modernização C++20: Substituir macros por constexpr
namespace MainEvent {
	constexpr int TIMER = 0;
	constexpr int ACABOU = 1;
	constexpr int STOP = 2;
	constexpr int PAUSE = 3;
	constexpr int CONTINUE = 4;
	constexpr int MONITOR_STOP = 5;
	constexpr int TASKSAPP_STOP = 6;
}
constexpr int QTD_EVENTS_FIXED = 7;

// Mantém compatibilidade com código legado
#define MAIN_EVENT_TIMER			MainEvent::TIMER
#define MAIN_EVENT_ACABOU			MainEvent::ACABOU
#define MAIN_EVENT_STOP				MainEvent::STOP
#define MAIN_EVENT_PAUSE			MainEvent::PAUSE
#define MAIN_EVENT_CONTINUE			MainEvent::CONTINUE
#define MAIN_EVENT_MONITOR_STOP		MainEvent::MONITOR_STOP
#define MAIN_EVENT_TASKSAPP_STOP	MainEvent::TASKSAPP_STOP

namespace ClientStatus {
	constexpr int CONNECT = 1;
	constexpr int CONSULTA = 2;
	constexpr int DISCONNECT = 3;
	constexpr int QUEUE = 4;
	constexpr int WAITRESP = 9;
}

// Mantém compatibilidade
#define ST_CLI_CONNECT			ClientStatus::CONNECT
#define ST_CLI_CONSULTA			ClientStatus::CONSULTA
#define ST_CLI_DISCONNECT		ClientStatus::DISCONNECT
#define ST_CLI_QUEUE			ClientStatus::QUEUE
#define ST_CLI_WAITRESP			ClientStatus::WAITRESP

constexpr bool TASK_AUTOMATIC = true;
constexpr bool TASK_MANUAL = false;



//------------------------------------------------------------//
// Constantes de funcoes para comunicacao entre tasks         //
//------------------------------------------------------------//

class CinitSrv;
class CMonitor;
class CBCDatabase;
class CBacenReqRS;
class CIFReqRS;
class CSTRLogRS;
;
//class CThreadApp;

class CClientItem : public CObject
{
public:
	CClientItem();
	CClientItem(char *CliHumano , char *szPorta);
	~CClientItem();
	BOOL Lock();
	BOOL Unlock();
protected:
	// Modernização C++20: HANDLE → std::mutex
	std::mutex		m_mutex;
	CString			m_lpszName;
public:
	bool			m_ForceCli;			//force client Active
	bool			m_IsActive;			//cliente Ativo
	int				m_status;			//ST_CLI_...
	int				m_index;			//indice do sock na rotina tcp
	SOCKET			m_Sock;
    SOCKADDR_IN		m_AddrCli;			//endereco e porta do cliente;
	char			m_CliHumano[30];	//endereco tcp/ip do cliente em forma humana.
	char			m_szPorta[10];		//porta conectada.
	char *			m_lpCliHumano;		//endereco tcp/ip do cliente em forma humana.
	char *			m_lpszPorta;		//porta conectada.
	CString			m_ComputerName;
	CString			m_UseridName;
	// Modernização C++20: raw pointers → std::unique_ptr
	std::unique_ptr<BYTE[]>	dadosin;	// buffer de dados.
	std::unique_ptr<BYTE[]>	dadosout;	// buffer de dados.
	int				tamdadosin;			// tamanho buffer de dados.
	int				tamdadosout;		// tamanho buffer de dados.
	int				m_timeout;			//tempo maximo de time em segundos
};


//class CProcessoId : public CObject
//{
//public:
//	CProcessoId();
//	CProcessoId(LPCTSTR NameLock);
//	~CProcessoId();
//	BOOL Lock();
//	BOOL Unlock();
//protected:
//	HANDLE			m_mutex;
//	CString			m_lpszName;
//public:
//	int				m_timeout;		//tempo maximo de time em segundos
//	bool			m_IsActive;
//	LPMIMSG			dadosin;		// buffer de dados.
//	LPMIMSG			dadosout;		// buffer de dados.
//	int				tamdadosin;		// tamanho buffer de dados.
//	int				tamdadosout;	// tamanho buffer de dados.
//};

class CQueueList : public CObject
{
// Attributes
public:
	CQueueList();
	CQueueList(LPCTSTR NameLock, BOOL bIsTrueList);
	~CQueueList();
	int Add(CObject * obj);
	void RemoveAt( int nIndex, int nCount = 1 );
	void RemoveAll();
	int GetSize();
	int GetMaxSize();
	CObject* GetAt( int position );
	CObject* GetFirst();
	CClientItem* LocateSock(SOCKET sock);
	CClientItem* RemoveSock(SOCKET sock);
	CClientItem* LocateSockAddr(char * sockaddr);
	void		 DepuraSockAddr(CMainSrv *pMainSrv, char *m_szTaskName);
//	CProcessoId* LocateOriginId(CClientItem* pCurrCli, BYTE * OriginId);
	CClientItem* LocateCliOrigin(BYTE * OriginId);
//	void		 RemoveOriginId(CClientItem* pCurrCli);
	void InactiveProcessoId(CClientItem* pCurrCli);

public:
	CString			m_lpszName;
	BOOL			m_bIsTrueList;
	int				m_iMaxList;

protected:
	// Modernização C++20: HANDLE → std::mutex (RAII automático)
	std::mutex		m_mutex;
	// Modernização Fase 4: CObArray → std::vector (STL container)
	std::vector<CObject*>	m_QueueList;
};

class CMainSrv
{
public:
	CMainSrv();
	~CMainSrv();
//	void			LockSyncLog();
//	void			UnlockSyncLog();
	BOOL			PreparaTasks(LPVOID MainSrv);
	void			WaitTasks();
public:
	void			ProcessaStopList();
	void			ProcessaTimer();
	HANDLE			m_hEvent[QTD_EVENTS_FIXED];
	HANDLE			hEventAgen;
	CMonitor		*pMonitor;					// Servico da Task MONITORACAO
	DWORD			qtdsessTot;
	bool			MainIsRunning;
	bool			MainIsStoping;
	bool			MoniIsRunning;
	char			m_szTaskName[40];
	LPTSTR			m_lpTaskName;
	CInitSrv		*pInitSrv;
	UINT			BCSrvSqlMQPort;
	int				iCount;
	HANDLE			m_hAudit;
	HANDLE			m_hAuditmutex;
	CString			m_pathAudit;
	CString			m_nameAudit;
	CTime			m_AuditDataOpen;

	long			m_ultnsu;

	// Modernização C++20: raw pointers → std::unique_ptr (RAII automático)
	std::unique_ptr<CQueueList>	m_StopList;
	std::unique_ptr<CQueueList>	m_ClientList;
	std::unique_ptr<CQueueList>	m_MonitorList;
	std::unique_ptr<CQueueList>	m_TaskList;

	int				m_TaskBacenReq;
	int				m_TaskBacenRsp;
	int				m_TaskBacenRep;
	int				m_TaskBacenSup;
	int				m_TaskIFReq;
	int				m_TaskIFRsp;
	int				m_TaskIFRep;
	int				m_TaskIFSup;


	BOOL			StartTask(DWORD i);
	void			EndTasks();
	void			CheckFinaliza();
	void			CheckFinalizaMon();
	bool		    InitAudit();
	void		    TermAudit();
	BOOL		    OpenAudit(CString pathAudit, CString nameAudit);
	void		    CloseAudit();
	BOOL			CheckDataAudit();
	BOOL			WriteAudit(UINT len, BYTE* lpbuffer);
	void			MontaAudit(UINT& len, BYTE* lpbuffer , SYSTEMTIME *time, BYTE* lpHdrMQ, long lenmsg, BYTE* lpMsgxml);


	STTASKSTATUS	m_StatusTask[TASKS_COUNT];
};

#endif
