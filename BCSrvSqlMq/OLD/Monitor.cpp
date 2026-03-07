// Monitor.cpp

// Fase 6: Removido #define _WIN32_WINNT 0x0400 (obsoleto, definido pelo CMake)


#include <afx.h>
#include <afxmt.h>
#include <afxdb.h>
#include <cmqc.h>
#include "MsgSgr.h"
#include "NTServApp.h"
#include "InitSrv.h"
// Fase 6: Desfazer conflitos wincrypt.h ANTES de incluir cryptlib.h
#include "crypto_compat.h"
#include "cryptlib.h"
#include "winsock2.h"
#include "MainSrv.h"
#include "Monitor.h"
#include "ThreadMQ.h"

//------------------------------------------------------------------------------------

DWORD WINAPI CMonitor::TaskMonitor(LPVOID MainSrv)
{
	// Modernização Fase 5: auto keyword + static_cast
	auto* pMainSrv = static_cast<CMainSrv*>(MainSrv);
	char bufwrk[512];

	memcpy(&pMainSrv->m_StatusTask[0].bTaskName,"MONITOR   ",sizeof(pMainSrv->m_StatusTask[0].bTaskName));

	wsprintf(bufwrk,"Task %s Iniciada.\r\n",pMainSrv->pMonitor->m_szTaskName);
	pMainSrv->pInitSrv->MsgToLog(EVENTLOG_INFORMATION_TYPE,EVMSG_MONITOR, bufwrk);

	pMainSrv->pMonitor->RunMonitor(pMainSrv);	// roda a task de monitora��o

	pMainSrv->pMonitor->m_dwThreadId = NULL;

	wsprintf(bufwrk,"Task %s terminada.\r\n",pMainSrv->pMonitor->m_szTaskName);
	pMainSrv->pInitSrv->MsgToLog(EVENTLOG_WARNING_TYPE,EVMSG_MONITOR, bufwrk);

	SetEvent(pMainSrv->m_hEvent[MAIN_EVENT_MONITOR_STOP]);
	return 0;
}

CMonitor::CMonitor()
{
	DWORD i;
	SrvSock = INVALID_SOCKET;
	iqtdsock		= 0;
	indexCli		= 0;

	wsprintf(m_szTaskName,"Monitor   (BCSrvSqlMQ)");
	m_lpTaskName = (LPTSTR) &m_szTaskName;

    for( i = 0; i < (QTD_MONI_EVENTS - EVENT_CLITCP); ++i )
	{
		CliSock[i]	= INVALID_SOCKET;
	}

	m_hEvent[0] = CreateWaitableTimer(NULL, FALSE, NULL);	

	for( i = 1; i < QTD_MONI_EVENTS; ++i )
 		m_hEvent[i]	= CreateEvent(NULL,TRUE,FALSE,NULL);
}

CMonitor::~CMonitor()
{
	DWORD i;

    for( i = 0; i < QTD_MONI_EVENTS; ++i )
 		CloseHandle(m_hEvent[i]);

}

void CMonitor::RunMonitor(LPVOID MainSrv)
{
	DWORD dwWait;
	isBusy = true;

	pMainSrv  = static_cast<CMainSrv*>(MainSrv);
	// Modernização C++20: .get() para obter raw pointer de std::unique_ptr
	m_list = pMainSrv->m_MonitorList.get();

	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8014,FALSE,&m_lpTaskName,NULL,NULL,NULL,NULL);

//	hCmdMutex	= CreateMutex(NULL,FALSE,"CmdRec Aloca/Desaloca DataServer");

 	pDueTime.LowPart	= (unsigned long) -1;   
	pDueTime.HighPart	= (unsigned long) -1;				
    lPeriod = 1000;							// de 1 em 1 segundos			

	if (!SetWaitableTimer(m_hEvent[MONI_EVENT_TIMER], &pDueTime, lPeriod, NULL, NULL, FALSE))
	{
		int err = GetLastError();
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8017,FALSE,&err,NULL,NULL,NULL,NULL);
	} 

	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8015,FALSE,NULL,NULL,NULL,NULL,NULL);

	while (isBusy)
	{
		dwWait = WSAWaitForMultipleEvents(QTD_MONI_EVENTS,m_hEvent,FALSE,WSA_INFINITE,TRUE);
		if ( dwWait ==  WAIT_FAILED)
		{
			int err = GetLastError();
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8010,FALSE,&err,NULL,NULL,NULL,NULL);
			isBusy = false;
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8050,FALSE,&m_lpTaskName,NULL,NULL,NULL,NULL);
			return;
		}

		switch (dwWait)
		{

			case MONI_EVENT_TIMER:
				ResetEvent(m_hEvent[dwWait]);
				CheckTimeout();
				if (SrvSock == INVALID_SOCKET)
				{
					InitSrvSocket();
				}
				break;

			case MONI_EVENT_TCP:
				if (WSAEnumNetworkEvents (SrvSock, m_hEvent[MONI_EVENT_TCP], &m_TcpEvents) == SOCKET_ERROR)
				{
					ResetEvent(m_hEvent[dwWait]);
					if (WSAGetLastError() == 10038)
						break;
					int err = WSAGetLastError();
					ResetEvent(m_hEvent[dwWait]);
					pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8051,FALSE,&err,NULL,NULL,NULL,NULL);
					break;
				}

				if ((m_TcpEvents.lNetworkEvents & FD_ACCEPT) == FD_ACCEPT)
				{
					AceitaConexao(m_TcpEvents.iErrorCode[FD_ACCEPT_BIT]);
				}
				break;

			case MONI_EVENT_STOP:
				ResetEvent(m_hEvent[dwWait]);
				isBusy = false;
				break;

			case MONI_EVENT_QUEUE:
				ResetEvent(m_hEvent[dwWait]);
				ProcessaQueue();
				break;

			default:
				indexCli = dwWait - EVENT_CLITCP;
				if (WSAEnumNetworkEvents (CliSock[indexCli], m_hEvent[dwWait], &m_TcpEvents) == SOCKET_ERROR)
				{
					ResetEvent(m_hEvent[dwWait]);
					if (WSAGetLastError() == 10038)
						break;
					int err = WSAGetLastError();
					pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8051,FALSE,&err,NULL,NULL,NULL,NULL);
					break;
				}

				if ((m_TcpEvents.lNetworkEvents & FD_READ) == FD_READ)
				{
					RecebeDadosCli(m_TcpEvents.iErrorCode[FD_READ_BIT],indexCli);
					break;
				}

				if ((m_TcpEvents.lNetworkEvents & FD_CLOSE) == FD_CLOSE)
				{
					ResetEvent(m_hEvent[dwWait]);
					CClientItem*	pCurrCLI = NULL;
					pCurrCLI = pMainSrv->m_ClientList->LocateSock(CliSock[indexCli]);
					if (pCurrCLI != NULL)
					{
						pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8052,TRUE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
						ForceCloseCli(pCurrCLI);
					}
				}

				break;
		}

	}

	if (pMainSrv->pInitSrv->m_bIsShutDownNow == TRUE)
		return;

	CClientItem* pCurrCLI;

	while (pMainSrv->m_ClientList->GetSize())
	{
		pCurrCLI = NULL;
		pCurrCLI = (CClientItem*) pMainSrv->m_ClientList->GetFirst();
		pMainSrv->m_ClientList->RemoveAt(0);
		if (pCurrCLI != NULL)
		{
			if (pCurrCLI->m_IsActive  == true)
			{
				ForceCloseCli(pCurrCLI);
			}
		}
	}

	CancelWaitableTimer(m_hEvent[MONI_EVENT_TIMER]);

	WSAEventSelect(SrvSock,m_hEvent[MONI_EVENT_TCP],0);
	shutdown(SrvSock, SD_BOTH);
	closesocket(SrvSock);
	SrvSock = INVALID_SOCKET;
	

//	CloseHandle( hCmdMutex );
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8012,FALSE,&m_lpTaskName,NULL,NULL,NULL,NULL);
	return;
}




void CMonitor::InitSrvSocket()
{

	SrvSock = socket(AF_INET, SOCK_STREAM, 0);

    if(SrvSock == INVALID_SOCKET)
	{
		int err = WSAGetLastError();
		CString Servico;
		Servico = "BCSrvSqlMQ";
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8053,FALSE,&Servico,&err,NULL,NULL,NULL);
		return;
	}
    
	SrvAddrTcp.sin_addr.s_addr = INADDR_ANY;
	SrvAddrTcp.sin_family = AF_INET;
	SrvAddrTcp.sin_port = htons(pMainSrv->BCSrvSqlMQPort);

	memset(szSrvHumano,0x00,sizeof(szSrvHumano));
	memset(szSrvPorta,0x00,sizeof(szSrvPorta));

	char * TempHostAddr = inet_ntoa (SrvAddrTcp.sin_addr);
	if (TempHostAddr != NULL)
	{
		strcpy(szSrvHumano,TempHostAddr);
	}

	UINT porta = ntohs(SrvAddrTcp.sin_port);
	_itoa(porta,szSrvPorta,10);

    if (bind(SrvSock, (SOCKADDR *)&SrvAddrTcp, sizeof(SrvAddrTcp)) == INVALID_SOCKET)
	{
		int err = WSAGetLastError();
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8054,FALSE,&err,NULL,NULL,NULL,NULL);
		closesocket(SrvSock);
		SrvSock = INVALID_SOCKET;
		return;
	}

	if (WSAEventSelect(SrvSock,m_hEvent[MONI_EVENT_TCP],FD_ACCEPT ) == SOCKET_ERROR)
	{
		int err = WSAGetLastError();
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8055,FALSE,&err,NULL,NULL,NULL,NULL);
		closesocket(SrvSock);
		SrvSock = INVALID_SOCKET;
		return;
	}

	if (listen(SrvSock,37) == SOCKET_ERROR)
	{
		int err = WSAGetLastError();
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8056,FALSE,&err,NULL,NULL,NULL,NULL);
		WSAEventSelect(SrvSock,m_hEvent[MONI_EVENT_TCP],0);
		closesocket(SrvSock);
		SrvSock = INVALID_SOCKET;
		return;
	}
}

void CMonitor::AceitaConexao(int ErrorCode)
{
	int		len;
	char    CliHumano[16];
	int		i;
	UINT    porta;
	char    szPorta[10];

	len = sizeof(CliAddrTcp);

	tCliSock = accept(SrvSock,(SOCKADDR *)&CliAddrTcp,&len);

	if (tCliSock == INVALID_SOCKET)
	{
		int err = WSAGetLastError();
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8057,FALSE,&err,&ErrorCode,NULL,NULL,NULL);
		return;
	}
	if (iqtdsock >= (QTD_MONI_EVENTS - EVENT_CLITCP))
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8058,FALSE,NULL,NULL,NULL,NULL,NULL);
		closesocket(tCliSock);
		return;
	}

	indexCli = -1;

	for (i=0; i < (QTD_MONI_EVENTS - EVENT_CLITCP);i++)
	{
		if (CliSock[i] == INVALID_SOCKET)
		{
			indexCli = i;
			iqtdsock++;
			break;
		}
	}

	if (indexCli == -1)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8058,FALSE,NULL,NULL,NULL,NULL,NULL);
		closesocket(tCliSock);
		return;
	}

	CliSock[indexCli] = tCliSock;

	if (WSAEventSelect(CliSock[indexCli],m_hEvent[indexCli+EVENT_CLITCP], FD_READ | FD_CLOSE) == SOCKET_ERROR)
	{
		int err = WSAGetLastError();
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8055,FALSE,&err,NULL,NULL,NULL,NULL);
		closesocket(CliSock[indexCli]);
		CliSock[indexCli] = INVALID_SOCKET;
		return;
	}

	CliHumano[0] = 0;

	char * TempHostAddr = inet_ntoa (CliAddrTcp.sin_addr);
	if (TempHostAddr == NULL)
	{
		int err = WSAGetLastError();
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8059,FALSE,&err,NULL,NULL,NULL,NULL);
		closesocket(CliSock[indexCli]);
		CliSock[indexCli] = INVALID_SOCKET;
		return;
	}

	strcpy(CliHumano,TempHostAddr);

	porta = ntohs(CliAddrTcp.sin_port);
	_itoa(porta,szPorta,10);

	// Modernização Fase 5: auto keyword + reinterpret_cast
	auto* WrkItem = new CClientItem(reinterpret_cast<char*>(&CliHumano), reinterpret_cast<char*>(&szPorta));

	WrkItem->Lock();
	WrkItem->m_index = indexCli;
	WrkItem->m_Sock = CliSock[indexCli];
	CopyMemory(reinterpret_cast<char*>(&WrkItem->m_AddrCli), &CliAddrTcp, sizeof(SOCKADDR_IN));
	WrkItem->m_status = ST_CLI_CONNECT;
	WrkItem->m_timeout = pMainSrv->pInitSrv->m_SrvTimeout;
	WrkItem->Unlock();
	pMainSrv->m_ClientList->Add(WrkItem);

	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8032,TRUE,&WrkItem->m_lpCliHumano,&WrkItem->m_lpszPorta,&WrkItem->m_Sock,NULL,NULL);

}

void CMonitor::RecebeDadosCli(int ErrorCode, int CurrCli)
{
	int		rc;
	bool	firstrec;

	CClientItem*	pCurrCLI = NULL;

	if (CliSock[CurrCli] == INVALID_SOCKET)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8033,FALSE,&CliSock[CurrCli],NULL,NULL,NULL,NULL);
		return;
	}

	pCurrCLI = pMainSrv->m_ClientList->LocateSock(CliSock[CurrCli]);
			
	if (!pCurrCLI)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8034,FALSE,&CliSock[CurrCli],NULL,NULL,NULL,NULL);
		return;
	}


RecebePrimeiro:

	totJarec = 0;
	totArec	 = 0;
	faltaArec = MAXMSGLENGTH;
	firstrec = true;

	pCurrCLI->Lock();
	qtdRecNow = recv(CliSock[CurrCli],(char*)(pCurrCLI->dadosin.get()), MINMSGLENGTH,0);
	pCurrCLI->m_status = ST_CLI_CONSULTA;
	pCurrCLI->Unlock();
	goto RecebeuDados;

RecebeMais:

	pCurrCLI->Lock();
	qtdRecNow = recv(CliSock[CurrCli],(char*)(pCurrCLI->dadosin.get()) + totJarec, faltaArec,0);
	pCurrCLI->Unlock();

RecebeuDados:

	if (qtdRecNow == SOCKET_ERROR)
	{	
		rc = WSAGetLastError();

		if (rc == WSAEWOULDBLOCK)  // nao tem mais dados;
		{
			if (totArec != 0)
			{
				Sleep(20);
				goto RecebeMais;
			}
			return;
		}

		if (rc == WSAECONNRESET)	//CLIENTE DESCONECTOU;
		{
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8035,FALSE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
			ForceCloseCli(pCurrCLI);
			return;
		}

		if (rc == WSAEMSGSIZE)	//BUFFER DE RECEPCAO PEQUENO;
		{
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8036,FALSE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
			ForceCloseCli(pCurrCLI);
			return;
		}

		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8037,FALSE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,&rc,NULL,NULL);
		ForceCloseCli(pCurrCLI);
		return;
	}

	if (qtdRecNow == 0)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8038,FALSE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
		ForceCloseCli(pCurrCLI);
		return;
	}

	if (firstrec)
	{
		firstrec = false;
		if (qtdRecNow < 2)		
		{
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8039,FALSE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
			ForceCloseCli(pCurrCLI);
			return;
		}
		totArec = reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.usMsgLength;
	}

	totJarec += qtdRecNow;
	
	if (totArec != totJarec)
	{
		faltaArec = totArec - totJarec;
		goto RecebeMais;
	}

	pCurrCLI->m_timeout = pMainSrv->pInitSrv->m_SrvTimeout;

	ProcessaDadosCli(pCurrCLI);

	goto RecebePrimeiro;

}

void CMonitor::ProcessaDadosCli(CClientItem* pCurrCLI)
{
	CClientItem*	pCurrWrk = NULL;

	pCurrCLI->tamdadosin = totArec;

	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8040,TRUE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
	pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,TRUE,pCurrCLI->tamdadosin,pCurrCLI->dadosin.get());

	if (pCurrCLI->m_IsActive == false)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8041,FALSE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,&pCurrCLI->m_status,NULL,NULL);
		ForceCloseCli(pCurrCLI);
		return;
	}

	if (reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.usMsgLength < MINMSGLENGTH)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8042,FALSE,&reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.usMsgLength,&pCurrCLI->m_lpCliHumano,NULL,NULL,NULL);
		ForceCloseCli(pCurrCLI);
		return;
	}

	if (reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.usMsgLength != reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.usDatLength + sizeof(COMHDR))
	{
		int i1,i2;
		i1 = reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.usMsgLength;
		i2 = reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.usDatLength + sizeof(COMHDR);
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8043,FALSE,&i1,&i2,NULL,NULL,NULL);
		ForceCloseCli(pCurrCLI);
		return;
	}

	switch (reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.ucFuncSgr)
	{
		case FUNC_NOP:
			{
				CString fun("NOP");
				pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8044,TRUE,&fun,NULL,NULL,NULL,NULL);

				pCurrCLI->Lock();
				pCurrCLI->m_timeout = pMainSrv->pInitSrv->m_SrvTimeout;
				pCurrCLI->Unlock();
				return;
			}
		case FUNC_POST:
			{
				CString fun("POST");
				pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8044,TRUE,&fun,NULL,NULL,NULL,NULL);

				pCurrCLI->Lock();
				pCurrCLI->m_timeout = pMainSrv->pInitSrv->m_SrvTimeout;
				pCurrCLI->Unlock();
				pCurrCLI->tamdadosout = pCurrCLI->tamdadosin;
				memcpy((char*)(pCurrCLI->dadosout.get()),(char*)(pCurrCLI->dadosin.get()),pCurrCLI->tamdadosout);

				CThreadMQ* WorkThread;

				int index = pMainSrv->m_TaskList->GetSize();
				reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usRc = 99;
				for (int i = 0;i < index;i++)
				{
					WorkThread = (CThreadMQ *) pMainSrv->m_TaskList->GetAt(i);
					if (WorkThread == NULL)
						continue;

					if (WorkThread->m_ThreadIsRunning)
					{
						CString wrk1;
						CString wrk2;
						wrk1 = WorkThread->m_szQueueName;
						reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->mdata[48] = 0x00; 
						wrk2 = reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->mdata;
						wrk1.TrimRight(" ");
						wrk2.TrimRight(" ");
						if (wrk1.Compare(wrk2) == 0)
						{
							pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8062,TRUE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
							SetEvent(WorkThread->m_hEvent[THREAD_EVENT_POST]);
							reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usRc = 0;
							break;
						}
					}
				}
				SendDadosCli(pCurrCLI);

				return;
			}
//		case FUNC_MONITOR_STATUS:
//			{
//				reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.usRc = 0;
//				CString fun("MONITOR STATUS");
//				pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8044,TRUE,&fun,NULL,NULL,NULL,NULL);
//				
//				int tasknum = reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.InfoArea.TaskNum;
//
//				if (tasknum == 0)
//				{
//					pMainSrv->m_StatusTask[tasknum].iTaskAutomatic = TASK_AUTOMATIC;
//					pMainSrv->m_StatusTask[tasknum].iTaskIsRunning = true;
//					pMainSrv->m_StatusTask[tasknum].bStatusDB	= 	1;			
//					pMainSrv->m_StatusTask[tasknum].bRcLoadRest	= 	0;			
//					pMainSrv->m_StatusTask[tasknum].bRcDelete	= 	0;		
//					pMainSrv->m_StatusTask[tasknum].iQtdClient	=	pMainSrv->m_ClientList->GetSize();		
//					pMainSrv->m_StatusTask[tasknum].iMaxClient	=	pMainSrv->m_ClientList->GetMaxSize();		
//				}
//				else
//				{
//					CThreadApp* WorkThread = NULL;
//
//					int index = pMainSrv->m_TaskList->GetSize();
//
//					for (int i = 0;i < index;i++)
//					{
//						WorkThread = (CThreadApp *) pMainSrv->m_TaskList->GetAt(i);
//						if (WorkThread != NULL)
//						{
//							WorkThread->Lock();
//							if (WorkThread->m_HandleDB == tasknum)
//							{
//								WorkThread->AtualizaStatus();
//								WorkThread->Unlock();
//								break;
//							}
//							WorkThread->Unlock();
//						}
//					}
//				}
//
//				pCurrCLI->Lock();
//				pCurrCLI->m_timeout = pMainSrv->pInitSrv->m_SrvTimeout;
//				pCurrCLI->tamdadosout = sizeof(_MSGHDR) + sizeof(STREGSTATUS);
//				memcpy(pCurrCLI->dadosout, pCurrCLI->dadosin, sizeof(_MSGHDR));
//				reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usMsgLength = pCurrCLI->tamdadosout;
//				reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usRc = 0;
//				reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usDatLength = sizeof(STREGSTATUS);  
//				pCurrCLI->dadosout->mststatus.iIsSyncLog = pMainSrv->m_IsSyncLog;
//				pCurrCLI->dadosout->mststatus.lUltNsu = pMainSrv->m_ultnsu;
//				pCurrCLI->dadosout->mststatus.liSynFileTime.QuadPart = pMainSrv->m_SynFileTime.QuadPart;
//				pCurrCLI->dadosout->mststatus.liSynDistance.QuadPart = pMainSrv->m_SynDistance.QuadPart;
//				pCurrCLI->dadosout->mststatus.liLogFileTime.QuadPart = pMainSrv->m_LogFileTime.QuadPart;
//				pCurrCLI->dadosout->mststatus.liLogDistance.QuadPart = pMainSrv->m_LogDistance.QuadPart;
//				pCurrCLI->dadosout->mststatus.iTask_Count = TASKS_COUNT;
//				pCurrCLI->dadosout->mststatus.bTaskNum = tasknum;
//				memcpy(&pCurrCLI->dadosout->mststatus.bTaskName,&pMainSrv->m_StatusTask[tasknum].bTaskName,sizeof(pCurrCLI->dadosout->mststatus.bTaskName));
//				pCurrCLI->dadosout->mststatus.iTaskAutomatic = pMainSrv->m_StatusTask[tasknum].iTaskAutomatic;
//				pCurrCLI->dadosout->mststatus.iTaskIsRunning = pMainSrv->m_StatusTask[tasknum].iTaskIsRunning;
//				memcpy(&pCurrCLI->dadosout->mststatus.bNomaArq,&pMainSrv->m_StatusTask[tasknum].bNomaArq,sizeof(pCurrCLI->dadosout->mststatus.bNomaArq));
//				memcpy(&pCurrCLI->dadosout->mststatus.bLengthArq,&pMainSrv->m_StatusTask[tasknum].bLengthArq,sizeof(pCurrCLI->dadosout->mststatus.bLengthArq));
//				memcpy(&pCurrCLI->dadosout->mststatus.bTableDb,&pMainSrv->m_StatusTask[tasknum].bTableDb,sizeof(pCurrCLI->dadosout->mststatus.bTableDb));
//				pCurrCLI->dadosout->mststatus.bStatusDB		= pMainSrv->m_StatusTask[tasknum].bStatusDB;
//				pCurrCLI->dadosout->mststatus.bRcLoadRest	= pMainSrv->m_StatusTask[tasknum].bRcLoadRest;
//				pCurrCLI->dadosout->mststatus.bRcDelete		= pMainSrv->m_StatusTask[tasknum].bRcDelete;
//				pCurrCLI->dadosout->mststatus.iQtdClient	= pMainSrv->m_StatusTask[tasknum].iQtdClient;
//				pCurrCLI->dadosout->mststatus.iMaxClient	= pMainSrv->m_StatusTask[tasknum].iMaxClient;
//				pCurrCLI->Unlock();
//				SendDadosCli(pCurrCLI);
//				return;
//			}
//			break;
		default:
			break;
	}

	pCurrCLI->Lock();
	pCurrCLI->m_timeout = pMainSrv->pInitSrv->m_SrvTimeout;
	pCurrCLI->Unlock();

//	CProcessoId*	pCurrPro = NULL;

//	switch (reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.InfoArea.HandleDB)
//	{
//	case TASKS_BACENREQ:
//		{
//			CThreadApp* task = (CThreadApp*) pMainSrv->m_TaskList->GetAt(pMainSrv->m_TaskCtlDB);
//			pCurrPro = pMainSrv->m_CtlRltId->LocateOriginId(pCurrCLI, (BYTE *) &reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.ucOriginId);
//			if (pCurrPro == NULL)
//			{
//				pCurrPro = new CProcessoId(reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.InfoArea.HandleDB, pCurrCLI, (BYTE *) &reinterpret_cast<LPMIMSG>(pCurrCLI->dadosin.get())->hdr.ucOriginId);
//				task->Lock();
//				pMainSrv->m_CtlRltId->Add(pCurrPro);
//				task->Unlock();
//				pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8579,TRUE,&pCurrPro->m_lpCliHumano,&pCurrPro->m_lpszPorta,&pCurrPro->m_OriginId,NULL,NULL);
//			}
//			else
//			{
//				pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8580,TRUE,&pCurrPro->m_lpCliHumano,&pCurrPro->m_lpszPorta,&pCurrPro->m_OriginId,NULL,NULL);
//			}
//			pCurrCLI->Lock();
//			pCurrPro->Lock();
//			pCurrPro->m_timeout = pMainSrv->pInitSrv->m_TimeoutPro;
//			pCurrPro->m_queue = true;
//			pCurrPro->tamdadosin = pCurrCLI->tamdadosin;
//			memcpy((char *) pCurrPro->dadosin.get(),(char*)(pCurrCLI->dadosin.get()),pCurrPro->tamdadosin);
//			pCurrPro->Unlock();
//			pCurrCLI->Unlock();
//			task->Lock();
//			pMainSrv->m_CtlRltList->Add(pCurrPro);
//			task->Unlock();
//			if (task != NULL)
//			{
//				pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8557,TRUE,(char *) &pMainSrv->m_CtlRltList->m_lpszName,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL);
//				SetEvent(task->m_hEvent[THREAD_EVENT_QUEUE]);
//			}
//		}
//		break;
//	default:
//		{
//			pCurrCLI->Lock();
//			pCurrCLI->m_timeout = pMainSrv->pInitSrv->m_SrvTimeout;
//			pCurrCLI->tamdadosout = sizeof(_MSGHDR);
//			memcpy(pCurrCLI->dadosout, pCurrCLI->dadosin, pCurrCLI->tamdadosout);
//			reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usMsgLength = pCurrCLI->tamdadosout;
//			reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usRc = 15;
//			reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usDatLength = 0;  
//			pCurrCLI->Unlock();
//			SendDadosCli(pCurrCLI);
//			return;
//		}
//	}

}

void CMonitor::ProcessaQueue()
{
//	CProcessoId*	pCurrPro = NULL;
//	CClientItem*    pCliWrk = NULL;

//	while (m_list->GetSize())
//	{
//		pCurrPro = (CProcessoId*)m_list->GetFirst(); 
//		m_list->RemoveAt(0);
//		if (pCurrPro != NULL)
//		{
//			pCurrPro->Lock();
//			if (pCurrPro->m_IsActive)
//			{
//				pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8577,TRUE,&pCurrPro->m_lpCliHumano,&pCurrPro->m_lpszPorta,&pCurrPro->m_OriginId,NULL,NULL);
//				pCliWrk = pMainSrv->m_ClientList->LocateSockAddr((char *) &pCurrPro->m_AddrCli); 
//				if (pCliWrk != NULL) 
//				{
//					pCliWrk->Lock();
//					pCliWrk->m_LastTask = pCurrPro->m_LastTask;	
//					pCurrPro->m_timeout = pMainSrv->pInitSrv->m_TimeoutPro;
//					pCliWrk->m_timeout  = pMainSrv->pInitSrv->m_SrvTimeout;
//					pCliWrk->tamdadosout = pCurrPro->tamdadosout;
//					memcpy((char *) pCliWrk->dadosout,(char *) pCurrPro->dadosout.get(),pCliWrk->tamdadosout);
//					pCliWrk->Unlock();
//					SendDadosCli(pCliWrk);
//				}
//				else
//				{
//					int cliseq = reinterpret_cast<LPMIMSG>(pCurrPro->dadosin.get())->hdr.usSequence;
//					pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,FALSE,sizeof(pCurrPro->m_AddrCli),(char *) &pCurrPro->m_AddrCli);
//					pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8568,FALSE,&cliseq,&pCurrPro->m_lpCliHumano,&pCurrPro->m_lpszPorta,NULL,NULL);
//					pMainSrv->m_ClientList->DepuraSockAddr(pMainSrv, m_szTaskName); 
//				}
//			}
//			else
//			{
//				pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8591,TRUE,&pCurrPro->m_lpCliHumano,&pCurrPro->m_lpszPorta,NULL,NULL,NULL);
//				int cliseq = reinterpret_cast<LPMIMSG>(pCurrPro->dadosin.get())->hdr.usSequence;
//				pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8558,TRUE,&cliseq,&pCurrPro->m_lpCliHumano,&pCurrPro->m_lpszPorta,NULL,NULL);
//			}
//			pCurrPro->m_queue = false;
//			pCurrPro->Unlock();
//		}
//		else
//		{
//			int cliseq = reinterpret_cast<LPMIMSG>(pCurrPro->dadosin.get())->hdr.usSequence;
//			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8568,FALSE,&cliseq,&pCurrPro->m_lpCliHumano,&pCurrPro->m_lpszPorta,NULL,NULL);
//		}
//	}
}

bool CMonitor::SendDadosCli(CClientItem* pCurrCLI)
{
	int		rc;
	int		i1,i2;

	if (pCurrCLI->m_IsActive == false)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8041,FALSE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,&pCurrCLI->m_status,NULL,NULL);
		return false;
	}


//---------------------------------
//			int cliseq = reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usSequence;
//			char buftst[50];
//			sprintf(buftst,"sndMon  seq=%d tamenv=%d.",cliseq,pCurrCLI->tamdadosout);
//			pMainSrv->pInitSrv->MsgToLog(EVENTLOG_INFORMATION_TYPE,EVMSG_MAIN,buftst);
//----------------------------------


	if (reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usMsgLength != pCurrCLI->tamdadosout)
	{
		i1 = reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usMsgLength;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8060,FALSE,&pCurrCLI->tamdadosout,&i1,NULL,NULL,NULL);
	}

	if (reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usMsgLength != reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usDatLength + sizeof(COMHDR))
	{
		i1 = reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usMsgLength;
		i2 = reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usDatLength + sizeof(COMHDR);
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8045,FALSE,&i1,&i2,NULL,NULL,NULL);
	}

	pCurrCLI->Lock();

	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8046,TRUE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
	pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,TRUE,pCurrCLI->tamdadosout,pCurrCLI->dadosout.get());

	pCurrCLI->Unlock();

SendDeNovo:
	pCurrCLI->Lock();
	rc = send(CliSock[pCurrCLI->m_index],(char*)(pCurrCLI->dadosout.get()),pCurrCLI->tamdadosout,0);
	pCurrCLI->m_timeout = pMainSrv->pInitSrv->m_SrvTimeout;
	pCurrCLI->Unlock();

	if (rc == SOCKET_ERROR)
	{	
		if (WSAGetLastError() == 10035)	// recurso temporariamente indisponivel ?
		{
			Sleep(20);
			goto SendDeNovo;
		}
		int err = WSAGetLastError();
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8047,FALSE,&err,&CliSock[pCurrCLI->m_index],NULL,NULL,NULL);
		ForceCloseCli(pCurrCLI);
		return false;
	}

//---------------------------------
//			cliseq = reinterpret_cast<LPMIMSG>(pCurrCLI->dadosout.get())->hdr.usSequence;
//			char buftst[50];
//			sprintf(buftst,"msgsend  seq=%d socket=%d tamenv=%d tamreg=%d.",cliseq,CliSock[pCurrCLI->m_index],rc,pCurrCLI->tamdadosout);
//			pMainSrv->pInitSrv->MsgToLog(EVENTLOG_INFORMATION_TYPE,EVMSG_MAIN,buftst);
//----------------------------------
	
	return true;
}

void CMonitor::ForceCloseCli(CClientItem* pCurrCLI)
{
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8048,TRUE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
	pCurrCLI->Lock();
	pMainSrv->m_ClientList->RemoveSock(pCurrCLI->m_Sock);
	pCurrCLI->m_IsActive  = false;
	WSAEventSelect(pCurrCLI->m_Sock,m_hEvent[pCurrCLI->m_index+EVENT_CLITCP],0);
	shutdown(pCurrCLI->m_Sock,SD_BOTH);
	closesocket(pCurrCLI->m_Sock);
	CliSock[pCurrCLI->m_index] = INVALID_SOCKET;
	pCurrCLI->m_Sock = INVALID_SOCKET;
	pCurrCLI->m_status = ST_CLI_DISCONNECT;
	pCurrCLI->Unlock();
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8049,TRUE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
	delete pCurrCLI;
	iqtdsock--;
}

void CMonitor::CheckTimeout()
{
	int i = 0;

	CClientItem* pCurrCLI = NULL;
	i = pMainSrv->m_ClientList->GetSize();

	while (i-- > 0)
	{
		pCurrCLI = (CClientItem*) pMainSrv->m_ClientList->GetAt(i); 
		if (pCurrCLI != NULL)
		{
			if (pCurrCLI->m_IsActive  == true)
			{
				pCurrCLI->Lock();
				pCurrCLI->m_timeout -= 1;
				pCurrCLI->Unlock();
				if (pCurrCLI->m_timeout <= 0)
				{
					pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8593,FALSE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
					ForceCloseCli(pCurrCLI);
				}
				else
				{
					if (pCurrCLI->m_ForceCli  == true)
					{
						pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8620,FALSE,&pCurrCLI->m_lpCliHumano,&pCurrCLI->m_lpszPorta,NULL,NULL,NULL);
						ForceCloseCli(pCurrCLI);
					}
				}
			}
		}
	}
}


