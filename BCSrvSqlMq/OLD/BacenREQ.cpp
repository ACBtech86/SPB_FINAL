// BacenReq.cpp : implementation file
//
// Fase 6: Removido #define _WIN32_WINNT 0x0400 (obsoleto, definido pelo CMake)


#include <afx.h>
#include <afxmt.h>
#include <afxdb.h>
#include <cmqc.h>
#include "MsgSgr.h"
#include "NTServApp.h"
#include "InitSrv.h"
#include "winsock2.h"
// Fase 6: Desfazer conflitos wincrypt.h ANTES de incluir cryptlib.h
#include "crypto_compat.h"
#include "cryptlib.h"
#include "MainSrv.h"
#include "Monitor.h"
#include "ThreadMQ.h"
#include "CBCDb.h"
#include "ControleRS.h"
#include "IFAppRS.h"
#include "STRLogRS.h"
#include "BacenAppRS.h"
#include "BacenReq.h"

void CBacenReq::RunThread(LPVOID MainSrv)
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


bool CBacenReq::RunInitDBeMQ()
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

    strcpy(m_szQueueName, pMainSrv->pInitSrv->m_MqQlBacenCidadeReq);
    strcpy(m_od.ObjectName, pMainSrv->pInitSrv->m_MqQlBacenCidadeReq);
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
    m_pDb3   = new CBCDatabase(pMainSrv->pInitSrv->m_DBName,pMainSrv->pInitSrv->m_MQServer,pMainSrv->pInitSrv->m_MonitorPort,pMainSrv->pInitSrv->m_MaxLenMsg);
	m_pDb3->SetTransactions();
    m_pDb4   = new CBCDatabase(pMainSrv->pInitSrv->m_DBName,pMainSrv->pInitSrv->m_MQServer,pMainSrv->pInitSrv->m_MonitorPort,pMainSrv->pInitSrv->m_MaxLenMsg);
	m_pDb4->SetTransactions();
	m_pRS = new CBacenAppRS(m_pDb1,pMainSrv->pInitSrv->m_DbTbBacenCidadeApp);
	m_pRSLog = new CSTRLogRS(m_pDb2,pMainSrv->pInitSrv->m_DbTbStrLog);
	m_pRSCtr = new CControleRS(m_pDb3,pMainSrv->pInitSrv->m_DbTbControle);
	m_pRSApp = new CIFAppRS(m_pDb4,pMainSrv->pInitSrv->m_DbTbCidadeBacenApp);

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
		try
		{
			m_pDb1->ExecuteSQL(m_pRS->m_sCreate);
			m_pDb1->ExecuteSQL(m_pRS->m_sPriKey);
			m_pDb1->ExecuteSQL(m_pRS->m_sIndex1);
			m_pDb1->ExecuteSQL(m_pRS->m_sIndex2);
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
		try
		{
			m_pDb2->ExecuteSQL(m_pRSLog->m_sCreate);
			m_pDb2->ExecuteSQL(m_pRSLog->m_sPriKey);
			m_pDb2->ExecuteSQL(m_pRSLog->m_sIndex1);
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

	try
	{
		if (!m_pDb3->Open(m_pRSLog->GetDefaultConnect(),FALSE,FALSE,"ODBC;",FALSE))
		{
			rt = true;
			return rt;
		}
		m_pRSCtr->m_strFilter = "[ISPB] = ? ";
		if (!m_pRSCtr->Open(CRecordset::dynaset))
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
		try
		{
			m_pDb3->ExecuteSQL(m_pRSCtr->m_sCreate);
			m_pDb3->ExecuteSQL(m_pRSCtr->m_sPriKey);
			m_pRSCtr->m_strFilter = "[ISPB] = ? ";
			m_pRSCtr->Open(CRecordset::dynaset);
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
		if (!m_pDb4->Open(m_pRSLog->GetDefaultConnect(),FALSE,FALSE,"ODBC;",FALSE))
		{
			rt = true;
			return rt;
		}
		m_pRSApp->m_index = 1;
		m_pRSApp->m_nParams = 1;
		m_pRSApp->m_strFilter = " [MQ_MSG_ID] = ? ";
		if (!m_pRSApp->Open(CRecordset::dynaset))
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
			m_pRSApp->m_index = 1;
			m_pRSApp->m_nParams = 1;
			m_pRSApp->m_strFilter = "[MQ_MSG_ID] = ? ";
			m_pRSApp->Open(CRecordset::dynaset);
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

bool CBacenReq::RunTermDBeMQ()
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
		if (m_pRSCtr	!= NULL) m_pRSCtr->Close();
		if (m_pRSApp	!= NULL) m_pRSApp->Close();
		if (m_pDb1		!= NULL) m_pDb1->Close();
		if (m_pDb2		!= NULL) m_pDb2->Close();
		if (m_pDb3		!= NULL) m_pDb3->Close();
		if (m_pDb4		!= NULL) m_pDb4->Close();
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
	delete m_pRSCtr;
	delete m_pRSApp;
	delete m_pDb1;
	delete m_pDb2;
	delete m_pDb3;
	delete m_pDb4;
	return rt;
}


void CBacenReq::ProcessaQueue()
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
	  m_StatusMsg = "N";
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

     pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8024,TRUE,&pMainSrv->pInitSrv->m_QueueMgr,&pMainSrv->pInitSrv->m_MqQlBacenCidadeReq,&m_messlen,NULL,NULL);
	 DumpHeader(&m_md);
     pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,TRUE,m_messlen,m_buffermsg);
	 m_buflen = m_messlen; /* len buffer of GET   */

	 GetSystemTime(&m_t);

//------------------------------------------------------------------------------------------
//  descriptografar e verificar assinatura  
//------------------------------------------------------------------------------------------
    if (!erro)
	{
		erro = CheckAssDeCryptBufferMQ();
	}

//------------------------------------------------------------------------------------------
//  TASK CONFERE XML s� em unicode - Em teste converte para unicode   
//------------------------------------------------------------------------------------------
    if (!erro)
	{
		if (pMainSrv->pInitSrv->m_UnicodeEnable.Compare("N") == 0)
		{
			int lenmsg = m_buflen - sizeof(SECHDR);
			if (lenmsg > 0 )
			{
				if (AnsiToUnicode(lenmsg, &m_buffermsg[sizeof(SECHDR)]))
				{
				    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8072,FALSE,NULL,NULL,NULL,NULL,NULL);
					erro = true;
				}
				m_messlen = sizeof(SECHDR) + lenmsg;
				m_buflen = m_messlen;
			}
		}
		else
		{
			BSTR bstr = (BSTR) &m_buffermsg[sizeof(SECHDR)];
			int lenwrk2 = (m_buflen - sizeof(SECHDR)) / 2;
			for (int i = 0;i < lenwrk2 ; i++)
			{
				bstr[i] = ntohs(bstr[i]);
			}
		}
	}


//------------------------------------------------------------------------------------------
//  Checar xml  
//------------------------------------------------------------------------------------------
    if (!erro)
	{
		erro = ChecarXml();
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
	
//------------------------------------------------------------------------------------------
//  converte de unicode para char   
//------------------------------------------------------------------------------------------
	
    if (!erro)
	{
		int lenmsg = m_buflen - sizeof(SECHDR);
		if (lenmsg > 0)
		{
			if (UnicodeToAnsi(lenmsg , &m_buffermsg[sizeof(SECHDR)]))
			{
			    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8107,FALSE,NULL,NULL,NULL,NULL,NULL);
				erro = true;
			}
		    m_buflen = sizeof(SECHDR) + lenmsg; 
		}
	}
//------------------------------------------------------------------------------------------
//  UpdateDB  
//------------------------------------------------------------------------------------------
    if (!erro)
	{
		erro = UpdateDB();
	}

    if (!erro)
	{
		if 	(m_StatusMsg.Compare("N") == 0)
		{
			erro = AtualizaCtr();
		}
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
		try
		{
			if (m_pRSCtr->Islock())
			{
				m_pRSCtr->m_pDatabase->Rollback();
			}
			m_pRSCtr->Unlock();
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
		    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		}
		try
		{
			if ((m_pRS->GetRowStatus(1) == SQL_ROW_ADDED) ||
			    (m_pRSApp->GetRowStatus(1) == SQL_ROW_UPDATED))
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
		    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSApp->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
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
		try
		{
			if (m_pRSCtr->Islock())
			{
				m_pRSCtr->m_pDatabase->CommitTrans();
			}
			m_pRSCtr->Unlock();
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
		    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		}
		try
		{
			if ((m_pRS->GetRowStatus(1) == SQL_ROW_ADDED) ||
			    (m_pRSApp->GetRowStatus(1) == SQL_ROW_UPDATED))
			{
				m_pRSApp->m_pDatabase->CommitTrans();
			}
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
		    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSApp->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
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

bool CBacenReq::UpdateDB()
{
	bool rc = false;
	try
	{
		::SQLFreeStmt(m_pRS->m_hstmt,SQL_CLOSE);
		m_pRS->m_pDatabase->BeginTrans();
		m_pRS->m_nParams = 1;
		m_pRS->m_index = 2;
		m_pRS->m_strFilter = "[NU_OPE] = ? ";
		m_pRS->Requery();
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
		::SQLFreeStmt(m_pRSLog->m_hstmt,SQL_CLOSE);
		m_pRSLog->m_pDatabase->BeginTrans();
		m_pRSLog->m_strFilter = "[NU_OPE] = ? ";
		m_pRSLog->Requery();
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

bool CBacenReq::MontaDbRegApp()
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
//  Status da Mensagem (N-Normal/E-Erro/R-Report)
//------------------------------------------------------------------------------------------

	m_pRS->m_STATUS_MSG = m_StatusMsg;                

//------------------------------------------------------------------------------------------
//  Flag de processamento N-no insert / S-apos aplicativo ler
//------------------------------------------------------------------------------------------

	m_pRS->m_FLAG_PROC = "N";                

//------------------------------------------------------------------------------------------
//  Fila de origem MQ
//------------------------------------------------------------------------------------------

	m_pRS->m_MQ_QN_ORIGEM = pMainSrv->pInitSrv->m_MqQlBacenCidadeReq;                

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
//  Extrair NUOpe do xml  
//------------------------------------------------------------------------------------------
	m_pRS->m_NU_OPE = m_NuOpe;

//------------------------------------------------------------------------------------------
//  Extrair CODMSG do xml  
//------------------------------------------------------------------------------------------

	m_pRS->m_COD_MSG    = m_CodMsg;

//------------------------------------------------------------------------------------------
//  Extrair toda a mensagem Xml  
//------------------------------------------------------------------------------------------

    m_pRS->m_MSG = m_buffermsg+sizeof(SECHDR); // - security header


	return rc;
}

bool CBacenReq::MontaDbRegLog()
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

    m_pRSLog->m_STATUS_MSG = m_StatusMsg;    

//------------------------------------------------------------------------------------------
//  Fila de origem MQ
//------------------------------------------------------------------------------------------

    m_pRSLog->m_MQ_QN_ORIGEM = pMainSrv->pInitSrv->m_MqQlBacenCidadeReq;    

	
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
//  Extrair NUOpe do xml  
//------------------------------------------------------------------------------------------
	m_pRSLog->m_NU_OPE = m_NuOpe;

//------------------------------------------------------------------------------------------
//  Extrair CODMSG do xml  
//------------------------------------------------------------------------------------------

	m_pRSLog->m_COD_MSG = m_CodMsg;

//------------------------------------------------------------------------------------------
//  Extrair toda a mensagem Xml  
//------------------------------------------------------------------------------------------

    m_pRSLog->m_MSG = m_buffermsg+sizeof(SECHDR); // - security header

	return rc;
}

bool CBacenReq::CheckAssDeCryptBufferMQ()
{
	bool rc = false;
	LPSECHDR lpSecHeader;
	m_messlen = 0;
	int lenmsgorig = 0;

//----------------------------------------------------------------
//  checando mensagem do Header de Seguran�a
//----------------------------------------------------------------
	lpSecHeader = (LPSECHDR) &m_buffermsg[0];
	m_messlen = sizeof(SECHDR);
	if (lpSecHeader->TamSecHeader[0] != 0x01)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8073,FALSE,NULL,NULL,NULL,NULL,NULL);
		lpSecHeader->CodErro = 0x04;
	}
	if (lpSecHeader->TamSecHeader[1] != 0x4C)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8073,FALSE,NULL,NULL,NULL,NULL,NULL);
		lpSecHeader->CodErro = 0x04;
	}
	if (lpSecHeader->CodErro != 0x00)
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8074,FALSE,&lpSecHeader->CodErro,NULL,NULL,NULL,NULL);
		rc = true;
	}

	int lenmsg = m_buflen - sizeof(SECHDR);
	if (lenmsg > 0)
	{
		if 	(lpSecHeader->Versao == 0x01)     // mensagem criptografada
		{
			if (rc == 0)
			{
				if (funcDeCript(lpSecHeader, lenmsg, &m_buffermsg[sizeof(SECHDR)]))
				{
					GeraReport();
					rc = true;
				}
			}
			if (rc == 0)
			{
				if (funcStrLog(lpSecHeader, lenmsg, &m_buffermsg[sizeof(SECHDR)]))
				{
					GeraReport();
					rc = true;
				}
			}
			if (rc == 0)
			{
				if (funcVerifyAss(lpSecHeader, lenmsg, &m_buffermsg[sizeof(SECHDR)]))
				{
					GeraReport();
					rc = true;
				}
			}
		}
		else
		{
			if (funcStrLog(lpSecHeader, lenmsg, &m_buffermsg[sizeof(SECHDR)]))
			{
				rc = true;
			}
		}
	}
	else
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8075,FALSE,NULL,NULL,NULL,NULL,NULL);
		if (funcStrLog(lpSecHeader, lenmsg, &m_buffermsg[sizeof(SECHDR)]))
		{
			rc = true;
		}
	}

	return rc;
}

bool CBacenReq::ChecarXml()
{
	bool rc = false;
	CString wrk;
	PBYTE ppbuf = &m_buffermsg[sizeof(SECHDR)]; 
	BSTR strwFind  = NULL;
	BSTR strwValue = NULL;
	BSTR strwParent = NULL;
	CHAR* strcValue = NULL;

	// Fase 6: Migrado de MSXML para pugixml
	ULONG lenmsg = m_buflen - sizeof(SECHDR);
	if (lenmsg > 0 )
	{
		// Load and parse XML document
		if (!LoadDocumentSync(m_xmlDoc, (const char*)&m_buffermsg[sizeof(SECHDR)], lenmsg)) {
			return false; // Error already logged by LoadDocumentSync
		}
		m_xmlNode = m_xmlDoc.document_element();

		wrk = "====== | ----------------Inicio Mensagem Xml --------------------------------- ";
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
		WalkTree(m_xmlNode,0);
		wrk = "====== | ----------------Fim    Mensagem Xml --------------------------------- ";
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8031,TRUE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);

		// Parse XML tags - usando std::string ao invés de BSTR
		std::string tagValue;

		// BCMSG/NUOp
		if (FindTag(m_xmlDoc, "BCMSG", "NUOp", tagValue))
		{
			m_NuOpe = tagValue.c_str();
		}

		// Grupo_EmissorMsg
		const char* emissor = "Grupo_EmissorMsg";
		m_TipoIdEmissor.Empty();
		if (FindTag(m_xmlDoc, emissor, "TipoId_Emissor", tagValue))
		{
			m_TipoIdEmissor = tagValue.c_str();
		}

		m_IdEmissor.Empty();
		if (FindTag(m_xmlDoc, emissor, "Id_Emissor", tagValue))
		{
			m_IdEmissor = tagValue.c_str();
		}

		// Grupo_DestinatarioMsg
		const char* destinatario = "Grupo_DestinatarioMsg";
		m_TipoIdDestinatario.Empty();
		if (FindTag(m_xmlDoc, destinatario, "TipoId_Destinatario", tagValue))
		{
			m_TipoIdDestinatario = tagValue.c_str();
		}

		m_IdDestinatario.Empty();
		if (FindTag(m_xmlDoc, destinatario, "Id_Destinatario", tagValue))
		{
			m_IdDestinatario = tagValue.c_str();
		}

		// CodMsg (sem parent)
		if (FindTag(m_xmlDoc, nullptr, "CodMsg", tagValue))
		{
			m_CodMsg = tagValue.c_str();
		}


//		if (m_CodMsg.Compare("CONECT") == 0 )
//		{
//			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8076,FALSE,&m_CodMsg,NULL,NULL,NULL,NULL);
//			rc = true;
//			return rc;
//		}
//		if (m_CodMsg.Compare("DESCON") == 0 )
//		{
//			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8076,FALSE,&m_CodMsg,NULL,NULL,NULL,NULL);
//			rc = true;
//			return rc;
//		}
		if (m_CodMsg.Compare("GEN0001") == 0 )
		{
			rc = FuncEco();
			return rc;
		}
		if (m_CodMsg.Compare("GEN0002") == 0 )
		{
			rc = FuncLog();
			return rc;
		}
		if (m_CodMsg.Compare("GEN0003") == 0 )
		{
			rc = FuncUltMsg();
			return rc;
		}

	
	}
	return rc;

CleanUp:
    m_StatusMsg = "E";
	GeraReport();
	return rc;
}


bool CBacenReq::AtualizaCtr()
{
	bool rc = false;
	BSTR strwFind  = NULL;
	BSTR strwValue = NULL;
	CHAR* strcValue = NULL;
	CString datewrk;

	try
	{
		::SQLFreeStmt(m_pRSCtr->m_hstmt,SQL_CLOSE);
		m_pRSCtr->m_pDatabase->BeginTrans();
		m_pRSCtr->m_nParams = 1;
		m_pRSCtr->m_strFilter = "[ISPB] = ? ";
		if (m_IdEmissor.Compare("SISBACEN") == 0)
		{
			m_pRSCtr->m_ParamISPB = "00038166";
		}
		else
		{
			m_pRSCtr->m_ParamISPB = m_IdEmissor;
		}
		m_pRSCtr->Lock();
		m_pRSCtr->Requery();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		m_pRSCtr->Unlock();
		rc = true;
		return rc;
	}

	if (m_pRSCtr->IsEOF())
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8077,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->m_ParamISPB,NULL,NULL,NULL,NULL);
		rc = true;
		return rc;
	}
	try
	{
		m_pRSCtr->Edit();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		m_pRSCtr->Unlock();
		rc = true;
		return rc;
	}

	if (!m_NuOpe.IsEmpty())
	{
		m_pRSCtr->m_ULTMSG	= m_NuOpe;
		m_pRSCtr->m_DTHR_ULTMSG.year		= m_t.wYear;
		m_pRSCtr->m_DTHR_ULTMSG.month		= m_t.wMonth;
		m_pRSCtr->m_DTHR_ULTMSG.day			= m_t.wDay;
		m_pRSCtr->m_DTHR_ULTMSG.hour		= m_t.wHour;
		m_pRSCtr->m_DTHR_ULTMSG.minute		= m_t.wMinute;
		m_pRSCtr->m_DTHR_ULTMSG.second		= m_t.wSecond;
		m_pRSCtr->m_DTHR_ULTMSG.fraction	= m_t.wMilliseconds;
	}

	try
	{
		m_pRSCtr->Update();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		m_pRSCtr->Unlock();
		rc = true;
		return rc;
	}

	return rc;
}

bool CBacenReq::ReadCtr()
{
	bool rc = false;
	BSTR strwFind  = NULL;
	BSTR strwValue = NULL;
	CHAR* strcValue = NULL;
	CString datewrk;

	try
	{
		m_pRSCtr->m_nParams = 1;
		m_pRSCtr->m_strFilter = "[ISPB] = ? ";
		if (m_IdEmissor.Compare("SISBACEN") == 0)
		{
			m_pRSCtr->m_ParamISPB = "00038166";
		}
		else
		{
			m_pRSCtr->m_ParamISPB = m_IdEmissor;
		}
		m_pRSCtr->Requery();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		m_pRSCtr->Unlock();
		rc = true;
		return rc;
	}

	if (m_pRSCtr->IsEOF())
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8077,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->m_ParamISPB,NULL,NULL,NULL,NULL);
		rc = true;
		return rc;
	}
	return rc;
}



bool CBacenReq::FuncEco()
{
	bool rc = false;
	CString datewrk;
	CString xml;
	CString wrk;

	// Fase 6: Migrado de MSXML para pugixml
	std::string tagValue;
	if (!FindTag(m_xmlDoc, "SISMSG", "GENReqECO", tagValue))
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8078,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
		rc = true;
		return rc;
	}

	GeraEcoR1(xml);

	try
	{
		::SQLFreeStmt(m_pRSCtr->m_hstmt,SQL_CLOSE);
		m_pRSCtr->m_pDatabase->BeginTrans();
		m_pRSCtr->m_nParams = 1;
		m_pRSCtr->m_strFilter = "[ISPB] = ? ";
		if (m_IdEmissor.Compare("SISBACEN") == 0)
		{
			m_pRSCtr->m_ParamISPB = "00038166";
		}
		else
		{
			m_pRSCtr->m_ParamISPB = m_IdEmissor;
		}
		m_pRSCtr->Lock();
		m_pRSCtr->Requery();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		rc = true;
		m_pRSCtr->Unlock();
		return rc;
	}


	if (m_pRSCtr->IsEOF())
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8077,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->m_ParamISPB,NULL,NULL,NULL,NULL);
		rc = true;
		m_pRSCtr->Unlock();
		return rc;
	}
	try
	{
		m_pRSCtr->Edit();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		rc = true;
		m_pRSCtr->Unlock();
		return rc;
	}

	m_pRSCtr->m_DTHR_ECO.year		= m_t.wYear;
	m_pRSCtr->m_DTHR_ECO.month		= m_t.wMonth;
	m_pRSCtr->m_DTHR_ECO.day		= m_t.wDay;
	m_pRSCtr->m_DTHR_ECO.hour		= m_t.wHour;
	m_pRSCtr->m_DTHR_ECO.minute		= m_t.wMinute;
	m_pRSCtr->m_DTHR_ECO.second		= m_t.wSecond;
	m_pRSCtr->m_DTHR_ECO.fraction	= m_t.wMilliseconds;

	try
	{
		m_pRSCtr->Update();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSCtr->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		rc = true;
		m_pRSCtr->Unlock();
		return rc;
	}


	try
	{
		::SQLFreeStmt(m_pRSApp->m_hstmt,SQL_CLOSE);
		m_pRSApp->m_pDatabase->BeginTrans();
		m_pRSApp->m_strFilter = "[MQ_MSG_ID] = ? ";
		m_pRSApp->m_index = 1;
		m_pRSApp->m_nParams = 1;
		m_pRSApp->Requery();
		m_pRSApp->AddNew();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
	    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSApp->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		return true;
	}

	
	m_pRSApp->m_DB_DATETIME.year	  = m_t.wYear;
	m_pRSApp->m_DB_DATETIME.month	  = m_t.wMonth;
	m_pRSApp->m_DB_DATETIME.day		  = m_t.wDay;
	m_pRSApp->m_DB_DATETIME.hour	  = m_t.wHour;
	m_pRSApp->m_DB_DATETIME.minute    = m_t.wMinute;
	m_pRSApp->m_DB_DATETIME.second    = m_t.wSecond;
	m_pRSApp->m_DB_DATETIME.fraction  = m_t.wMilliseconds;
	m_pRSApp->m_STATUS_MSG = "P";
	m_pRSApp->m_FLAG_PROC  = "N";
	m_pRSApp->m_MQ_QN_DESTINO  = pMainSrv->pInitSrv->m_MqQrCidadeBacenRsp;
	m_pRSApp->m_NU_OPE = m_NuOpe;
	m_pRSApp->m_COD_MSG = "GEN0001R1";
	m_pRSApp->m_MSG = xml;

    if (!rc)
	{
		try
		{
			 m_pRSApp->Update();
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSApp->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
			rc = true;
		}
	}


	return rc;

}

bool CBacenReq::FuncLog()
{
	bool rc = false;
	CString xml;
	CString wrk;
	CString NUOpLog;

	// Fase 6: Migrado de MSXML para pugixml
	std::string tagValue;

	// Verifica se tag GENReqLOG existe
	if (!FindTag(m_xmlDoc, "SISMSG", "GENReqLOG", tagValue))
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8078,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
		rc = true;
		return rc;
	}

	// Busca NUOp dentro de GENReqLOG
	if (FindTag(m_xmlDoc, "GENReqLOG", "NUOp", tagValue))
	{
		NUOpLog = tagValue.c_str();
	}

	GeraLogR1(NUOpLog,xml);

	try
	{
		::SQLFreeStmt(m_pRSApp->m_hstmt,SQL_CLOSE);
		m_pRSApp->m_pDatabase->BeginTrans();
		m_pRSApp->m_strFilter = "[MQ_MSG_ID] = ? ";
		m_pRSApp->m_index = 1;
		m_pRSApp->m_nParams = 1;
		m_pRSApp->Requery();
		m_pRSApp->AddNew();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
	    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSApp->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		return true;
	}

	
	m_pRSApp->m_DB_DATETIME.year	  = m_t.wYear;
	m_pRSApp->m_DB_DATETIME.month	  = m_t.wMonth;
	m_pRSApp->m_DB_DATETIME.day		  = m_t.wDay;
	m_pRSApp->m_DB_DATETIME.hour	  = m_t.wHour;
	m_pRSApp->m_DB_DATETIME.minute    = m_t.wMinute;
	m_pRSApp->m_DB_DATETIME.second    = m_t.wSecond;
	m_pRSApp->m_DB_DATETIME.fraction  = m_t.wMilliseconds;
	m_pRSApp->m_STATUS_MSG = "P";
	m_pRSApp->m_FLAG_PROC  = "N";
	m_pRSApp->m_MQ_QN_DESTINO  = pMainSrv->pInitSrv->m_MqQrCidadeBacenRsp;
	m_pRSApp->m_NU_OPE = m_NuOpe;
	m_pRSApp->m_COD_MSG = "GEN0002R1";
	m_pRSApp->m_MSG = xml;
    if (!rc)
	{
		try
		{
			 m_pRSApp->Update();
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSApp->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
			rc = true;
		}
	}


	return rc;
}

bool CBacenReq::FuncUltMsg()
{
	bool rc = false;
	CString xml;
	CString wrk;

	// Fase 6: Migrado de MSXML para pugixml
	std::string tagValue;
	if (!FindTag(m_xmlDoc, "SISMSG", "GENReqUltMsg", tagValue))
	{
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8078,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
		rc = true;
		return rc;
	}

	if (ReadCtr())
	{
		rc = true;
		return rc;
	}

	GeraUltMsgR1(xml);

	try
	{
		::SQLFreeStmt(m_pRSApp->m_hstmt,SQL_CLOSE);
		m_pRSApp->m_pDatabase->BeginTrans();
		m_pRSApp->m_strFilter = "[MQ_MSG_ID] = ? ";
		m_pRSApp->m_index = 1;
		m_pRSApp->m_nParams = 1;
		m_pRSApp->Requery();
		m_pRSApp->AddNew();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
	    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSApp->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		return true;
	}

	
	m_pRSApp->m_DB_DATETIME.year	  = m_t.wYear;
	m_pRSApp->m_DB_DATETIME.month	  = m_t.wMonth;
	m_pRSApp->m_DB_DATETIME.day		  = m_t.wDay;
	m_pRSApp->m_DB_DATETIME.hour	  = m_t.wHour;
	m_pRSApp->m_DB_DATETIME.minute    = m_t.wMinute;
	m_pRSApp->m_DB_DATETIME.second    = m_t.wSecond;
	m_pRSApp->m_DB_DATETIME.fraction  = m_t.wMilliseconds;
	m_pRSApp->m_STATUS_MSG = "P";
	m_pRSApp->m_FLAG_PROC  = "N";
	m_pRSApp->m_MQ_QN_DESTINO  = pMainSrv->pInitSrv->m_MqQrCidadeBacenRsp;
	m_pRSApp->m_NU_OPE = m_NuOpe;
	m_pRSApp->m_COD_MSG = "GEN0003R1";
	m_pRSApp->m_MSG = xml;
    if (!rc)
	{
		try
		{
			 m_pRSApp->Update();
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSApp->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
			rc = true;
		}
	}

	
	return rc;
}

bool  CBacenReq::GeraEcoR1(CString& xml)
{
	bool rc = false;
	CString msgeco;

	// Fase 6: Migrado de MSXML para pugixml
	std::string tagValue;
	if (FindTag(m_xmlDoc, "GENReqECO", "MsgECO", tagValue))
	{
		msgeco = tagValue.c_str();
	}

	xml.Empty();
	xml  = "<?xml version=";
	xml += '"';
	xml += "1.0";
	xml += '"';
	xml += "?><!DOCTYPE SPBDOC SYSTEM ";
	xml += '"';
	xml += "SPBDOC.DTD";
	xml += '"';
	xml += ">";
	xml += "<SPBDOC>";
	xml += "<BCMSG>";
	xml += "<Grupo_EmissorMsg>";
	xml += "<TipoId_Emissor>";
	xml += m_TipoIdDestinatario;
	xml += "</TipoId_Emissor>";
	xml += "<Id_Emissor>";
	xml += m_IdDestinatario;
	xml += "</Id_Emissor>";
	xml += "</Grupo_EmissorMsg>";
	xml += "<Grupo_DestinatarioMsg>";
	xml += "<TipoId_Destinatario>";
	xml += m_TipoIdEmissor;
	xml += "</TipoId_Destinatario>";
	xml += "<Id_Destinatario>";
	xml += m_IdEmissor;
	xml += "</Id_Destinatario>";
	xml += "</Grupo_DestinatarioMsg>";
	xml += "<NUOp>";
	xml += m_NuOpe;
	xml += "</NUOp>";
	xml += "</BCMSG>";
	xml += "<SISMSG>";
	xml += "<GENReqECORespReq>";
	xml += "<CodMsg>GEN0001R1</CodMsg>";
	xml += "<MsgECO>";
	xml += msgeco;
	delete[] msgeco;
	xml += "</MsgECO>";
	xml += "</GENReqECORespReq>";
	xml += "</SISMSG>";
	xml += "<USERMSG/>";
	xml += "</SPBDOC>";

	return rc;
       
}

bool  CBacenReq::GeraUltMsgR1(CString& xml)
{
	bool rc = false;
	CString datawrk;
	
	xml.Empty();
	xml  = "<?xml version=";
	xml += '"';
	xml += "1.0";
	xml += '"';
	xml += "?><!DOCTYPE SPBDOC SYSTEM ";
	xml += '"';
	xml += "SPBDOC.DTD";
	xml += '"';
	xml += ">";
	xml += "<SPBDOC>";
	xml += "<BCMSG>";
	xml += "<Grupo_EmissorMsg>";
	xml += "<TipoId_Emissor>";
	xml += m_TipoIdDestinatario;
	xml += "</TipoId_Emissor>";
	xml += "<Id_Emissor>";
	xml += m_IdDestinatario;
	xml += "</Id_Emissor>";
	xml += "</Grupo_EmissorMsg>";
	xml += "<Grupo_DestinatarioMsg>";
	xml += "<TipoId_Destinatario>";
	xml += m_TipoIdEmissor;
	xml += "</TipoId_Destinatario>";
	xml += "<Id_Destinatario>";
	xml += m_IdEmissor;
	xml += "</Id_Destinatario>";
	xml += "</Grupo_DestinatarioMsg>";
	xml += "<NUOp>";
	xml += m_NuOpe;
	xml += "</NUOp>";
	xml += "</BCMSG>";
	xml += "<SISMSG>";
	xml += "<GENReqUltMsgRespReq>";
	xml += "<CodMsg>GEN0003R1</CodMsg>";
	xml += "<NumUltOp>";
	xml += m_pRSCtr->m_ULTMSG;
	xml += "</NumUltOp>";
	xml += "<DtHUltMsg>";
	datawrk.Format("%04d%02d%02d%02d%02d%02d",
					m_pRSCtr->m_DTHR_ULTMSG.year,
					m_pRSCtr->m_DTHR_ULTMSG.month,
					m_pRSCtr->m_DTHR_ULTMSG.day,
					m_pRSCtr->m_DTHR_ULTMSG.hour,
					m_pRSCtr->m_DTHR_ULTMSG.minute,
					m_pRSCtr->m_DTHR_ULTMSG.second);
	xml += datawrk;	
	xml += "</DtHUltMsg>";
	xml += "<DtHBC>";
	datawrk.Format("%04d%02d%02d%02d%02d%02d",
					m_t.wYear,m_t.wMonth,m_t.wDay,
					m_t.wHour,m_t.wMinute,m_t.wSecond);
	xml += datawrk;	
	xml += "</DtHBC>";
	xml += "</GENReqUltMsgRespReq>";
	xml += "</SISMSG>";
	xml += "</SPBDOC>";

	return rc;
       
}


bool  CBacenReq::GeraLogR1(CString& NUOpLog,CString& xml)
{
	bool rc = false;

	try
	{
		::SQLFreeStmt(m_pRSLog->m_hstmt,SQL_CLOSE);
		m_pRSLog->m_ParamNU_OPE = NUOpLog;
		m_pRSLog->m_strFilter = "[NU_OPE] = ? ";
		m_pRSLog->Requery();
		m_pRSLog->m_ParamNU_OPE = "";

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


	xml.Empty();
	xml  = "<?xml version=";
	xml += '"';
	xml += "1.0";
	xml += '"';
	xml += "?><!DOCTYPE SPBDOC SYSTEM ";
	xml += '"';
	xml += "SPBDOC.DTD";
	xml += '"';
	xml += ">";
	xml += "<SPBDOC>";
	xml += "<BCMSG>";
	xml += "<Grupo_EmissorMsg>";
	xml += "<TipoId_Emissor>";
	xml += m_TipoIdDestinatario;
	xml += "</TipoId_Emissor>";
	xml += "<Id_Emissor>";
	xml += m_IdDestinatario;
	xml += "</Id_Emissor>";
	xml += "</Grupo_EmissorMsg>";
	xml += "<Grupo_DestinatarioMsg>";
	xml += "<TipoId_Destinatario>";
	xml += m_TipoIdEmissor;
	xml += "</TipoId_Destinatario>";
	xml += "<Id_Destinatario>";
	xml += m_IdEmissor;
	xml += "</Id_Destinatario>";
	xml += "</Grupo_DestinatarioMsg>";
	xml += "<NUOp>";
	xml += m_NuOpe;
	xml += "</NUOp>";
	xml += "</BCMSG>";

	if (m_pRSLog->IsEOF())
	{
		// erro de  NUOp n�o encontrada
		xml += "<SISMSG>";
		xml += "<GENReqLOG>";
		xml += "<CodMsg>";
		xml += m_CodMsg;
		xml += "E</CodMsg>";
		xml += "<NUOp CodErro=";
		xml += '"';
		xml += "EGEN0013";
		xml += '"';
		xml += ">";
		xml += m_NuOpe;
		xml += "</NUOp>";
		xml += "</GENReqLOG>";
		xml += "</SISMSG>";
		xml += "</SPBDOC>";
		return rc;
	}

	xml += "<SISMSG>";
	xml += "<GENReqLOGRespReq>";
	xml += "<CodMsg>GEN0002R1</CodMsg>";
	xml += "<Repet_GEN0002R1_Msg>";
	
	
	while(!m_pRSLog->IsEOF())
	{
		xml += "<Msg><![CDATA[";
		xml += m_pRSLog->m_MSG;
		xml += "]]></Msg>";
		m_pRSLog->MoveNext();
	}
	
	xml += "</Repet_GEN0002R1_Msg>";
	xml += "</GENReqLOGRespReq>";
	xml += "</SISMSG>";
	xml += "</SPBDOC>";

	return rc;
       
}

bool CBacenReq::GeraReport()
{
	bool rc = false;
	ULONG lenmsg = m_buflen - sizeof(SECHDR);
	try
	{
		::SQLFreeStmt(m_pRSApp->m_hstmt,SQL_CLOSE);
		m_pRSApp->m_pDatabase->BeginTrans();
		m_pRSApp->m_strFilter = "[MQ_MSG_ID] = ? ";
		m_pRSApp->m_index = 1;
		m_pRSApp->m_nParams = 1;
		m_pRSApp->Requery();
		m_pRSApp->AddNew();
	}
	catch( CDBException * pEx )
	{
		TCHAR    szCause[255];
		char *   lpszCause = (char *)  &szCause;
		pEx->GetErrorMessage(szCause, 255);
		pEx->Delete( );
	    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSApp->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		return true;
	}

	
	m_pRSApp->m_DB_DATETIME.year	  = m_t.wYear;
	m_pRSApp->m_DB_DATETIME.month	  = m_t.wMonth;
	m_pRSApp->m_DB_DATETIME.day		  = m_t.wDay;
	m_pRSApp->m_DB_DATETIME.hour	  = m_t.wHour;
	m_pRSApp->m_DB_DATETIME.minute    = m_t.wMinute;
	m_pRSApp->m_DB_DATETIME.second    = m_t.wSecond;
	m_pRSApp->m_DB_DATETIME.fraction  = m_t.wMilliseconds;
	m_pRSApp->m_STATUS_MSG = "P";
	m_pRSApp->m_FLAG_PROC  = "N";
	m_pRSApp->m_MQ_QN_DESTINO  = pMainSrv->pInitSrv->m_MqQrCidadeBacenRep;
	m_pRSApp->m_NU_OPE = "";
	m_pRSApp->m_COD_MSG = "REPORT";

    ULONG i;

    
	LPBYTE pbyte = (BYTE *) &m_md.MsgId;

    try 
	{ 
        m_pRSApp->m_MQ_CORREL_ID.SetSize(sizeof(m_md.CorrelId));
    }
    catch (CMemoryException* e) 
	{   
		e->Delete ();
        AfxThrowMemoryException();
        return true;
    }

    for ( i=0; i < sizeof(m_md.CorrelId) ; i++) 
	{
        m_pRSApp->m_MQ_CORREL_ID[i] = pbyte[i];
    }
	
	try 
	{ 
        m_pRSApp->m_SECURITY_HEADER.SetSize(sizeof(SECHDR));
    }
    catch (CMemoryException* e) 
	{   
		e->Delete ();
        AfxThrowMemoryException();
        return true;
    }
	for (i=0; i< sizeof(SECHDR); i++) 
	{  
        m_pRSApp->m_SECURITY_HEADER[i] = m_buffermsg[i];
    }
    pbyte = m_buffermsg+sizeof(SECHDR); // - security header

	m_pRSApp->m_MSG_LEN = lenmsg;
    m_pRSApp->m_MSG.Empty();
    for (i=0; i < lenmsg; i++) 
	{
        m_pRSApp->m_MSG.Insert(i,(TCHAR) pbyte[i]);
    }

    if (!rc)
	{
		try
		{
			 m_pRSApp->Update();
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRSApp->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
			rc = true;
		}
	}

	return rc;
}
