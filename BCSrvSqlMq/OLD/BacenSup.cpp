// BacenSup.cpp : implementation file
//
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
#include "CBCDb.h"
#include "STRLogRS.h"
#include "BacenAppRS.h"
#include "BacenSup.h"

void CBacenSup::RunThread(LPVOID MainSrv)
{
	pMainSrv	= (CMainSrv *) MainSrv;

	RunInit();

	if (!RunInitDBeMQ())
	{
		RunWait();
	}
	RunTermDBeMQ();
	RunTerm();
	return;
}


bool CBacenSup::RunInitDBeMQ()
{
	bool rt = false;

	m_pDb1		= NULL;
	m_pDb2		= NULL;
	m_pRS		= NULL;
	m_pRSLog	= NULL;

    MQOD    od  = {MQOD_DEFAULT};    /* Object Descriptor             */
    MQMD    md  = {MQMD_DEFAULT};    /* Message Descriptor            */
    MQGMO   gmo = {MQGMO_DEFAULT};   /* get message options           */
	MQBO	bo	= {MQBO_DEFAULT};    /* begin options             */
 
	memcpy(&m_od,&od,sizeof(MQOD));   
	memcpy(&m_md,&md,sizeof(MQMD));   
	memcpy(&m_gmo,&gmo,sizeof(MQGMO));   
	memcpy(&m_bo,&bo,sizeof(MQBO));   
	
	m_buffermsg = new MQBYTE[pMainSrv->pInitSrv->m_MaxLenMsg];

    strcpy(m_szQueueName, pMainSrv->pInitSrv->m_MqQlBacenCidadeSup);
    strcpy(m_od.ObjectName, pMainSrv->pInitSrv->m_MqQlBacenCidadeSup);
    m_od.ObjectType = MQOT_Q;  // Set queue object type
    m_QMName[0] = 0;   /* default */
    strcpy(m_QMName, pMainSrv->pInitSrv->m_QueueMgr);

   /******************************************************************/
   /*                                                                */
   /*   Connect to queue manager                                     */
   /*                                                                */
   /******************************************************************/
   MQCONN(m_QMName,                  /* queue manager                  */
          &m_Hcon,                   /* connection handle              */
          &m_CompCode,               /* completion code                */
          &m_CReason);               /* reason code                    */

   /* report reason and stop if it failed     */
   if (m_CompCode == MQCC_FAILED)
   {
	 pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8018,FALSE,&m_CReason,NULL,NULL,NULL,NULL);
     rt = true;
	 return rt;
   }

   /******************************************************************/
   /*                                                                */
   /*   Open the named message queue for input; exclusive or shared  */
   /*   use of the queue is controlled by the queue definition here  */
   /*                                                                */
   /******************************************************************/
   m_O_options = MQOO_INPUT_EXCLUSIVE  /* open queue for input EXCLUSIVE */
         + MQOO_FAIL_IF_QUIESCING;     /* but not if MQM stopping      */
   MQOPEN(m_Hcon,                      /* connection handle            */
          &m_od,                       /* object descriptor for queue  */
          m_O_options,                 /* open options                 */
          &m_Hobj,                     /* object handle                */
          &m_OpenCode,                 /* completion code              */
          &m_Reason);                  /* reason code                  */

   /* report reason, if any; stop if failed      */
   if (m_Reason != MQRC_NONE)
   {
	 pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8019,FALSE,&m_Reason,NULL,NULL,NULL,NULL);
     rt = true;
	 return rt;
   }

   if (m_OpenCode == MQCC_FAILED)
   {
	 pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8020,FALSE,NULL,NULL,NULL,NULL,NULL);
     rt = true;
	 return rt;
   }


   
    m_pDb1   = new CBCDatabase(pMainSrv->pInitSrv->m_DBName,pMainSrv->pInitSrv->m_MQServer,pMainSrv->pInitSrv->m_MonitorPort,pMainSrv->pInitSrv->m_MaxLenMsg);
	m_pDb1->SetTransactions();
    m_pDb2   = new CBCDatabase(pMainSrv->pInitSrv->m_DBName,pMainSrv->pInitSrv->m_MQServer,pMainSrv->pInitSrv->m_MonitorPort,pMainSrv->pInitSrv->m_MaxLenMsg);
	m_pDb2->SetTransactions();
	m_pRS = new CBacenAppRS(m_pDb1,pMainSrv->pInitSrv->m_DbTbBacenCidadeApp);
	m_pRSLog = new CSTRLogRS(m_pDb2,pMainSrv->pInitSrv->m_DbTbStrLog);

	try
	{
		if (!m_pDb1->Open(m_pRS->GetDefaultConnect(),FALSE,FALSE,"ODBC;",FALSE))
		{
			rt = true;
			return rt;
		}
		m_pRS->m_index = 2;
		m_pRS->m_nParams = 1;
		m_pRS->m_strFilter = "[NU_OPE] = ? ";
		if (!m_pRS->Open(CRecordset::dynaset))
		{
			rt = true;
			return rt;
		}
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		rt = true;
		if (pEx->m_strStateNativeOrigin.Find(_T("State:S0002")) >= 0)
		{
			pEx->Delete( );
		}
		else
		{
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8071,FALSE,lpszCause,NULL,NULL,NULL,NULL);
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8070,FALSE,(LPVOID)&pEx->m_nRetCode,(LPVOID)(LPCTSTR)pEx->m_strStateNativeOrigin ,(LPVOID)(LPCTSTR)pEx->m_strError,NULL,NULL);
			pEx->Delete( );
			return rt;
		}
	}

	if (rt)
	{
		rt = false;
		DWORD dwMilliseconds = 30000;   			
		Sleep(dwMilliseconds);
		try
		{
			m_pRS->m_index = 2;
			m_pRS->m_nParams = 1;
			m_pRS->m_strFilter = "[NU_OPE] = ? ";
			m_pRS->Open(CRecordset::dynaset);
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8071,FALSE,lpszCause,NULL,NULL,NULL,NULL);
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8070,FALSE,(LPVOID)&pEx->m_nRetCode,(LPVOID)(LPCTSTR)pEx->m_strStateNativeOrigin ,(LPVOID)(LPCTSTR)pEx->m_strError,NULL,NULL);
			pEx->Delete( );
			rt = true;
			return rt;
		}
	}

	try
	{
		if (!m_pDb2->Open(m_pRSLog->GetDefaultConnect(),FALSE,FALSE,"ODBC;",FALSE))
		{
			rt = true;
			return rt;
		}
		m_pRSLog->m_strFilter = "[NU_OPE] = ? ";
		if (!m_pRSLog->Open(CRecordset::dynaset))
		{
			rt = true;
			return rt;
		}
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		rt = true;
		if (pEx->m_strStateNativeOrigin.Find(_T("State:S0002")) >= 0)
		{
			pEx->Delete( );
		}
		else
		{
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8071,FALSE,lpszCause,NULL,NULL,NULL,NULL);
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8070,FALSE,(LPVOID)&pEx->m_nRetCode,(LPVOID)(LPCTSTR)pEx->m_strStateNativeOrigin ,(LPVOID)(LPCTSTR)pEx->m_strError,NULL,NULL);
			pEx->Delete( );
			return rt;
		}
	}

	if (rt)
	{
		rt = false;
		DWORD dwMilliseconds = 30000;   			
		Sleep(dwMilliseconds);
		try
		{
			m_pRSLog->m_strFilter = "[NU_OPE] = ? ";
			m_pRSLog->Open(CRecordset::dynaset);
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8071,FALSE,lpszCause,NULL,NULL,NULL,NULL);
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8070,FALSE,(LPVOID)&pEx->m_nRetCode,(LPVOID)(LPCTSTR)pEx->m_strStateNativeOrigin ,(LPVOID)(LPCTSTR)pEx->m_strError,NULL,NULL);
			pEx->Delete( );
			rt = true;
			return rt;
		}
	}
	return rt;
}

bool CBacenSup::RunTermDBeMQ()
{
	bool rt = false;

   /******************************************************************/
   /*                                                                */
   /*   Close the source queue (if it was opened)                    */
   /*                                                                */
   /******************************************************************/
   if (m_OpenCode != MQCC_FAILED)
   {
     m_C_options = 0;                   /* no close options            */
     MQCLOSE(m_Hcon,                    /* connection handle           */
             &m_Hobj,                   /* object handle               */
             m_C_options,
             &m_CompCode,               /* completion code             */
             &m_Reason);                /* reason code                 */

     /* report reason, if any     */
     if (m_Reason != MQRC_NONE)
     {
    	 pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8021,FALSE,&m_Reason,NULL,NULL,NULL,NULL);
     }
   }

   /******************************************************************/
   /*                                                                */
   /*   Disconnect from MQM if not already connected                 */
   /*                                                                */
   /******************************************************************/
   if (m_CReason != MQRC_ALREADY_CONNECTED )
   {
     MQDISC(&m_Hcon,                     /* connection handle          */
            &m_CompCode,                 /* completion code            */
            &m_Reason);                  /* reason code                */

     /* report reason, if any     */
     if (m_Reason != MQRC_NONE)
     {
    	 pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8022,FALSE,&m_Reason,NULL,NULL,NULL,NULL);
     }
   }


	try
	{
		if (m_pRS		!= NULL) m_pRS->Close();
		if (m_pRSLog	!= NULL) m_pRSLog->Close();
		if (m_pDb1		!= NULL) m_pDb1->Close();
		if (m_pDb2		!= NULL) m_pDb2->Close();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8071,FALSE,lpszCause,NULL,NULL,NULL,NULL);
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8070,FALSE,(LPVOID)&pEx->m_nRetCode,(LPVOID)(LPCTSTR)pEx->m_strStateNativeOrigin ,(LPVOID)(LPCTSTR)pEx->m_strError,NULL,NULL);
		pEx->Delete( );
		rt = true;
	}

	delete m_buffermsg;

	delete m_pRS;
	delete m_pRSLog;
	delete m_pDb1;
	delete m_pDb2;
	return rt;
}


void CBacenSup::ProcessaQueue()
{
	bool erro = false;
	m_CompCode = m_OpenCode;       /* use MQOPEN result for initial test  */
   
   /******************************************************************/
   /* Use these options when connecting to Queue Managers that also  */
   /* support them, see the Application Programming Reference for    */
   /* details.                                                       */
   /* These options cause the MsgId and CorrelId to be replaced, so  */
   /* that there is no need to reset them before each MQGET          */ 
   /******************************************************************/
   m_gmo.Version = MQGMO_VERSION_2; /* Avoid need to reset Message */
   m_gmo.MatchOptions = MQMO_NONE;  /* ID and Correlation ID after */
                                      /* every MQGET                 */
   m_gmo.Options = MQGMO_WAIT       /* wait for new messages           */
			   + MQGMO_SYNCPOINT;
   m_gmo.WaitInterval = 5000;      /* 5 second limit for waiting     */

//   while (m_CompCode != MQCC_FAILED)
   while (erro != true)
   {
	  erro = false;
	  m_buflen = pMainSrv->pInitSrv->m_MaxLenMsg - 1; /* buffer size available for GET   */

     /****************************************************************/
     /* The following two statements are not required if the MQGMO   */
     /* version is set to MQGMO_VERSION_2 and and gmo.MatchOptions   */
     /* is set to MQGMO_NONE                                         */
     /****************************************************************/
     /*                                                              */
     /*   In order to read the messages in sequence, MsgId and       */
     /*   CorrelID must have the default value.  MQGET sets them     */
     /*   to the values in for message it returns, so re-initialise  */
     /*   them before every call                                     */
     /*                                                              */
     /****************************************************************/
     memcpy(m_md.MsgId, MQMI_NONE, sizeof(m_md.MsgId));
     memcpy(m_md.CorrelId, MQCI_NONE, sizeof(m_md.CorrelId));

     /****************************************************************/
     /*                                                              */
     /*   MQGET sets Encoding and CodedCharSetId to the values in    */
     /*   the message returned, so these fields should be reset to   */
     /*   the default values before every call, as MQGMO_CONVERT is  */
     /*   specified.                                                 */
     /*                                                              */
     /****************************************************************/

     m_md.Encoding       = MQENC_NATIVE;
     m_md.CodedCharSetId = MQCCSI_Q_MGR;

     MQGET(m_Hcon,                /* connection handle                 */
           m_Hobj,                /* object handle                     */
           &m_md,                 /* message descriptor                */
           &m_gmo,                /* get message options               */
           m_buflen,              /* buffer length                     */
           m_buffermsg,           /* message buffer                    */
           &m_messlen,            /* message length                    */
           &m_CompCode,           /* completion code                   */
           &m_Reason);            /* reason code                       */

     /* report reason, if any     */
     if (m_Reason != MQRC_NONE)
     {
       if (m_Reason == MQRC_NO_MSG_AVAILABLE)
       {                         
         return;
       }
       else                      /* general report for other reasons */
       {
    	 pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8023,FALSE,&m_Reason,&m_CompCode,NULL,NULL,NULL);
         /*   treat truncated message as a failure for this sample   */
         if (m_Reason == MQRC_TRUNCATED_MSG_FAILED)
         {
           m_CompCode = MQCC_FAILED;
         }
       }
     }

     /****************************************************************/
     /*   Display each message received                              */
     /****************************************************************/
     if (m_CompCode == MQCC_FAILED)
     {
    	 pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8023,FALSE,&m_Reason,&m_CompCode,NULL,NULL,NULL);
		 continue;
     }

     pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8024,TRUE,&pMainSrv->pInitSrv->m_QueueMgr,&pMainSrv->pInitSrv->m_MqQlBacenCidadeSup,&m_messlen,NULL,NULL);
	 DumpHeader(&m_md);
     pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,TRUE,m_messlen,m_buffermsg);
	 m_buflen = m_messlen; /* len buffer of GET   */

	 GetSystemTime(&m_t);

//------------------------------------------------------------------------------------------
//  UpdateDB  
//------------------------------------------------------------------------------------------
    if (!erro)
	{
		erro = UpdateDB();
	}

//------------------------------------------------------------------------------------------
//  Log sequencial 
//------------------------------------------------------------------------------------------
    if (!erro)
	{
		UINT lenwrt = 0;
		BYTE *wrk;
		wrk = new BYTE[sizeof(STAUDITFILE)];
		pMainSrv->MontaAudit(lenwrt,wrk, &m_t, (BYTE *) &m_md , m_buflen, m_buffermsg);
		pMainSrv->WriteAudit(lenwrt,wrk);
		delete wrk;
	}

    if (erro)
	{
        m_CompCode = MQCC_FAILED;
		SetEvent(m_hEvent[THREAD_EVENT_STOP]);
		try
		{
			if (m_pRS->GetRowStatus(1) == SQL_ROW_ADDED)
			{
				m_pRS->m_pDatabase->Rollback();
			}
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
		    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRS->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		}
		try
		{
			if (m_pRSLog->GetRowStatus(1) == SQL_ROW_ADDED)
			{
				m_pRSLog->m_pDatabase->Rollback();
			}
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
		    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSLog->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		}
		MQBACK(m_Hcon, &m_CompCode, &m_Reason);
		if (m_Reason == MQRC_NONE)
		{
		   pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8025,TRUE,NULL,NULL,NULL,NULL,NULL);
		}
		else
		{
    	   pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8027,FALSE,&m_Reason,&m_CompCode,NULL,NULL,NULL);
		} 
	}
	else
	{
		try
		{
			if (m_pRS->GetRowStatus(1) == SQL_ROW_ADDED)
			{
				m_pRS->m_pDatabase->CommitTrans();
			}
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
		    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRS->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		}
		try
		{
			if (m_pRSLog->GetRowStatus(1) == SQL_ROW_ADDED)
			{
				m_pRSLog->m_pDatabase->CommitTrans();
			}
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
		    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSLog->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		}
		MQCMIT(m_Hcon, &m_CompCode, &m_Reason);

		if (m_Reason == MQRC_NONE)
		{
		   pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8026,TRUE,NULL,NULL,NULL,NULL,NULL);
		}
		else
		{
    	   pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8028,FALSE,&m_Reason,&m_CompCode,NULL,NULL,NULL);
		}
	}
   }

}

bool CBacenSup::UpdateDB()
{
	bool rc = false;
	try
	{
		m_pRS->AddNew();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRS->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		rc = true;
		return rc;
	}

	MontaDbRegApp();

	try
	{
		m_pRS->Update();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRS->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		rc = true;
		return rc;
	}

	try
	{
		m_pRSLog->AddNew();

	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSLog->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		rc = true;
		return rc;
	}

	MontaDbRegLog();

	try
	{
		m_pRSLog->Update();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSLog->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		rc = true;
		return rc;
	}
	return rc;
}

bool CBacenSup::MontaDbRegApp()
{
	bool rc = false;
	int i = 0;
	LPBYTE pbyte;
	char wrk[25];
	CString datewrk;

//------------------------------------------------------------------------------------------
//  Atualiza db da aplica��o
//------------------------------------------------------------------------------------------
	m_pRS->SetFieldNull(NULL);

	pbyte = (BYTE *) &m_md.MsgId;
    try 
	{ 
        m_pRS->m_MQ_MSG_ID.SetSize(sizeof(m_md.MsgId));
    }
    catch (CMemoryException* e) 
	{   
		e->Delete ();
        AfxThrowMemoryException();
        return true;
    }
    for ( i=0; i < sizeof(m_md.MsgId) ; i++) 
	{
        m_pRS->m_MQ_MSG_ID[i] = pbyte[i];
    }
	pbyte = (BYTE *) &m_md.CorrelId;
    try 
	{ 
        m_pRS->m_MQ_CORREL_ID.SetSize(sizeof(m_md.CorrelId));
    }
    catch (CMemoryException* e) 
	{   
		e->Delete ();
        AfxThrowMemoryException();
        return true;
    }
    for ( i=0; i < sizeof(m_md.CorrelId) ; i++) 
	{
        m_pRS->m_MQ_CORREL_ID[i] = pbyte[i];
    }

//------------------------------------------------------------------------------------------
//  DB_DATETIME setada com data e hora atual  
//------------------------------------------------------------------------------------------

	m_pRS->m_DB_DATETIME.year	  = m_t.wYear;
	m_pRS->m_DB_DATETIME.month	  = m_t.wMonth;
	m_pRS->m_DB_DATETIME.day	  = m_t.wDay;
	m_pRS->m_DB_DATETIME.hour	  = m_t.wHour;
	m_pRS->m_DB_DATETIME.minute   = m_t.wMinute;
	m_pRS->m_DB_DATETIME.second   = m_t.wSecond;
	m_pRS->m_DB_DATETIME.fraction = m_t.wMilliseconds;

//------------------------------------------------------------------------------------------
//  Status da Mensagem (S-SEND/X-Xml Erro/C-Cryptografia erro/R-Receive/P-Processado/E-Report
//------------------------------------------------------------------------------------------

	m_pRS->m_STATUS_MSG = "N";       //n-normal         

//------------------------------------------------------------------------------------------
//  Flag de processamento N-no insert / S-apos aplicativo ler
//------------------------------------------------------------------------------------------

	m_pRS->m_FLAG_PROC = "N";                

//------------------------------------------------------------------------------------------
//  Fila de origem MQ
//------------------------------------------------------------------------------------------

	m_pRS->m_MQ_QN_ORIGEM = pMainSrv->pInitSrv->m_MqQlBacenCidadeSup;                

//------------------------------------------------------------------------------------------
//  Data e Hora do Put do MQ 
//------------------------------------------------------------------------------------------

	
	memset(&wrk,0x00,25);
	memcpy(&wrk,&m_md.PutDate,sizeof(m_md.PutDate));
	datewrk = wrk;
	memset(&wrk,0x00,25);
	memcpy(&wrk,&m_md.PutTime,sizeof(m_md.PutTime));
	datewrk += wrk;
	
	m_pRS->m_MQ_DATETIME.year	  = atoi(datewrk.Mid(0,4));
	m_pRS->m_MQ_DATETIME.month	  = atoi(datewrk.Mid(4,2));
	m_pRS->m_MQ_DATETIME.day	  = atoi(datewrk.Mid(6,2));
	m_pRS->m_MQ_DATETIME.hour	  = atoi(datewrk.Mid(8,2));
	m_pRS->m_MQ_DATETIME.minute   = atoi(datewrk.Mid(10,2));
	m_pRS->m_MQ_DATETIME.second   = atoi(datewrk.Mid(12,2));
	m_pRS->m_MQ_DATETIME.fraction = atoi(datewrk.Mid(14,2)) * 10;

//------------------------------------------------------------------------------------------
//  m_MQ_HEADER setada com o Header do MQSeries  
//------------------------------------------------------------------------------------------
	pbyte = (BYTE *) &m_md;
    try 
	{ 
        m_pRS->m_MQ_HEADER.SetSize(512);
    }
    catch (CMemoryException* e) 
	{   
		e->Delete ();
        AfxThrowMemoryException();
        return true;
    }

    for ( i=0; i < sizeof(MQMD); i++) 
	{
        m_pRS->m_MQ_HEADER[i] = pbyte[i];
    }

	pbyte = (BYTE *) &m_md;

    try 
	{ 
        m_pRS->m_SECURITY_HEADER.SetSize(sizeof(SECHDR));
    }
    catch (CMemoryException* e) 
	{   
		e->Delete ();
        AfxThrowMemoryException();
        return true;
    }

    for ( i=0; i < sizeof(SECHDR); i++) 
	{
        m_pRS->m_SECURITY_HEADER[i] = pbyte[i];
    }

//------------------------------------------------------------------------------------------
//  Extrair toda a mensagem CLEAN  
//------------------------------------------------------------------------------------------

    m_pRS->m_MSG = m_buffermsg; 

	m_pRS->m_COD_MSG = "SUPORTE";

	return rc;
}

bool CBacenSup::MontaDbRegLog()
{
	bool rc = false;
	int i = 0;
	LPBYTE pbyte;
	char wrk[25];
	CString datewrk;

//------------------------------------------------------------------------------------------
//  Atualiza db log
//------------------------------------------------------------------------------------------
	m_pRSLog->SetFieldNull(NULL);

//------------------------------------------------------------------------------------------
//  Msg Id do MQ
//------------------------------------------------------------------------------------------

	pbyte = (BYTE *) &m_md.MsgId;

    try 
	{ 
        m_pRSLog->m_MQ_MSG_ID.SetSize(sizeof(m_md.MsgId));
    }
    catch (CMemoryException* e) 
	{   
		e->Delete ();
        AfxThrowMemoryException();
        return true;
    }

    for ( i=0; i < sizeof(m_md.MsgId) ; i++) 
	{
        m_pRSLog->m_MQ_MSG_ID[i] = pbyte[i];
    }

//------------------------------------------------------------------------------------------
//  Correl Id do MQ
//------------------------------------------------------------------------------------------

	pbyte = (BYTE *) &m_md.CorrelId;

    try 
	{ 
        m_pRSLog->m_MQ_CORREL_ID.SetSize(sizeof(m_md.CorrelId));
    }
    catch (CMemoryException* e) 
	{   
		e->Delete ();
        AfxThrowMemoryException();
        return true;
    }

    for ( i=0; i < sizeof(m_md.CorrelId) ; i++) 
	{
        m_pRSLog->m_MQ_CORREL_ID[i] = pbyte[i];
    }

//------------------------------------------------------------------------------------------
//  DB_DATETIME setada com data e hora atual  
//------------------------------------------------------------------------------------------

	m_pRSLog->m_DB_DATETIME.year	  = m_t.wYear;
	m_pRSLog->m_DB_DATETIME.month	  = m_t.wMonth;
	m_pRSLog->m_DB_DATETIME.day	  = m_t.wDay;
	m_pRSLog->m_DB_DATETIME.hour	  = m_t.wHour;
	m_pRSLog->m_DB_DATETIME.minute   = m_t.wMinute;
	m_pRSLog->m_DB_DATETIME.second   = m_t.wSecond;
	m_pRSLog->m_DB_DATETIME.fraction = m_t.wMilliseconds;

//------------------------------------------------------------------------------------------
//  Status da Mensagem (N-Normal/X-Xml Erro/D-Decryptografia erro
//------------------------------------------------------------------------------------------

    m_pRSLog->m_STATUS_MSG = "N";    

//------------------------------------------------------------------------------------------
//  Fila de origem MQ
//------------------------------------------------------------------------------------------

    m_pRSLog->m_MQ_QN_ORIGEM = pMainSrv->pInitSrv->m_MqQlBacenCidadeSup;    

	
//------------------------------------------------------------------------------------------
//  Data e Hora do Put do MQ 
//------------------------------------------------------------------------------------------

	memset(&wrk,0x00,25);
	memcpy(&wrk,&m_md.PutDate,sizeof(m_md.PutDate));
	datewrk = wrk;
	memset(&wrk,0x00,25);
	memcpy(&wrk,&m_md.PutTime,sizeof(m_md.PutTime));
	datewrk += wrk;
	
	m_pRSLog->m_MQ_DATETIME.year	  = atoi(datewrk.Mid(0,4));
	m_pRSLog->m_MQ_DATETIME.month	  = atoi(datewrk.Mid(4,2));
	m_pRSLog->m_MQ_DATETIME.day	      = atoi(datewrk.Mid(6,2));
	m_pRSLog->m_MQ_DATETIME.hour	  = atoi(datewrk.Mid(8,2));
	m_pRSLog->m_MQ_DATETIME.minute    = atoi(datewrk.Mid(10,2));
	m_pRSLog->m_MQ_DATETIME.second    = atoi(datewrk.Mid(12,2));
	m_pRSLog->m_MQ_DATETIME.fraction  = atoi(datewrk.Mid(14,2)) * 10;

//------------------------------------------------------------------------------------------
//  m_MQ_HEADER setada com o Header do MQSeries  
//------------------------------------------------------------------------------------------
	pbyte = (BYTE *) &m_md;

    try 
	{ 
        m_pRSLog->m_MQ_HEADER.SetSize(512);
    }
    catch (CMemoryException* e) 
	{   
		e->Delete ();
        AfxThrowMemoryException();
        return true;
    }

    for ( i=0; i < sizeof(MQMD); i++) 
	{
        m_pRSLog->m_MQ_HEADER[i] = pbyte[i];
    }

//------------------------------------------------------------------------------------------
//  m_SEC_HEADER setada com o zero binarios  
//------------------------------------------------------------------------------------------
    try 
	{ 
        m_pRSLog->m_SECURITY_HEADER.SetSize(sizeof(SECHDR));
    }
    catch (CMemoryException* e) 
	{   
		e->Delete ();
        AfxThrowMemoryException();
        return true;
    }
    for ( i=0; i< sizeof(SECHDR); i++) 
	{  
        m_pRSLog->m_SECURITY_HEADER[i] = 0;
    }


//------------------------------------------------------------------------------------------
//  Extrair toda a mensagem CLEAN  
//------------------------------------------------------------------------------------------

    m_pRSLog->m_MSG = m_buffermsg; 

	return rc;
}

