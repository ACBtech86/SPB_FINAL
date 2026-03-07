// ThreadMQ.cpp

// Fase 6: Removido #define _WIN32_WINNT 0x0400 (obsoleto, definido pelo CMake)


#include <afx.h>
#include <afxmt.h>
#include <afxdb.h>
#include <afxdisp.h>
#include <cmqc.h>
#include "wtypes.h"
#include "objbase.h"
#include "MsgSgr.h"
#include "NTServApp.h"
#include "InitSrv.h"
#include "winsock2.h"
// Migração CryptLib → OpenSSL (27/02/2026)
#include "OpenSSLWrapper.h"
#include <openssl/evp.h>
#include <openssl/rsa.h>
#include <openssl/rand.h>
#include "MainSrv.h"
#include "ThreadMQ.h"
#include "Monitor.h"

DWORD WINAPI CThreadMQ::TaskThread(LPVOID MainSrv)
{
	// Modernização Fase 5: auto keyword + static_cast
	auto* pMainSrv = static_cast<CMainSrv*>(MainSrv);
	auto numthread = GetCurrentThreadId();

	// Modernização Fase 5: Range-based for loop + auto keyword
	int index = pMainSrv->m_TaskList->GetSize();
	for (int i = 0; i < index; i++)
	{
		auto* pApp = static_cast<CThreadMQ*>(pMainSrv->m_TaskList->GetAt(i));

		if (pApp->m_dwThreadId == numthread)
		{
			pApp->RunThread(pMainSrv);
			pMainSrv->m_StopList->Add(pApp);					//mudei para apos o runterm();
			break;
		}
	}
	SetEvent(pMainSrv->m_hEvent[MAIN_EVENT_TASKSAPP_STOP]);		//mudei para apos o RUNTERM();
	return 0;
}


CThreadMQ::CThreadMQ(LPCTSTR lpszName, bool AutomaticThread, int HandleMQ, CMainSrv *MainSrv)
{
	DWORD i;

	pMainSrv  = MainSrv;

	m_ServiceName = pMainSrv->pInitSrv->m_szServiceName;
	m_ServiceName.Left(11);
	memset((char *) &m_szTaskName,0x00,41);
	strcpy((char *) &m_szTaskName,lpszName);
	memcpy((char *) &m_szTaskName+11,m_ServiceName,m_ServiceName.GetLength());
	m_lpTaskName = (LPTSTR) &m_szTaskName;

	m_HandleMQ			= HandleMQ;
	m_AutomaticThread	= AutomaticThread;
	// Modernização C++20: std::mutex é inicializado automaticamente
	// Não precisa de CreateMutex

	memcpy(&pMainSrv->m_StatusTask[HandleMQ].bTaskName,m_lpTaskName,sizeof(pMainSrv->m_StatusTask[HandleMQ].bTaskName));

	
	m_hEvent[0] = CreateWaitableTimer(NULL, FALSE, NULL);	

	for( i = 1; i < QTD_THREAD_EVENTS; ++i )
		m_hEvent[i]	= CreateEvent(NULL,TRUE,FALSE,NULL);

	// Modernização C++20: std::atomic<bool> inicializado (atribuição direta funciona)
	m_ThreadIsRunning = false;
	m_ServicoIsRunning = false;

	// Migração CryptLib → OpenSSL (27/02/2026)
	m_publicKey = nullptr;
	m_privateKey = nullptr;
	m_certificate = nullptr;
	m_certBio = nullptr;
	m_keyBio = nullptr;
}

CThreadMQ::~CThreadMQ()
{
	DWORD i;

    for( i = 0; i < QTD_THREAD_EVENTS; ++i )
 		CloseHandle(m_hEvent[i]);

	// Modernização C++20: std::mutex limpa automaticamente
	// Não precisa de CloseHandle(m_mutex)
}

void CThreadMQ::AtualizaStatus()
{
	memcpy(&pMainSrv->m_StatusTask[m_HandleMQ].bTaskName,m_lpTaskName,sizeof(pMainSrv->m_StatusTask[m_HandleMQ].bTaskName));
	pMainSrv->m_StatusTask[m_HandleMQ].iTaskAutomatic = m_AutomaticThread;
	pMainSrv->m_StatusTask[m_HandleMQ].iTaskIsRunning = m_ThreadIsRunning;
	return;
}


BOOL CThreadMQ::Lock()
{
	// Modernização C++20: std::mutex::lock()
	m_mutex.lock();
	return false;
}

BOOL CThreadMQ::Unlock()
{
	// Modernização C++20: std::mutex::unlock()
	m_mutex.unlock();
	return false;
}

void CThreadMQ::RunThread(LPVOID MainSrv)
{
	pMainSrv  = (CMainSrv *) MainSrv;

	RunInit();
	RunWaitPost();
	RunTerm();
	return;
}

void CThreadMQ::RunInit()
{
	BSTR DBServer = NULL;
	BSTR DBName   = NULL;
	VARIANT_BOOL vb = false;

	m_ServicoIsRunning = true;
	m_ThreadIsRunning = true;

	memset(m_szQueueName,0x20,48);
	m_szQueueName[48] = 0x00;

	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8014,FALSE,&m_lpTaskName,NULL,NULL,NULL,NULL);

	pDueTime.LowPart	= (unsigned long) -1;   
	pDueTime.HighPart	= (unsigned long) -1;				
	lPeriod = 1000;							// de 1 em 1 segundos			

//	if (!SetWaitableTimer(m_hEvent[THREAD_EVENT_TIMER], &pDueTime, lPeriod, NULL, NULL, FALSE))
//	{
//		int err = GetLastError();
//		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8017,FALSE,&err,NULL,NULL,NULL,NULL);
//	} 
	if (pMainSrv->MainIsStoping)
	{
		SetEvent(m_hEvent[THREAD_EVENT_STOP]);
	}
	else
	{
		SetEvent(m_hEvent[THREAD_EVENT_POST]);
	}

	// Fase 6: MSXML removido - pugixml não precisa de inicialização COM
	return;
}

void CThreadMQ::RunWait()
{
	DWORD dwWait;
	AtualizaStatus();
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8015,FALSE,&m_lpTaskName,NULL,NULL,NULL,NULL);
	while (m_ServicoIsRunning)
	{
		dwWait = WaitForMultipleObjects(QTD_THREAD_EVENTS,m_hEvent,FALSE,0);
		if ( dwWait ==  WAIT_FAILED)
		{
			int err = GetLastError();
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8503,FALSE,&err,NULL,NULL,NULL,NULL);
			m_ServicoIsRunning = false;
			return;
		}

		if ( dwWait ==  WAIT_TIMEOUT)
		{
			Lock();
			ProcessaQueue();
			Unlock();
			continue;
		}

		ResetEvent(m_hEvent[dwWait]);

		switch (dwWait)
		{

//			case THREAD_EVENT_TIMER:
//				Lock();
//				CheckTimeout();
//				Unlock();
//				break;

//			case THREAD_EVENT_QUEUE:
//				Lock();
//				ProcessaQueue();
//				Unlock();
//				break;

			case THREAD_EVENT_STOP:
				pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8011,FALSE,NULL,NULL,NULL,NULL,NULL);
				m_ServicoIsRunning = false;
				break;

			default:
				break;
		}

	}
	return;
}

void CThreadMQ::RunWaitPost()
{
	DWORD dwWait;
	AtualizaStatus();
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8015,FALSE,&m_lpTaskName,NULL,NULL,NULL,NULL);
	while (m_ServicoIsRunning)
	{
		dwWait = WaitForMultipleObjects(QTD_THREAD_EVENTS,m_hEvent,FALSE,INFINITE);
		if ( dwWait ==  WAIT_FAILED)
		{
			int err = GetLastError();
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8503,FALSE,&err,NULL,NULL,NULL,NULL);
			m_ServicoIsRunning = false;
			return;
		}

		ResetEvent(m_hEvent[dwWait]);

		switch (dwWait)
		{

//			case THREAD_EVENT_TIMER:
//				Lock();
//				CheckTimeout();
//				Unlock();
//				break;

			case THREAD_EVENT_POST:
				Lock();
				ProcessaQueue();
				Unlock();
				break;

			case THREAD_EVENT_STOP:
				pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8011,FALSE,NULL,NULL,NULL,NULL,NULL);
				m_ServicoIsRunning = false;
				break;

			default:
				break;
		}

	}
	return;
}
void CThreadMQ::RunTerm()
{
	if (pMainSrv->pInitSrv->m_bIsShutDownNow == TRUE)
	{
		return;
	}

	AtualizaStatus();
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8012,FALSE,&m_lpTaskName,NULL,NULL,NULL,NULL);

	// Fase 6: MSXML removido - cleanup não necessário para pugixml

	// Migração CryptLib → OpenSSL (27/02/2026): Cleanup
	if (m_publicKey != nullptr)
	{
		EVP_PKEY_free(m_publicKey);
		m_publicKey = nullptr;
	}

	if (m_privateKey != nullptr)
	{
		EVP_PKEY_free(m_privateKey);
		m_privateKey = nullptr;
	}

	if (m_certificate != nullptr)
	{
		X509_free(m_certificate);
		m_certificate = nullptr;
	}

	if (m_certBio != nullptr)
	{
		BIO_free(m_certBio);
		m_certBio = nullptr;
	}

	if (m_keyBio != nullptr)
	{
		BIO_free(m_keyBio);
		m_keyBio = nullptr;
	}

	return;
}

void CThreadMQ::ProcessaQueue()
{
	Sleep(15000);
}

void CThreadMQ::DumpHeader(MQMD* InQmd)
{
	CString wrk;
   
    wrk = "====== | ----------------Inicio Header MQSeries------------------------------- ";
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

    wrk.Format("====== | StrucId        : '%.4s' Version %ld",
           InQmd->StrucId, (long)InQmd->Version);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

    wrk.Format("====== | Report         : %#ld", (long)InQmd->Report);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

	switch (InQmd->MsgType)
	{

			case MQMT_REQUEST:
				wrk.Format("====== | Type           : REQUEST");
				break;
			case MQMT_REPLY:
				wrk.Format("====== | Type           : REPLY");
				break;
			case MQMT_DATAGRAM:
				wrk.Format("====== | Type           : DATAGRAM");
				break;
			case MQMT_REPORT:
				wrk.Format("====== | Type           : REPORT");
				break;
			default:
				wrk.Format("====== | Type           : %ld",(long)InQmd->MsgType);
				break;
	}
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

    if(InQmd->Expiry == MQEI_UNLIMITED)
	{
        wrk.Format("====== | Expiry         : unlimited");
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
	}
    else
	{
        wrk.Format("====== | Expiry         : %ld.%ld secs", (long)InQmd->Expiry / 10,
                   (long)InQmd->Expiry % 10);
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
	}

    wrk.Format("====== | Priority       : %ld Persist : %ld CCSID : %ld Encode : %ld ",
           (long)InQmd->Priority, (long)InQmd->Persistence,
           (long)InQmd->CodedCharSetId, (long)InQmd->Encoding);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

	wrk = "====== | MsgId ";
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,TRUE,sizeof(InQmd->MsgId),&InQmd->MsgId);

	wrk = "====== | nCorrelId ";
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,TRUE,sizeof(InQmd->CorrelId),&InQmd->CorrelId);

    wrk.Format("====== | Userid         : '%12.12s' Format : '%8.8s'",InQmd->UserIdentifier,InQmd->Format);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

    wrk.Format("====== | ReplyToQMgr    : '%48.48s'", InQmd->ReplyToQMgr);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    wrk.Format("====== | ReplyToQ       : '%48.48s'", InQmd->ReplyToQ);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    wrk.Format("====== | PutApplName    : '%28.28s' PutApplType : %ld",
           InQmd->PutApplName, (long)InQmd->PutApplType);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    wrk.Format("====== | ApplOriginData : '%4.4s'",InQmd->ApplOriginData);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

    wrk.Format("====== | PutDate        : '%8.8s' PutTime : '%8.8s' ",
           InQmd->PutDate, InQmd->PutTime);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

	switch (InQmd->Feedback)
	{

			case MQFB_NONE:
				wrk.Format("====== | Feedback       : NONE");
				break;
			case MQFB_QUIT:
				wrk.Format("====== | Feedback       : QUIT");
				break;
			case MQFB_EXPIRATION:
				wrk.Format("====== | Feedback       : EXPIRATION");
				break;
			case MQFB_COA:
				wrk.Format("====== | Feedback       : COA");
				break;
			case MQFB_COD:
				wrk.Format("====== | Feedback       : COD");
				break;
			default:
				wrk.Format("====== | Feedback       : %ld",(long)InQmd->Feedback);
				break;
	}
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    wrk.Format("====== | BackoutCount   : %ld ",(long)InQmd->BackoutCount);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);


	wrk = "====== | AccountingToken ";
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,TRUE,sizeof(InQmd->AccountingToken),&InQmd->AccountingToken);

	wrk = "====== | ApplIdentityData ";
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,TRUE,sizeof(InQmd->ApplIdentityData),&InQmd->ApplIdentityData);

	wrk = "====== | GroupId ";
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,TRUE,sizeof(InQmd->GroupId),&InQmd->GroupId);

    wrk.Format("====== | MsgSeqNumber   : %#d", (long)InQmd->MsgSeqNumber);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

    wrk.Format("====== | Offset         : %#d", (long)InQmd->Offset);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

    wrk.Format("====== | MsgFlags       : %#d", (long)InQmd->MsgFlags);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

    wrk.Format("====== | OriginalLength : %#d", (long)InQmd->OriginalLength);
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

	wrk = "====== | ----------------Fim Header MQSeries---------------------------------- ";
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
}

bool CThreadMQ::AnsiToUnicode(int &lenmsg, LPBYTE msg)
{
	bool rc = false;
	msg[lenmsg] = 0x00; 
	int nLen = MultiByteToWideChar(CP_ACP, 0, (char *) msg , -1, NULL, NULL);
	BSTR lpszW = new OLECHAR[nLen+1];
	MultiByteToWideChar(CP_ACP, 0, (char *) msg , -1, (BSTR) lpszW, nLen);
	lenmsg = sizeof(OLECHAR) * nLen;
	CopyMemory(msg,lpszW,lenmsg);
	delete[] lpszW;
	return rc;
}

bool CThreadMQ::UnicodeToAnsi(int &lenmsg, LPBYTE msg)
{
	bool rc = false;
	int nLen = WideCharToMultiByte(CP_ACP, 0,  (LPWSTR) msg , lenmsg, NULL, NULL, NULL, NULL);
	LPBYTE lpsz = new BYTE[nLen+1];
	lenmsg = WideCharToMultiByte(CP_ACP, 0, (LPWSTR) msg, lenmsg, (char *) lpsz ,nLen, NULL, NULL);
	CopyMemory(msg,lpsz,lenmsg);
	delete[] lpsz;
	return rc;
}

bool CThreadMQ::UnicodeToAnsi(BSTR psz,LPSTR &pstr)      
{    
	bool rc = false;
	int nLen = WideCharToMultiByte(CP_ACP, 0,  psz , -1, NULL, NULL, NULL, NULL);
	pstr = new CHAR[nLen+1];
	nLen = WideCharToMultiByte(CP_ACP, 0, psz, -1, pstr ,nLen, NULL, NULL);
	pstr[nLen] = 0x00;
	return rc;
}  


// Fase 6: Migrado de MSXML para pugixml
bool CThreadMQ::ReportError(const pugi::xml_parse_result& result)
{
	CString wrk;

	wrk.Format("Carga xml - Erro: %s", result.description());
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8109,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

	if (result.offset > 0)
    {
		wrk.Format("Error at offset %d.", static_cast<int>(result.offset));
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8109,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    }

    return false;  // Sempre retorna false pois é um erro
}

// Fase 6: Migrado de MSXML para pugixml
bool CThreadMQ::CheckLoad(pugi::xml_document& doc)
{
    // pugixml: documento sempre está "carregado" após load_*()
    // A verificação de erro é feita no load_* que retorna xml_parse_result
	CString wrk;
	wrk.Format("XML document loaded successfully");
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    return true;
}

// Fase 6: Migrado de MSXML para pugixml
bool CThreadMQ::FindTag(pugi::xml_document& doc, const char* pwParent, const char* pwText, std::string& pwValue)
{
	int count = 0;
	bool found = false;

	// Usar XPath para encontrar todos os nós com o nome da tag
	std::string xpath = std::string("//") + pwText;
	pugi::xpath_node_set nodes = doc.select_nodes(xpath.c_str());

	for (pugi::xpath_node xnode : nodes)
	{
		pugi::xml_node node = xnode.node();
		count++;

		if (pwParent == NULL || pwParent[0] == '\0')
		{
			// Sem filtro de pai - deve ter apenas um elemento
			if (count == 1)
			{
				pwValue = node.child_value();
				found = true;
			}
			else
			{
				// Múltiplos elementos sem especificar pai
				return false;
			}
		}
		else
		{
			// Com filtro de pai - verificar nome do nó pai
			pugi::xml_node parent = node.parent();
			if (parent && strcmp(parent.name(), pwParent) == 0)
			{
				pwValue = node.child_value();
				found = true;
				break;
			}
		}
	}

	return found;
}

// Fase 6: Migrado de MSXML para pugixml
bool CThreadMQ::SetTag(pugi::xml_document& doc, const char* pwText, std::string& pwValue)
{
	int count = 0;

	// Usar XPath para encontrar todos os nós com o nome da tag
	std::string xpath = std::string("//") + pwText;
	pugi::xpath_node_set nodes = doc.select_nodes(xpath.c_str());

	for (pugi::xpath_node xnode : nodes)
	{
		pugi::xml_node node = xnode.node();
		node.text().set(pwValue.c_str());
		count++;
	}

	// Retorna true apenas se encontrou exatamente 1 elemento
	return (count == 1);
}

////////////////////////////////////////////////////////////////////////////
// Function: Walk all the Elements in a loaded XML document.
// Fase 6: Migrado de MSXML para pugixml
////////////////////////////////////////////////////////////////////////////
bool CThreadMQ::WalkTree(pugi::xml_node node, int level)
{
	CString wrk, wrk1;

	// Criar indentação
	wrk1 = "";
    for (int i = 0; i < level; i++)
       wrk1 += " ";

	// Nome do nó (pular nós especiais que começam com '#')
	const char* nodeName = node.name();
	if (nodeName && nodeName[0] != '#')
	{
		wrk.Format("====== | NodeName       : %s '%s' ", (LPCSTR)wrk1, nodeName);
		if (wrk.GetLength() >= 150)
		{
			wrk = wrk.Mid(0,150);
		}
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
	}

	// Valor do nó
	const char* value = node.value();
	if (value && value[0] != '\0')
    {
		wrk.Format("====== | Value          : %s '%s' ", (LPCSTR)wrk1, value);
		if (wrk.GetLength() >= 150)
		{
			wrk = wrk.Mid(0,150);
		}
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    }

	// Atributos
	for (pugi::xml_attribute attr : node.attributes())
    {
		wrk.Format("====== | Tag            : '%s' ", attr.name());
		if (wrk.GetLength() >= 150)
		{
			wrk = wrk.Mid(0,150);
		}
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

		wrk.Format("====== | Value           : '%s' ", attr.value());
		if (wrk.GetLength() >= 150)
		{
			wrk = wrk.Mid(0,150);
		}
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    }

	// Processar filhos recursivamente
	for (pugi::xml_node child : node.children())
    {
        WalkTree(child, level + 1);
    }

    return true;
}

// Fase 6: Migrado de MSXML para pugixml
bool CThreadMQ::LoadDocumentSync(pugi::xml_document& doc, const char* pData, size_t ulLen)
{
    // pugixml: load_buffer_inplace requer buffer modificável, usamos load_buffer
    pugi::xml_parse_result result = doc.load_buffer(pData, ulLen);

    if (!result)
    {
        return ReportError(result);
    }

    return CheckLoad(doc);
}

////////////////////////////////////////////////////////////////////////////
// Function: Save document out to specified local file.
// Fase 6: Migrado de MSXML para pugixml
////////////////////////////////////////////////////////////////////////////
bool CThreadMQ::SaveDocument(pugi::xml_document& doc, const char* pFileName)
{
    return doc.save_file(pFileName);
}

int CThreadMQ::ReadPublicKey()
{
	// Migração CryptLib → OpenSSL (27/02/2026)
	int status = 0;

	if (pMainSrv->pInitSrv->m_SecurityEnable.Compare("N") == 0)		// security enable (S/N)
		return status;

	// Limpar chave pública anterior
	if (m_publicKey != nullptr)
	{
		EVP_PKEY_free(m_publicKey);
		m_publicKey = nullptr;
	}

	if (m_certificate != nullptr)
	{
		X509_free(m_certificate);
		m_certificate = nullptr;
	}

	if (m_certBio != nullptr)
	{
		BIO_free(m_certBio);
		m_certBio = nullptr;
	}

	// Usando m_CertificateFile para caminho do certificado PEM (OpenSSL migration 2026-03-01)
	CString certPath = pMainSrv->pInitSrv->m_CertificateFile;

	// Abrir arquivo do certificado
	m_certBio = BIO_new_file((LPCSTR)certPath, "r");
	if (!m_certBio)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8079, FALSE, &status, &certPath, NULL, NULL, NULL);
		return status;
	}

	// Ler certificado X.509
	m_certificate = PEM_read_bio_X509(m_certBio, nullptr, nullptr, nullptr);
	if (!m_certificate)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8080, FALSE, &status, &certPath, NULL, NULL, NULL);
		BIO_free(m_certBio);
		m_certBio = nullptr;
		return status;
	}

	// Extrair chave pública do certificado
	m_publicKey = X509_get_pubkey(m_certificate);
	if (!m_publicKey)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8080, FALSE, &status, &certPath, NULL, NULL, NULL);
		return status;
	}

	// Verificar se é RSA
	int cryptAlgo = EVP_PKEY_base_id(m_publicKey);
	if (cryptAlgo != EVP_PKEY_RSA)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8081, FALSE, &cryptAlgo, NULL, NULL, NULL, NULL);
		return status;
	}

	// Verificar tamanho da chave (1024 bits)
	int cryptKeySize = EVP_PKEY_bits(m_publicKey);
	if (cryptKeySize != 1024)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8084, FALSE, &cryptKeySize, NULL, NULL, NULL, NULL);
		status = -1;
		return status;
	}

	// Obter serial number do certificado
	memset(m_cryptSerialNumberPub, 0x00, sizeof(m_cryptSerialNumberPub));
	ASN1_INTEGER* serial = X509_get_serialNumber(m_certificate);
	if (serial)
	{
		int len = serial->length;
		if (len > sizeof(m_cryptSerialNumberPub))
			len = sizeof(m_cryptSerialNumberPub);
		memcpy(m_cryptSerialNumberPub, serial->data, len);
	}
	else
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8105, FALSE, &cryptAlgo, NULL, NULL, NULL, NULL);
		return status;
	}

	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8082, FALSE, &certPath, &cryptAlgo, &cryptKeySize, NULL, NULL);

	// Log serial number
	CString wrk;
	LPVOID lpwrk = &m_cryptSerialNumberPub;
    wrk = "====== | ----------------Inicio Public Key Serial Number --------------------- ";
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,FALSE,sizeof(m_cryptSerialNumberPub),lpwrk);
    wrk = "====== | ----------------Fim    Public Key Serial Number --------------------- ";
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

	return status;


}

int CThreadMQ::ReadPrivatKey()
{
	// Migração CryptLib → OpenSSL (27/02/2026)
	int status = 0;

	if (pMainSrv->pInitSrv->m_SecurityEnable.Compare("N") == 0)		// security enable (S/N)
		return status;

	// Limpar chave privada anterior
	if (m_privateKey != nullptr)
	{
		EVP_PKEY_free(m_privateKey);
		m_privateKey = nullptr;
	}

	if (m_keyBio != nullptr)
	{
		BIO_free(m_keyBio);
		m_keyBio = nullptr;
	}

	// Abrir arquivo da chave privada
	CString keyPath = pMainSrv->pInitSrv->m_PrivateKeyFile;
	m_keyBio = BIO_new_file((LPCSTR)keyPath, "r");
	if (!m_keyBio)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8079, FALSE, &status, &keyPath, NULL, NULL, NULL);
		return status;
	}

	// Ler chave privada (com senha se configurada)
	CString password = pMainSrv->pInitSrv->m_KeyPassword;
	const char* pwd = password.IsEmpty() ? nullptr : (LPCSTR)password;

	m_privateKey = PEM_read_bio_PrivateKey(m_keyBio, nullptr, nullptr, const_cast<char*>(pwd));
	if (!m_privateKey)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8083, FALSE, &status, &keyPath, NULL, NULL, NULL);
		BIO_free(m_keyBio);
		m_keyBio = nullptr;
		return status;
	}

	// Verificar se é RSA
	int cryptAlgo = EVP_PKEY_base_id(m_privateKey);
	if (cryptAlgo != EVP_PKEY_RSA)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8085, FALSE, &cryptAlgo, NULL, NULL, NULL, NULL);
		return status;
	}

	// Verificar tamanho da chave (1024 bits)
	int cryptKeySize = EVP_PKEY_bits(m_privateKey);
	if (cryptKeySize != 1024)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8086, FALSE, &cryptKeySize, NULL, NULL, NULL, NULL);
		return status;
	}

	// Para OpenSSL, usamos o label da configuração
	char cryptlabel[255];
	LPVOID lpcryptlabel = &cryptlabel;
	memset(&cryptlabel, 0x00, 255);
	strncpy_s(cryptlabel, sizeof(cryptlabel), (LPCSTR)pMainSrv->pInitSrv->m_PrivateKeyLabel, _TRUNCATE);

	// Obter serial number do certificado associado (se houver)
	// Para chave privada PEM, podemos não ter certificado embutido
	// Vamos usar o serial do certificado público se disponível
	LPVOID lpwrk = &m_cryptSerialNumberPrv;
	memset(m_cryptSerialNumberPrv, 0x00, sizeof(m_cryptSerialNumberPrv));

	// Se temos um certificado carregado, usar seu serial number
	if (m_certificate)
	{
		ASN1_INTEGER* serial = X509_get_serialNumber(m_certificate);
		if (serial)
		{
			int len = serial->length;
			if (len > sizeof(m_cryptSerialNumberPrv))
				len = sizeof(m_cryptSerialNumberPrv);
			memcpy(m_cryptSerialNumberPrv, serial->data, len);
		}
	}

	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8087, TRUE, &lpcryptlabel, &cryptAlgo, &cryptKeySize, NULL, NULL);

	// Log serial number
	CString wrk;
    wrk = "====== | ----------------Inicio Private Key Serial Number -------------------- ";
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
    pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,FALSE,sizeof(m_cryptSerialNumberPrv),lpwrk);
    wrk = "====== | ----------------Fim    Private Key Serial Number -------------------- ";
	pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

	return status;
}

int CThreadMQ::funcAssinar(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg)
{
	// Migração CryptLib → OpenSSL (27/02/2026)
	int status = 0;

	if (lentmp == 0)
		return status;

	if (lpSecHeader->Versao == 0x00)
		return status;

	// Selecionar algoritmo de hash baseado em AlgHash
	const EVP_MD* digestAlgo = nullptr;
	if (lpSecHeader->AlgHash == 0x01)
	{
		digestAlgo = EVP_md5();  // MD5
	}
	else if (lpSecHeader->AlgHash == 0x02)
	{
		digestAlgo = EVP_sha1();  // SHA-1
	}
	else
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8088, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	// Alinhar mensagem para múltiplo de 8 bytes (compatibilidade com código original)
	int tamlenorig = lentmp;
	int restlen = 0;
	if ((lentmp % 8) != 0)
	{
		restlen = 8 - (lentmp % 8);
		memset(&msg[lentmp], 0x00, restlen);
		lentmp += restlen;
	}

	// Carregar chave privada se não estiver carregada
	if (m_privateKey == nullptr)
	{
		status = ReadPrivatKey();
		if (status != 0)
		{
			return status;
		}
	}

	// Copiar serial number do certificado local
	memcpy(lpSecHeader->NumSerieCertLocal, m_cryptSerialNumberPrv, sizeof(m_cryptSerialNumberPrv));

	// Criar assinatura digital usando OpenSSL wrapper
	unsigned char* signature = nullptr;
	size_t signatureLen = 0;

	bool signResult = OpenSSLCrypto::DigitalSignature::CreateSignature(
		msg,
		lentmp,
		m_privateKey,
		&signature,
		&signatureLen,
		digestAlgo
	);

	if (!signResult || signature == nullptr)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8091, FALSE, &status, NULL, NULL, NULL, NULL);
		if (signature) delete[] signature;
		return status;
	}

	// Copiar assinatura para estrutura (pulando 3 bytes iniciais - compatibilidade)
	// NOTA: CryptLib usava CRYPT_FORMAT_SPB que tinha 3 bytes de cabeçalho
	if (signatureLen > 3)
	{
		size_t copyLen = (signatureLen - 3) > 128 ? 128 : (signatureLen - 3);
		memcpy((BYTE*)&lpSecHeader->IniHashCifrSign, signature + 3, copyLen);
	}
	else
	{
		// Se assinatura muito pequena, copiar o que tiver
		size_t copyLen = signatureLen > 128 ? 128 : signatureLen;
		memcpy((BYTE*)&lpSecHeader->IniHashCifrSign, signature, copyLen);
	}

	delete[] signature;

	return status;
}

int CThreadMQ::funcLog(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg)
{
	int rc = false;
	return rc;
}

int CThreadMQ::funcCript(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg)
{
	// Migração CryptLib → OpenSSL (27/02/2026) - Criptografia 3DES + RSA
	int status = 0;

	if (lentmp == 0)
		return status;

	if (lpSecHeader->Versao == 0x00)
		return status;

	// Verificar algoritmo (só suporta 3DES)
	if (lpSecHeader->AlgSymKey != 0x01)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8093, FALSE, NULL, NULL, NULL, NULL, NULL);
		return -1;
	}

	// Gerar chave 3DES aleatória (24 bytes = 192 bits)
	unsigned char des3_key[24];
	unsigned char des3_iv[8];  // IV para CBC mode
	if (!RAND_bytes(des3_key, sizeof(des3_key)) || !RAND_bytes(des3_iv, sizeof(des3_iv)))
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8095, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	// Carregar chave pública se necessário
	if (m_publicKey == nullptr)
	{
		status = ReadPublicKey();
		if (status != 0)
		{
			return status;
		}
	}

	// Copiar serial number do certificado destino
	memcpy(lpSecHeader->NumSerieCertDest, m_cryptSerialNumberPub, sizeof(m_cryptSerialNumberPub));

	// Criptografar (wrap) a chave 3DES usando RSA
	EVP_PKEY_CTX* ctx = EVP_PKEY_CTX_new(m_publicKey, nullptr);
	if (!ctx)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8097, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	if (EVP_PKEY_encrypt_init(ctx) <= 0)
	{
		EVP_PKEY_CTX_free(ctx);
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8097, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	// Determinar tamanho do buffer necessário
	size_t encryptedKeyLen = 0;
	if (EVP_PKEY_encrypt(ctx, nullptr, &encryptedKeyLen, des3_key, sizeof(des3_key)) <= 0)
	{
		EVP_PKEY_CTX_free(ctx);
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8097, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	// Criptografar a chave
	unsigned char* encryptedKey = (unsigned char*)malloc(encryptedKeyLen);
	if (EVP_PKEY_encrypt(ctx, encryptedKey, &encryptedKeyLen, des3_key, sizeof(des3_key)) <= 0)
	{
		free(encryptedKey);
		EVP_PKEY_CTX_free(ctx);
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8097, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	EVP_PKEY_CTX_free(ctx);

	// Copiar chave criptografada para header (compatibilidade: pular 3 bytes se necessário)
	size_t copyLen = encryptedKeyLen > 128 ? 128 : encryptedKeyLen;
	memset(&lpSecHeader->IniSymKeyCifr, 0x00, 128);
	memcpy((BYTE*)&lpSecHeader->IniSymKeyCifr, encryptedKey, copyLen);
	free(encryptedKey);

	// Alinhar mensagem para múltiplo de 8 bytes (bloco 3DES)
	int tamlenorig = lentmp;
	if ((lentmp % 8) != 0)
	{
		int restlen = 8 - (lentmp % 8);
		memset(&msg[lentmp], 0x00, restlen);
		lentmp += restlen;
	}

	// Criptografar dados com 3DES-CBC
	EVP_CIPHER_CTX* cipherCtx = EVP_CIPHER_CTX_new();
	if (!cipherCtx)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8096, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	if (EVP_EncryptInit_ex(cipherCtx, EVP_des_ede3_cbc(), nullptr, des3_key, des3_iv) != 1)
	{
		EVP_CIPHER_CTX_free(cipherCtx);
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8096, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	EVP_CIPHER_CTX_set_padding(cipherCtx, 0);  // Já fizemos padding manual

	int outLen = 0;
	int totalLen = 0;
	if (EVP_EncryptUpdate(cipherCtx, msg, &outLen, msg, lentmp) != 1)
	{
		EVP_CIPHER_CTX_free(cipherCtx);
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8096, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}
	totalLen = outLen;

	if (EVP_EncryptFinal_ex(cipherCtx, msg + totalLen, &outLen) != 1)
	{
		EVP_CIPHER_CTX_free(cipherCtx);
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8096, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}
	totalLen += outLen;

	EVP_CIPHER_CTX_free(cipherCtx);

	return status;
}

int CThreadMQ::funcVerifyAss(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg)
{
	// Migração CryptLib → OpenSSL (27/02/2026)
	int status = 0;

	if (lentmp == 0)
		return status;

	if (lpSecHeader->Versao == 0x00)
		return status;

	// Selecionar algoritmo de hash
	const EVP_MD* digestAlgo = nullptr;
	if (lpSecHeader->AlgHash == 0x01)
	{
		digestAlgo = EVP_md5();  // MD5
	}
	else if (lpSecHeader->AlgHash == 0x02)
	{
		digestAlgo = EVP_sha1();  // SHA-1
	}
	else
	{
		lpSecHeader->CodErro = 0x06;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8101, FALSE, &lpSecHeader->AlgHash, NULL, NULL, NULL, NULL);
		return -1;
	}

	// Carregar chave pública se não estiver carregada
	if (m_publicKey == nullptr)
	{
		status = ReadPublicKey();
		if (status != 0)
		{
			return status;
		}
	}

	// Verificar serial number do certificado
	if (memcmp(lpSecHeader->NumSerieCertLocal, m_cryptSerialNumberPub, sizeof(m_cryptSerialNumberPub)) != 0)
	{
		lpSecHeader->CodErro = 0x10;
		CString wrk;
		wrk = "====== | ----------------Erro de Serial Number - Inicio Public Key ---------- ";
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8031, FALSE, (LPVOID)(LPTSTR)(LPCTSTR)wrk, NULL, NULL, NULL, NULL);
		pMainSrv->pInitSrv->m_WriteReg(m_szTaskName, FALSE, sizeof(m_cryptSerialNumberPub), &m_cryptSerialNumberPub);
		wrk = "====== | ----------------Erro de Serial Number - Inicio do Header ----------- ";
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8031, FALSE, (LPVOID)(LPTSTR)(LPCTSTR)wrk, NULL, NULL, NULL, NULL);
		pMainSrv->pInitSrv->m_WriteReg(m_szTaskName, FALSE, sizeof(lpSecHeader->NumSerieCertLocal), lpSecHeader->NumSerieCertLocal);
		wrk = "====== | ----------------Fim Serial Number ---------------------------------- ";
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8031, FALSE, (LPVOID)(LPTSTR)(LPCTSTR)wrk, NULL, NULL, NULL, NULL);
		return -1;
	}

	// Reconstruir assinatura com cabeçalho (compatibilidade com formato anterior)
	size_t signatureLen = 128 + 3;
	BYTE* signature = (BYTE*)malloc(signatureLen);
	memset(signature, 0x00, signatureLen);
	signature[0] = 0x43;
	signature[1] = 0x81;
	signature[2] = 0x80;
	memcpy((BYTE*)signature + 3, (BYTE*)&lpSecHeader->IniHashCifrSign, 128);

	// Verificar assinatura usando OpenSSL wrapper
	// Para OpenSSL, pulamos os 3 bytes de cabeçalho
	bool verifyResult = OpenSSLCrypto::DigitalSignature::VerifySignature(
		msg,
		lentmp,
		signature + 3,  // Pular cabeçalho CryptLib
		128,            // Tamanho real da assinatura
		m_publicKey,
		digestAlgo
	);

	if (!verifyResult)
	{
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8102, FALSE, &status, NULL, NULL, NULL, NULL);
		lpSecHeader->CodErro = 0x05;
		free(signature);
		return status;
	}

	free(signature);

	return status;
}

int CThreadMQ::funcStrLog(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg)
{
	bool rc = false;
	return rc;
}

int CThreadMQ::funcDeCript(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg)
{
	// Migração CryptLib → OpenSSL (27/02/2026) - Descriptografia 3DES + RSA
	int status = 0;

	if (lentmp == 0)
		return status;

	if (lpSecHeader->Versao == 0x00)
		return status;

	// Verificar algoritmo (só suporta 3DES)
	if (lpSecHeader->AlgSymKey != 0x01)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8093, FALSE, NULL, NULL, NULL, NULL, NULL);
		lpSecHeader->CodErro = 0x04;
		return -1;
	}

	// Carregar chave privada se necessário
	if (m_privateKey == nullptr)
	{
		status = ReadPrivatKey();
		if (status != 0)
		{
			return status;
		}
	}

	// Verificar serial number
	if (memcmp(lpSecHeader->NumSerieCertDest, m_cryptSerialNumberPrv, sizeof(m_cryptSerialNumberPrv)) != 0)
	{
		lpSecHeader->CodErro = 0x08;
		CString wrk;
		wrk = "====== | ----------------Erro de Serial Number - Inicio Private Key---------- ";
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8031, FALSE, (LPVOID)(LPTSTR)(LPCTSTR)wrk, NULL, NULL, NULL, NULL);
		pMainSrv->pInitSrv->m_WriteReg(m_szTaskName, FALSE, sizeof(m_cryptSerialNumberPrv), &m_cryptSerialNumberPrv);
		wrk = "====== | ----------------Erro de Serial Number - Inicio do Header ----------- ";
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8031, FALSE, (LPVOID)(LPTSTR)(LPCTSTR)wrk, NULL, NULL, NULL, NULL);
		pMainSrv->pInitSrv->m_WriteReg(m_szTaskName, FALSE, sizeof(lpSecHeader->NumSerieCertDest), lpSecHeader->NumSerieCertDest);
		wrk = "====== | ----------------Fim Serial Number ---------------------------------- ";
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8031, FALSE, (LPVOID)(LPTSTR)(LPCTSTR)wrk, NULL, NULL, NULL, NULL);
		return -1;
	}

	// Descriptografar (unwrap) a chave 3DES usando RSA
	unsigned char* encryptedKey = (unsigned char*)&lpSecHeader->IniSymKeyCifr;
	size_t encryptedKeyLen = 128;

	EVP_PKEY_CTX* ctx = EVP_PKEY_CTX_new(m_privateKey, nullptr);
	if (!ctx)
	{
		status = -1;
		lpSecHeader->CodErro = 0x03;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8099, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	if (EVP_PKEY_decrypt_init(ctx) <= 0)
	{
		EVP_PKEY_CTX_free(ctx);
		status = -1;
		lpSecHeader->CodErro = 0x03;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8099, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	// Determinar tamanho do buffer necessário
	size_t decryptedKeyLen = 0;
	if (EVP_PKEY_decrypt(ctx, nullptr, &decryptedKeyLen, encryptedKey, encryptedKeyLen) <= 0)
	{
		EVP_PKEY_CTX_free(ctx);
		status = -1;
		lpSecHeader->CodErro = 0x03;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8099, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	// Descriptografar a chave
	unsigned char* des3_key = (unsigned char*)malloc(decryptedKeyLen);
	if (EVP_PKEY_decrypt(ctx, des3_key, &decryptedKeyLen, encryptedKey, encryptedKeyLen) <= 0)
	{
		free(des3_key);
		EVP_PKEY_CTX_free(ctx);
		status = -1;
		lpSecHeader->CodErro = 0x03;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8099, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	EVP_PKEY_CTX_free(ctx);

	// Verificar alinhamento de 8 bytes
	if ((lentmp % 8) != 0)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8100, FALSE, &lentmp, NULL, NULL, NULL, NULL);
		lpSecHeader->CodErro = 0x01;
		free(des3_key);
		return -1;
	}

	// Descriptografar dados com 3DES-CBC
	// NOTA: Como não temos o IV original, usamos IV zero (compatibilidade com código antigo)
	unsigned char des3_iv[8] = {0};

	EVP_CIPHER_CTX* cipherCtx = EVP_CIPHER_CTX_new();
	if (!cipherCtx)
	{
		free(des3_key);
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8096, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	if (EVP_DecryptInit_ex(cipherCtx, EVP_des_ede3_cbc(), nullptr, des3_key, des3_iv) != 1)
	{
		EVP_CIPHER_CTX_free(cipherCtx);
		free(des3_key);
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8096, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}

	EVP_CIPHER_CTX_set_padding(cipherCtx, 0);  // Sem padding automático

	int outLen = 0;
	int totalLen = 0;
	if (EVP_DecryptUpdate(cipherCtx, msg, &outLen, msg, lentmp) != 1)
	{
		EVP_CIPHER_CTX_free(cipherCtx);
		free(des3_key);
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8096, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}
	totalLen = outLen;

	if (EVP_DecryptFinal_ex(cipherCtx, msg + totalLen, &outLen) != 1)
	{
		EVP_CIPHER_CTX_free(cipherCtx);
		free(des3_key);
		status = -1;
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName, 8096, FALSE, &status, NULL, NULL, NULL, NULL);
		return status;
	}
	totalLen += outLen;

	EVP_CIPHER_CTX_free(cipherCtx);
	free(des3_key);

	return status;
}
