// MainSrv.cpp

// Fase 6: Removido #define _WIN32_WINNT 0x0400 (obsoleto, definido pelo CMake)

#include <afx.h>
#include <afxmt.h>
#include <afxdb.h>
#include <cmqc.h>
#include "MsgSgr.h"
#include <odbcinst.h>
// Modernização Fase 4: STL headers
#include <algorithm>
#include "NTServApp.h"
#include "InitSrv.h"
#include "winsock2.h"

// Fase 6: Desfazer conflitos wincrypt.h ANTES de incluir cryptlib.h
#include "crypto_compat.h"
#include "cryptlib.h"
#include "ThreadMq.h"
#include "CBCDb.h"
#include "ControleRS.h"
#include "STRLogRS.h"
#include "BacenAppRS.h"
#include "IFAppRS.h"
#include "BacenReq.h"
#include "BacenRsp.h"
#include "BacenRep.h"
#include "BacenSup.h"
#include "IFReq.h"
#include "IFRsp.h"
#include "IFRep.h"
#include "IFSup.h"
#include "MsgSgr.h"
#include "MainSrv.h"
#include "Monitor.h"

/*-------------------------------------------------------------------------*/

CQueueList::CQueueList(LPCTSTR lpszName, BOOL bIsTrueList)
{
	m_lpszName		= lpszName;
	m_bIsTrueList	= bIsTrueList;
	// Modernização C++20: CreateMutex → std::mutex (RAII, inicialização automática)
	// m_mutex é inicializado automaticamente no construtor
	m_iMaxList		= 0;
	// Modernização Fase 4: std::vector inicializa automaticamente vazio
	// Não precisa de alocação manual
}

CQueueList::~CQueueList()
{
	// Modernização C++20: std::lock_guard garante unlock automático (RAII)
	std::lock_guard<std::mutex> lock(m_mutex);

	if (m_bIsTrueList)
	{
		// Modernização Fase 4: std::vector → size() e operator[]
		size_t index = m_QueueList.size();
		for (size_t i = 0; i < index; i++)
		{
			CObject* WorkObj = static_cast<CObject*>(m_QueueList[i]);
			m_QueueList[i] = nullptr;
			delete WorkObj;
		}
	}

	// Modernização Fase 4: RemoveAll() → clear()
	m_QueueList.clear();
	// Modernização C++20: std::mutex limpa automaticamente
	// Não precisa de CloseHandle(m_mutex)
}

int CQueueList::Add(CObject * obj)
{
	// Modernização C++20: std::lock_guard → RAII automático (exception-safe)
	std::lock_guard<std::mutex> lock(m_mutex);

	// Modernização Fase 4: Add() → push_back(), GetSize() → size()
	m_QueueList.push_back(obj);
	int rt = static_cast<int>(m_QueueList.size()) - 1;  // Retorna índice do elemento adicionado
	int ct = static_cast<int>(m_QueueList.size());

	if (ct > m_iMaxList)
	{
		m_iMaxList = ct;
	}

	// lock_guard libera o mutex automaticamente ao sair do escopo
	return rt;
}

int CQueueList::GetSize()
{
	// Modernização C++20: std::lock_guard → RAII automático
	std::lock_guard<std::mutex> lock(m_mutex);
	// Modernização Fase 4: GetSize() → size()
	return static_cast<int>(m_QueueList.size());
}

int CQueueList::GetMaxSize()
{
	// Modernização C++20: std::lock_guard → RAII automático
	std::lock_guard<std::mutex> lock(m_mutex);
	return m_iMaxList;
}

CObject* CQueueList::GetAt( int position )
{
	CObject* obj = nullptr;

	// Modernização Fase 4: GetUpperBound() → empty() check
	if (m_QueueList.empty())
		return obj;

	// Modernização Fase 4: GetUpperBound() < position → size() check
	if (static_cast<int>(m_QueueList.size()) <= position)
		return obj;

	// Modernização C++20: std::lock_guard → RAII automático
	std::lock_guard<std::mutex> lock(m_mutex);
	// Modernização Fase 4: GetAt() → operator[]
	obj = m_QueueList[position];

	return obj;
}

CObject* CQueueList::GetFirst()
{
	CObject* obj = nullptr;

	// Modernização Fase 4: GetUpperBound() → empty() check
	if (m_QueueList.empty())
		return obj;

	// Modernização C++20: std::lock_guard → RAII automático
	std::lock_guard<std::mutex> lock(m_mutex);

	// Modernização Fase 4: GetSize() → size(), GetAt(0) → front() ou [0]
	if (!m_QueueList.empty())
	{
		obj = m_QueueList[0];
	}

	return obj;
}

void CQueueList::RemoveAt( int nIndex, int nCount)
{
	// Modernização Fase 4: GetUpperBound() → empty() check
	if (m_QueueList.empty())
		return;

	// Modernização C++20: std::lock_guard → RAII automático
	std::lock_guard<std::mutex> lock(m_mutex);
	// Modernização Fase 4: RemoveAt() → erase()
	if (nIndex >= 0 && nIndex < static_cast<int>(m_QueueList.size()))
	{
		auto start = m_QueueList.begin() + nIndex;
		auto end = start + std::min(nCount, static_cast<int>(m_QueueList.size()) - nIndex);
		m_QueueList.erase(start, end);
	}
}

void CQueueList::RemoveAll()
{
	// Modernização Fase 4: GetUpperBound() → empty() check
	if (m_QueueList.empty())
		return;

	// Modernização C++20: std::lock_guard → RAII automático
	std::lock_guard<std::mutex> lock(m_mutex);
	// Modernização Fase 4: RemoveAll() → clear()
	m_QueueList.clear();
}

CClientItem* CQueueList::LocateSockAddr(char * sockaddr)
{
	// Modernização C++20: std::lock_guard → RAII automático
	std::lock_guard<std::mutex> lock(m_mutex);

	// Modernização Fase 5: Range-based for loop
	for (auto* obj : m_QueueList)
	{
		auto* pCurCli = static_cast<CClientItem*>(obj);
		if (memcmp(reinterpret_cast<char*>(&pCurCli->m_AddrCli), sockaddr, sizeof(SOCKADDR_IN)) == 0)
		{
//			pCurCli->Lock();
//			pCurCli->Unlock();
			return pCurCli;
		}
	}

	return nullptr;
}

void CQueueList::DepuraSockAddr(CMainSrv *pMainSrv, char *m_szTaskName)
{
	// Modernização C++20: std::lock_guard → RAII automático
	std::lock_guard<std::mutex> lock(m_mutex);

	// Modernização Fase 5: Range-based for loop + auto keyword
	for (auto* obj : m_QueueList)
	{
		auto* pCurCli = static_cast<CClientItem*>(obj);
		pMainSrv->pInitSrv->m_WriteReg(m_szTaskName, FALSE, sizeof(pCurCli->m_AddrCli),
			reinterpret_cast<char*>(&pCurCli->m_AddrCli));
	}
}

CClientItem* CQueueList::LocateSock(SOCKET sock)
{
	// Modernização C++20: std::lock_guard → RAII automático
	std::lock_guard<std::mutex> lock(m_mutex);

	// Modernização Fase 5: Range-based for loop + auto keyword
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

CClientItem* CQueueList::RemoveSock(SOCKET sock)
{
	// Modernização C++20: std::lock_guard → RAII automático
	std::lock_guard<std::mutex> lock(m_mutex);

	// Modernização Fase 5: std::find_if (algoritmo STL) + lambda
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





/*-------------------------------------------------------------------------*/
CClientItem::CClientItem(char *CliHumano , char *szPorta)
{
	m_lpszName.Format("%s %s", CliHumano,szPorta);

	// Modernização C++20: CreateMutex → std::mutex (RAII, inicialização automática)
	// m_mutex é inicializado automaticamente

	memset(m_CliHumano, 0x00, sizeof(m_CliHumano));
	memset(m_szPorta, 0x00, sizeof(m_szPorta));
	CopyMemory(&m_CliHumano, CliHumano, sizeof(m_CliHumano));
	CopyMemory(&m_szPorta, szPorta, sizeof(m_szPorta));
	m_lpCliHumano = reinterpret_cast<char*>(&m_CliHumano);
	m_lpszPorta   = reinterpret_cast<char*>(&m_szPorta);
	m_ComputerName	= "NONE";
	m_UseridName	= "NONE";

	// Modernização C++20: new BYTE[] → std::make_unique<BYTE[]> (gerenciamento automático)
	dadosin		= std::make_unique<BYTE[]>(MAXMSGLENGTH);
	dadosout	= std::make_unique<BYTE[]>(MAXMSGLENGTH);

	tamdadosin	= 	0;
	tamdadosout	= 	0;
	m_timeout	= 0;
	m_ForceCli	= false;
	m_IsActive	= true;
	m_status	= ST_CLI_DISCONNECT;
	m_index		= -1;

	if (dadosin)
	{
		memset(dadosin.get(), 0x00, MAXMSGLENGTH);
	}
	else
	{
		m_IsActive	= false;
	}

	if (dadosout)
	{
		memset(dadosout.get(), 0x00, MAXMSGLENGTH);
	}
	else
	{
		m_IsActive	= false;
	}
}

CClientItem::~CClientItem()
{
	m_IsActive	= false;
	// Modernização C++20: std::unique_ptr limpa automaticamente
	// Não precisa de delete dadosin/dadosout
	// Modernização C++20: std::mutex limpa automaticamente
	// Não precisa de CloseHandle(m_mutex)
}


BOOL CClientItem::Lock()
{
	// Modernização C++20: std::mutex::lock()
	m_mutex.lock();
	return false;
}

BOOL CClientItem::Unlock()
{
	// Modernização C++20: std::mutex::unlock()
	m_mutex.unlock();
	return false;
}

/*-------------------------------------------------------------------------*/
//CProcessoId::CProcessoId(LPCTSTR nsu)
//{
//	m_lpszName = nsu;
//
//	m_mutex			= CreateMutex(NULL,FALSE,(LPCTSTR) m_lpszName);
//	tamdadosin	= 	0;
//	tamdadosout	= 	0;
//	m_timeout	= 0;								//tempo maximo de time em segundos
//	m_IsActive	= true;
//	dadosin		= (LPMIMSG) new BYTE[MAXMSGLENGTH];	// buffer de dados.
//	dadosout	= (LPMIMSG) new BYTE[MAXMSGLENGTH];	// buffer de dados.

//	if (dadosin)
//		memset(dadosin,0x00,MAXMSGLENGTH);
//	else
//		m_IsActive	= false;
//
//	if (dadosout)
//		memset(dadosout,0x00,MAXMSGLENGTH);
//	else
//		m_IsActive	= false;
//}

//CProcessoId::~CProcessoId()
//{
//	m_IsActive	= false;
//	if (dadosin != NULL)
//		delete dadosin;	
//	if (dadosout != NULL)
//		delete dadosout;	
//	if (m_mutex != NULL)
//	{
//		ReleaseMutex(m_mutex);
//		CloseHandle(m_mutex);
//	}
//}

//BOOL CProcessoId::Lock()
//{
//	WaitForSingleObject(m_mutex, INFINITE);
//	return false;
//}

//BOOL CProcessoId::Unlock()
//{
//	ReleaseMutex(m_mutex);
//	return false;
//}

/*-------------------------------------------------------------------------*/
CMainSrv::CMainSrv()
{
	strcpy(m_szTaskName,"MainSrv   (BCSrvSqlMq)");
	m_lpTaskName = (char *) &m_szTaskName;

	DWORD i;

	for (i = 0;i < TASKS_COUNT; i++)
	{
		m_StatusTask[i].bTaskNum = i;
		memset(&m_StatusTask[i].bTaskName,' ',sizeof(m_StatusTask[0].bTaskName));
		m_StatusTask[i].iTaskAutomatic = 0x00;
		m_StatusTask[i].iTaskIsRunning = 0x00;
	}

	m_TaskBacenReq	= -1;
	
	
	m_hEvent[0] = CreateWaitableTimer(NULL, FALSE, NULL);	

	for( i = 1; i < QTD_EVENTS_FIXED; ++i )
 		m_hEvent[i]	= CreateEvent(NULL,TRUE,FALSE,NULL);

	MainIsRunning = false;
	MoniIsRunning = false;
	MainIsStoping = false;
}

CMainSrv::~CMainSrv()
{
    for( DWORD i = 0; i < QTD_EVENTS_FIXED; ++i )
 		CloseHandle(m_hEvent[i]);

	// Modernização C++20: std::unique_ptr limpa automaticamente
	// Não precisa de delete m_TaskList, m_StopList, m_ClientList, m_MonitorList
}


BOOL CMainSrv::PreparaTasks(LPVOID InitSrv)
{
	iCount = 100;
	pInitSrv  = (CInitSrv *) InitSrv;
	pInitSrv->m_WriteLog(m_szTaskName,8002,FALSE,&m_lpTaskName,NULL,NULL,NULL,NULL);

    CString wrknamelist;
    wrknamelist = pInitSrv->m_szServiceName;
    wrknamelist += " (Main Task List)";
	// Modernização C++20: new → std::make_unique (gerenciamento automático)
	m_TaskList		= std::make_unique<CQueueList>(wrknamelist, TRUE);
    wrknamelist = pInitSrv->m_szServiceName;
    wrknamelist += " (Main Stop List)";
	m_StopList		= std::make_unique<CQueueList>(wrknamelist, FALSE);
    wrknamelist = pInitSrv->m_szServiceName;
    wrknamelist += " (Main Client List)";
	m_ClientList	= std::make_unique<CQueueList>(wrknamelist, TRUE);
    wrknamelist = pInitSrv->m_szServiceName;
    wrknamelist += " (Monitor List)";
	m_MonitorList	= std::make_unique<CQueueList>(wrknamelist, FALSE);

	CString pathAudit(' ',255);
	char  workpath[255];

	pathAudit = pInitSrv->m_DirAudFile;
	
	strcpy((char*) &workpath,pathAudit);
	char filepgm[64]; // nome do servi�o
	memset(&filepgm,0x00,sizeof(filepgm));
	memcpy(&filepgm,pInitSrv->m_szServiceName,sizeof(pInitSrv->m_szServiceName));

	if (InitAudit())
	{
		pInitSrv->m_WriteLog(m_szTaskName,8063,FALSE,NULL,NULL,NULL,NULL,NULL);
		return FALSE;
	}
	if (OpenAudit((char*) &workpath, (char*) &filepgm))
	{
		pInitSrv->m_WriteLog(m_szTaskName,8064,FALSE,NULL,NULL,NULL,NULL,NULL);
		return FALSE;
	}

	SetPriorityClass(GetCurrentProcess(),REALTIME_PRIORITY_CLASS);

	BCSrvSqlMQPort	= pInitSrv->m_MonitorPort;

	MainIsRunning = true;

	pMonitor = new CMonitor();

	if (pMonitor == NULL)
	{
		pInitSrv->m_WriteLog(m_szTaskName,8003,FALSE,NULL,NULL,NULL,NULL,NULL);
		return FALSE;
	}



/*---------------------------------------------------------------------------------------------
	DSN-less ODBC Connection: SQLConfigDataSource disabled

	The code below is no longer needed because we're using DSN-less ODBC connection strings.
	The full connection string is built in InitSrv.cpp and stored in pInitSrv->m_DBName.
	This eliminates the need to configure ODBC Data Source Names via ODBC Administrator.

	If you need to revert to DSN-based connections, uncomment this section.
---------------------------------------------------------------------------------------------*/
#if 0
	UCHAR szAttributes[256];
	CString dsn,srv,dbq,dbn;
	if (pInitSrv->m_DBServer.Compare(pInitSrv->m_ComputerName) == 0)
	{
		pInitSrv->m_WriteLog(m_szTaskName,8004,FALSE,&pInitSrv->m_DBAliasName,&pInitSrv->m_DBServer,NULL,NULL,NULL);
		dsn = "DSN=" + pInitSrv->m_DBAliasName;
		srv = "Server=(local)";
		dbn = "DATABASE=" + pInitSrv->m_DBName;
		sprintf( (char *) szAttributes,"%s\r%s\r%s\r%s\r%s\r\0",
								dsn,
								srv,
								dbn,
								"Description=DataBase da Agencia",
								"Trusted_Connection=Yes");

		for (int i = 0; i < sizeof(szAttributes);i++)
		{
			if (szAttributes[i] == '\r')
			    szAttributes[i] = '\0';
		}
			int rcConfig = SQLConfigDataSource(	NULL,ODBC_ADD_SYS_DSN,(LPSTR) "SQL Server",
										(LPSTR) &szAttributes);
		if (rcConfig == 0)
		{
			pInitSrv->m_WriteLog(m_szTaskName,8008,FALSE,&pInitSrv->m_DBAliasName,&pInitSrv->m_DBServer,NULL,NULL,NULL);
		}
	}
	else
	{
		pInitSrv->m_WriteLog(m_szTaskName,8004,FALSE,&pInitSrv->m_DBAliasName,&pInitSrv->m_DBServer,NULL,NULL,NULL);
		dsn = "DSN=" + pInitSrv->m_DBAliasName;
		srv = "Server=" + pInitSrv->m_DBServer;
		dbn = "DATABASE=" + pInitSrv->m_DBName;
		sprintf( (char *) szAttributes,"%s\r%s\r%s\r%s\r%s\r\0",
								dsn,
								srv,
								dbn,
								"Description=DataBase da Agencia",
								"Trusted_Connection=Yes");
			for (int i = 0; i < sizeof(szAttributes);i++)
		{
			if (szAttributes[i] == '\r')
			    szAttributes[i] = '\0';
		}
			int rcConfig = SQLConfigDataSource(	NULL,ODBC_ADD_SYS_DSN,(LPSTR) "SQL Server",
										(LPSTR) &szAttributes);
		if (rcConfig == 0)
		{
			pInitSrv->m_WriteLog(m_szTaskName,8005,FALSE,&pInitSrv->m_DBName,&pInitSrv->m_DBServer,NULL,NULL,NULL);
		}
	}
#endif

/*---------------------------------------------------------------------------------------------
	Ativar Task .
---------------------------------------------------------------------------------------------*/
	CThreadMQ* WorkThread = NULL;


	WorkThread = (CBacenReq *) new CBacenReq ("RmtReq    (___________) Task Req Remota.",TASK_AUTOMATIC,TASKS_BACENREQ,this);
	m_TaskBacenReq = m_TaskList->Add(WorkThread);
	WorkThread = (CBacenRsp *) new CBacenRsp ("RmtRsp    (___________) Task Rsp Remota.",TASK_AUTOMATIC,TASKS_BACENRSP,this);
	m_TaskBacenRsp = m_TaskList->Add(WorkThread);
	WorkThread = (CBacenRep *) new CBacenRep ("RmtRep    (___________) Task Rep Remota.",TASK_AUTOMATIC,TASKS_BACENREP,this);
	m_TaskBacenRep = m_TaskList->Add(WorkThread);
	WorkThread = (CBacenSup *) new CBacenSup ("RmtSup    (___________) Task Sup Remota.",TASK_AUTOMATIC,TASKS_BACENSUP,this);
	m_TaskBacenSup = m_TaskList->Add(WorkThread);
	WorkThread = (CIFReq *)    new CIFReq    ("LocReq    (___________) Task Req Local. ",TASK_AUTOMATIC,TASKS_IFREQ,this);
	m_TaskIFReq = m_TaskList->Add(WorkThread);
	WorkThread = (CIFRsp *)    new CIFRsp    ("LocRsp    (___________) Task Rsp Local. ",TASK_AUTOMATIC,TASKS_IFRSP,this);
	m_TaskIFRsp = m_TaskList->Add(WorkThread);
	WorkThread = (CIFRep *)    new CIFRep    ("LocRep    (___________) Task Rep Local. ",TASK_AUTOMATIC,TASKS_IFREP,this);
	m_TaskIFRep = m_TaskList->Add(WorkThread);
	WorkThread = (CIFSup *)    new CIFSup    ("LocSup    (___________) Task Sup Local. ",TASK_AUTOMATIC,TASKS_IFSUP,this);
	m_TaskIFSup = m_TaskList->Add(WorkThread);

    LARGE_INTEGER pDueTime;
    LONG lPeriod;

	pDueTime.LowPart	= (unsigned long) -1;   
	pDueTime.HighPart	= (unsigned long) -1;				
    lPeriod = 1000;							// de 1 em 1 segundos			

	if (!SetWaitableTimer(m_hEvent[MAIN_EVENT_TIMER], &pDueTime, lPeriod, NULL, NULL, FALSE))
	{
		int err = GetLastError();
		pInitSrv->m_WriteLog(m_szTaskName,8017,FALSE,&err,NULL,NULL,NULL,NULL);
		return FALSE;
	} 

	pInitSrv->m_WriteLog(m_szTaskName,8007,FALSE,NULL,NULL,NULL,NULL,NULL);
 	pMonitor->m_hThreadHandle = CreateThread(
			 NULL,					// atributos
			 16384,					// stack size
			 pMonitor->TaskMonitor,  // task procedure
			 this,					// parameter
			 0,						// flags	
			 &pMonitor->m_dwThreadId); // thread number
	
	CString msgdebug;
	msgdebug.Format("Monitor ThreadId = %04x",pMonitor->m_dwThreadId);
	pInitSrv->m_WriteLog(m_szTaskName,8008,FALSE,(char *) &msgdebug,NULL,NULL,NULL,NULL);

	if (pMonitor->m_hThreadHandle == NULL)
	{
		int err = GetLastError();
		pInitSrv->m_WriteLog(m_szTaskName,8009,FALSE,&err,NULL,NULL,NULL,NULL);
		delete pMonitor;
		return FALSE;
	}
	
	SetThreadPriority(pMonitor->m_hThreadHandle,THREAD_PRIORITY_HIGHEST);


	MoniIsRunning = true;
	
	return TRUE;
}

void CMainSrv::WaitTasks()
{
	DWORD		dwWait;

	while (MainIsRunning)
	{
		dwWait = WaitForMultipleObjects(QTD_EVENTS_FIXED, m_hEvent, FALSE, INFINITE);

		if ( dwWait ==  WAIT_FAILED)
		{
			int err = GetLastError();
			pInitSrv->m_WriteLog(m_szTaskName,8010,FALSE,&err,NULL,NULL,NULL,NULL);
			EndTasks();
			Sleep(500);
			MainIsRunning = false;
			pInitSrv->m_bIsRunning	= FALSE;
			return;
		}

		ResetEvent(m_hEvent[dwWait]);

		switch (dwWait)
		{
			case MAIN_EVENT_TIMER:
				if (MainIsStoping)
					break;
				ProcessaTimer();
				break;

			case MAIN_EVENT_ACABOU:
				MainIsRunning = false;
				break;

			case MAIN_EVENT_STOP:
				pInitSrv->m_WriteLog(m_szTaskName,8011,FALSE,NULL,NULL,NULL,NULL,NULL);
				MainIsStoping = true;
				EndTasks();
				CheckFinaliza();
				if (pInitSrv->m_bIsShutDownNow == TRUE)
				{
					Sleep(2000);
					return;
				}
				break;

			case MAIN_EVENT_PAUSE:
				break;

			case MAIN_EVENT_CONTINUE:
				break;

			case MAIN_EVENT_MONITOR_STOP:
				MoniIsRunning = false;
				CheckFinalizaMon();
				delete pMonitor;
				pInitSrv->MsgToLog(EVENTLOG_WARNING_TYPE,EVMSG_MONITOR, "Task MONITOR Deletada.\r\n");
				break;

			case MAIN_EVENT_TASKSAPP_STOP:
				ProcessaStopList();
				if (MainIsStoping)
				{
					CheckFinaliza();
				}
				break;

			default:
				break;
		}

	}

	CancelWaitableTimer(m_hEvent[MAIN_EVENT_TIMER]);

	CThreadMQ* WorkThread;
//	char bufwrk[256];
	
	while (m_TaskList->GetSize())
	{
		WorkThread = (CThreadMQ *) m_TaskList->GetFirst();
		if (WorkThread)
		{
			WorkThread->Lock();
			if (WorkThread->m_ThreadIsRunning)
			{
				WorkThread->Unlock();
			}
			else
			{
				m_TaskList->RemoveAt(0);
//				wsprintf(bufwrk,"Deletando task: %s.\r\n",WorkThread->m_lpTaskName);
//				pInitSrv->MsgToLog(EVENTLOG_WARNING_TYPE,EVMSG_MONITOR, bufwrk);
				WorkThread->Unlock();
				delete WorkThread;
			}
		}
	}

	CloseAudit();
	TermAudit();

	pInitSrv->m_WriteLog(m_szTaskName,8012,FALSE,&m_lpTaskName,NULL,NULL,NULL,NULL);
	pInitSrv->MsgToLog(EVENTLOG_INFORMATION_TYPE,EVMSG_MAIN,"Terminando task MAINSRV.\r\n");
	return;
}

void CMainSrv::EndTasks()
{
	CThreadMQ* WorkThread;

	int index = m_TaskList->GetSize();

	for (int i = 0;i < index;i++)
	{
		WorkThread = (CThreadMQ *) m_TaskList->GetAt(i);
		if (WorkThread == NULL)
			continue;

		WorkThread->Lock();
		WorkThread->m_AutomaticThread = TASK_MANUAL;
		if (WorkThread->m_ThreadIsRunning)
		{
			SetEvent(WorkThread->m_hEvent[THREAD_EVENT_STOP]);
		}
		WorkThread->Unlock();
	}
	
	return;
}

void CMainSrv::CheckFinaliza()
{
	CThreadMQ* WorkThread;
	int index = m_TaskList->GetSize();
	
	BOOL taskativa = FALSE;

	for (int i = 0;i < index;i++)
	{
		WorkThread = (CThreadMQ *) m_TaskList->GetAt(i);
		if (WorkThread == NULL)
			continue;

		WorkThread->Lock();
		if (WorkThread->m_ThreadIsRunning)
		{
			taskativa = TRUE;
			WorkThread->Unlock();
			break;
		}
		WorkThread->Unlock();
	}
	
	if (taskativa)
		return;

	if (MoniIsRunning)
	{
		SetEvent(pMonitor->m_hEvent[MONI_EVENT_STOP]);
		return;
	}

}


void CMainSrv::CheckFinalizaMon()
{
	if (MoniIsRunning)
		return;

	SetEvent(m_hEvent[MAIN_EVENT_ACABOU]);
}


void CMainSrv::ProcessaTimer()
{
	if (iCount < 20)
	{
		iCount++;
		return;
	}

	iCount = 0;

	CThreadMQ* WorkThread;
	int index = m_TaskList->GetSize();
	
	for (int i = 0;i < index;i++)
	{
		WorkThread = (CThreadMQ *) m_TaskList->GetAt(i);

		if (WorkThread->m_AutomaticThread)
		{
			if (!WorkThread->m_ThreadIsRunning)
			{
				WorkThread->Lock();
				WorkThread->m_hThreadHandle = CreateThread(
						 NULL,							// atributos
						 16384,							// stack size
						 WorkThread->TaskThread,		// task procedure
						 this,							// parameter
						 0,								// flags	
						 &WorkThread->m_dwThreadId);	// thread number
				WorkThread->Unlock();

				if (WorkThread->m_hThreadHandle == NULL)
				{
					pInitSrv->m_WriteLog(m_szTaskName,8013,FALSE,&WorkThread->m_lpTaskName,NULL,NULL,NULL,NULL);
				}
				else
				{
					CString msgdebug;
					msgdebug.Format("%s ThreadId = %04x",WorkThread->m_szTaskName,WorkThread->m_dwThreadId);
					pInitSrv->m_WriteLog(m_szTaskName,8008,FALSE,(char *) &msgdebug,NULL,NULL,NULL,NULL);
					SetThreadPriority(WorkThread->m_hThreadHandle,THREAD_PRIORITY_HIGHEST);
				}
			}
		}
	}
}

void CMainSrv::ProcessaStopList()
{
	CThreadMQ* WorkThread;
//	char bufwrk[256];
	
	while (m_StopList->GetSize())
	{
		WorkThread = (CThreadMQ *) m_StopList->GetFirst();
		if (WorkThread != NULL)
		{
//			wsprintf(bufwrk,"Processando stop para task: %s.\r\n",WorkThread->m_lpTaskName);
//			pInitSrv->MsgToLog(EVENTLOG_WARNING_TYPE,EVMSG_MONITOR, bufwrk);
			m_StopList->RemoveAt(0);
			WorkThread->Lock();
			WorkThread->m_ThreadIsRunning = false;
			WorkThread->Unlock();
		}
	}
}


bool CMainSrv::InitAudit()
{
	CTime	t	=	CTime::GetCurrentTime();

    CString txt =   "Sincroniza Audit ";
    txt +=  pInitSrv->m_szServiceName;

	m_hAuditmutex	= CreateMutex(NULL,FALSE,txt);
	if (m_hAuditmutex == NULL)
	{
		return true;
	}
	
	return false;
}

void CMainSrv::TermAudit() 
{
	if (m_hAuditmutex != NULL)
	{
		CloseHandle( m_hAuditmutex );
	}
	return ;
}

BOOL CMainSrv::CheckDataAudit()
{
	CTime t = CTime::GetCurrentTime();
	CString s1 = t.Format( "%Y%m%d" );
	CString s2 = m_AuditDataOpen.Format( "%Y%m%d" );

	if (s1.Compare(s2) == 0)
		return FALSE;

	CloseAudit();

	return OpenAudit(m_pathAudit, m_nameAudit);
}

BOOL CMainSrv::OpenAudit(CString pathAudit, CString nameAudit)
{
	BOOL rt = FALSE;
	CString FileName;
	CString WorknameAudit;

	m_pathAudit = pathAudit;
	m_nameAudit = nameAudit;

	CTime t = CTime::GetCurrentTime();
	m_AuditDataOpen = t;

	int pos = nameAudit.Find('.');

	if (pos == -1)
	{
		WorknameAudit = nameAudit + t.Format("_%d_%m_%Y");		
		WorknameAudit += ".Audit";		
	}
	else
	{
		WorknameAudit = nameAudit.Left(pos) + t.Format("_%d_%m_%Y");
		WorknameAudit += ".Audit";		
	}

	if (WorknameAudit[0] == '\\')
	{
		FileName = pathAudit + WorknameAudit;
	}
	else
	{
		FileName = pathAudit + "\\";
		FileName += WorknameAudit;
	}

	CreateDirectory(pathAudit,NULL);

	m_hAudit = CreateFile(FileName, GENERIC_WRITE | GENERIC_READ,
			 FILE_SHARE_READ, NULL, OPEN_EXISTING ,
			 FILE_ATTRIBUTE_NORMAL | FILE_FLAG_WRITE_THROUGH , NULL);

	if ( m_hAudit ==  INVALID_HANDLE_VALUE)
	{
		m_hAudit = CreateFile(FileName, GENERIC_WRITE | GENERIC_READ,
				FILE_SHARE_READ, NULL, CREATE_ALWAYS ,
				FILE_ATTRIBUTE_NORMAL | FILE_FLAG_WRITE_THROUGH , NULL);
	}

CheckFile:
	if ( m_hAudit ==  INVALID_HANDLE_VALUE)
	{
		m_hAudit = NULL;
		rt = TRUE;
		return rt;
	}

	char RegAudit[11];
	DWORD bytes_lidos;

	if (ReadFile( m_hAudit, RegAudit,
		  10, &bytes_lidos, NULL) != 0)
	{
		if (bytes_lidos != 0)
		{
			RegAudit[10] = 0;
			CTime t = CTime::GetCurrentTime();
			m_AuditDataOpen = t;
			CString s = t.Format( "%Y%m%d" );
			if (s.Compare(RegAudit+2) == 0)
			{
				long lDistanceHigh = 0;
				DWORD lDistanceLow = 0;
				lDistanceLow = SetFilePointer (m_hAudit, lDistanceLow, 
                               &lDistanceHigh, FILE_END); 
			}
			else
			{
				CloseHandle(m_hAudit);
				m_hAudit = CreateFile(FileName, GENERIC_WRITE | GENERIC_READ,
						FILE_SHARE_READ, NULL, CREATE_ALWAYS,
						FILE_ATTRIBUTE_NORMAL | FILE_FLAG_WRITE_THROUGH , NULL);
				goto CheckFile;
			}
		}
	}

	return rt;
}

void CMainSrv::CloseAudit()
{
	WaitForSingleObject(m_hAuditmutex, INFINITE);

	if (m_hAudit)
	{
		CloseHandle(m_hAudit);
		m_hAudit = NULL;
	}

	ReleaseMutex(m_hAuditmutex);
}

BOOL CMainSrv::WriteAudit(UINT len, BYTE* lpbuffer)
{
	BOOL rt = FALSE;
	
	WaitForSingleObject(m_hAuditmutex, INFINITE);

	rt = CheckDataAudit();	
	if (rt)
	{
		ReleaseMutex(m_hAuditmutex);
		return rt;
	}
	DWORD bytes_gravados;

	if (m_hAudit)
	{
		if(WriteFile( m_hAudit, (char *) lpbuffer,
					len,
					(unsigned long *) &bytes_gravados, NULL) == 0)
		{
			CloseHandle(m_hAudit);
			m_hAudit = NULL;
			rt = TRUE;
		}
		else
		{
			FlushFileBuffers(m_hAudit);
		}
	}
	else
	{
		rt = TRUE;
	}

	ReleaseMutex(m_hAuditmutex);
	return rt;
}

void CMainSrv::MontaAudit(UINT& len, BYTE* lpbuffer ,  SYSTEMTIME *time, BYTE* lpHdrMQ, long lenmsg, BYTE* lpMsgxml)
{
	STAUDITFILE *audreg = (STAUDITFILE*) lpbuffer;


	audreg->AUD_TAMREG = 0;

	memset(audreg->AUD_AAAAMMDD,0x00,sizeof(audreg->AUD_AAAAMMDD));
	memset(audreg->AUD_HHMMDDSS,0x00,sizeof(audreg->AUD_HHMMDDSS));
	wsprintf((char *) audreg->AUD_AAAAMMDD,"%04d%02d%02d",time->wYear,time->wMonth,time->wDay);
	wsprintf((char *) audreg->AUD_HHMMDDSS,"%02d%02d%02d%02d",time->wHour,time->wMinute,time->wSecond, (time->wMilliseconds / 10));

	memset(audreg->AUD_MQ_HEADER,0x00,512);
	memset(audreg->AUD_SEC_HEADER,0x00,sizeof(SECHDR));
	memset(audreg->AUD_SPBDOC,0x00,lenmsg);

	memcpy((char *) audreg->AUD_MQ_HEADER,lpHdrMQ,sizeof(MQMD));
	if (lenmsg > 0)
	{
		memcpy((char *) audreg->AUD_SEC_HEADER,lpMsgxml,lenmsg);
	}

	len = 8 + 8 + 512 + lenmsg;
	audreg->AUD_TAMREG = len;

	memcpy(lpbuffer + 2 + len, (BYTE *) audreg, sizeof(audreg->AUD_TAMREG));

	len += 4;

	return;
}

