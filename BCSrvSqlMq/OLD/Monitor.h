// Monitor.h

#ifndef _MONITOR_H_
#define _MONITOR_H_

// Modernização C++20: Includes padrão
#include <thread>
#include <memory>
#include <atomic>

// Modernização C++20: Macros → constexpr
namespace MonitorEvent {
    constexpr int TIMER = 0;
    constexpr int TCP = 1;
    constexpr int STOP = 2;
    constexpr int MST = 3;
    constexpr int QUEUE = 4;
}

constexpr int QTD_MONI_EVENTS = 55;
constexpr int EVENT_CLITCP = 5;

// Manter compatibilidade
#define MONI_EVENT_TIMER	MonitorEvent::TIMER
#define MONI_EVENT_TCP		MonitorEvent::TCP
#define MONI_EVENT_STOP		MonitorEvent::STOP
#define MONI_EVENT_MST		MonitorEvent::MST
#define MONI_EVENT_QUEUE	MonitorEvent::QUEUE

class CMainSrv;
class CMonitor
{
public:
	CMonitor();
	~CMonitor();
	static		DWORD WINAPI TaskMonitor(LPVOID MainSrv);
	void		RunMonitor(LPVOID MainSrv);

	// Modernização C++20: std::atomic para flag thread-safe
	std::atomic<bool>	isBusy;
	// Modernização C++20: std::thread ao invés de HANDLE
	std::unique_ptr<std::thread>	m_thread;
	std::thread::id	m_threadId;
	HANDLE		m_hThreadHandle;  // Manter para compatibilidade temporária
	DWORD		m_dwThreadId;     // Manter para compatibilidade com logs
	char		m_szTaskName[40];
	LPTSTR		m_lpTaskName;
	CMainSrv	*pMainSrv;
	// TODO Fase 4: Substituir eventos Win32 por std::condition_variable
	HANDLE		m_hEvent[QTD_MONI_EVENTS];
//  Evento 0=TIMER 1=TCP 2=STOP 3=MST 4=CLITCP
	int         TamSend;
	SOCKET		CliSock[QTD_MONI_EVENTS - EVENT_CLITCP];
private:
	void		InitSrvSocket();
	void		AceitaConexao(int ErrorCode);
	void		RecebeDadosCli(int ErrorCode, int CurrCli);
	bool		SendDadosCli(CClientItem* pCurrCLI);
	void		ForceCloseCli(CClientItem* CurrCLI);
	void		CheckTimeout();
	void		ProcessaQueue();
	void		ProcessaDadosCli(CClientItem* pCurrCLI);

//	HANDLE		hCmdMutex; 
	WSANETWORKEVENTS m_TcpEvents;
	SOCKET		tCliSock;
	SOCKET		SrvSock;
    SOCKADDR_IN SrvAddrTcp;         
	char		szSrvHumano[30];	
	char		szSrvPorta[10];		
    SOCKADDR_IN CliAddrTcp;			
	linger		Linger; 
	unsigned long	addr_temp;
	PHOSTENT	phe;
    LARGE_INTEGER pDueTime;
    LONG		lPeriod;

	int			iqtdsock;		//quantidade de sockes de clientes
	int			indexCli;
	int         totArec;
	int			totJarec;
	int			faltaArec;
	int		    qtdRecNow;		//tamanho dos dados in Max=8192
	char	    dadosin[8192];	//comando recebido;
	LPMIMSG		pMsgRec;
	LPMIMSG		pMsgSend;
	UINT		StatusServer;

	// Nota: m_list é non-owning pointer (aponta para pMainSrv->m_MonitorList)
	CQueueList* m_list;
};

#endif // _MONITOR_H_
