// IFSup.cpp : implementation file
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
#include "STRLogRS.h"
#include "IFAppRS.h"
#include "IFSup.h"

void CIFSup::RunThread(LPVOID MainSrv)
{
	pMainSrv	= (CMainSrv *) MainSrv;

	RunInit();

	if (!RunInitDBeMQ())
	{
		RunWaitPost();
	}
	RunTermDBeMQ();
	RunTerm();
	return;
}


bool CIFSup::RunInitDBeMQ()
{
	bool rt = false;

	m_pDb1		= NULL;
	m_pDb2		= NULL;
	m_pRS		= NULL;
	m_pRSLog	= NULL;

    MQOD    od  = {MQOD_DEFAULT};    /* Object Descriptor             */
    MQMD    md  = {MQMD_DEFAULT};    /* Message Descriptor            */
	MQBO	bo	= {MQBO_DEFAULT};    /* begin options             */
 
	memcpy(&m_od,&od,sizeof(MQOD));   
	memcpy(&m_md,&md,sizeof(MQMD));   
	memcpy(&m_bo,&bo,sizeof(MQBO));   
	
	m_buffermsg = new MQBYTE[pMainSrv->pInitSrv->m_MaxLenMsg];

    strcpy(m_szQueueName, pMainSrv->pInitSrv->m_MqQlIFCidadeSup);
    strcpy(m_od.ObjectName, pMainSrv->pInitSrv->m_MqQlIFCidadeSup);
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
   /*   Open the named message queue for output                      */
   /*   use of the queue is controlled by the queue definition here  */
   /*                                                                */
   /******************************************************************/
   m_O_options = MQOO_OUTPUT		   /* open queue for output         */
         + MQOO_FAIL_IF_QUIESCING;	   /* but not if MQM stopping      */
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
	m_pRS    = new CIFAppRS(m_pDb1,pMainSrv->pInitSrv->m_DbTbCidadeBacenApp);
	m_pRSLog = new CSTRLogRS(m_pDb2,pMainSrv->pInitSrv->m_DbTbStrLog);

	try
	{
		if (!m_pDb1->Open(m_pRS->GetDefaultConnect(),FALSE,FALSE,"ODBC;",FALSE))
		{
			rt = true;
			return rt;
		}
		m_pRS->m_index = 2;
		m_pRS->m_nParams = 2;
		m_pRS->m_ParamMQ_QN_DESTINO = pMainSrv->pInitSrv->m_MqQrCidadeBacenSup;
		m_pRS->m_ParamFLAG_PROC = "N";
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
			m_pRS->m_nParams = 2;
			m_pRS->m_ParamMQ_QN_DESTINO = pMainSrv->pInitSrv->m_MqQrCidadeBacenSup;
			m_pRS->m_ParamFLAG_PROC = "N";
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

bool CIFSup::RunTermDBeMQ()
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

void CIFSup::ProcessaQueue()
{
	bool processa = true;
	while (processa)
	{
		try
		{
			::SQLFreeStmt(m_pRS->m_hstmt,SQL_CLOSE);
			m_pRS->m_pDatabase->BeginTrans();
			m_pRS->m_ParamMQ_QN_DESTINO = pMainSrv->pInitSrv->m_MqQrCidadeBacenSup;
			m_pRS->m_ParamFLAG_PROC = "N";
			m_pRS->m_strFilter = "[MQ_QN_DESTINO] = ? AND [FLAG_PROC] = ? ";
			m_pRS->Requery();
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
		    pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRS->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
			return;
		}
		if (m_pRS->IsEOF())
		{
			m_pRS->m_pDatabase->Rollback();
			processa = false;
			continue;
		}

		GetSystemTime(&m_t);
		
		if (UpdateMQeDB(m_pRS))
		{
			processa = false;
			SetEvent(m_hEvent[THREAD_EVENT_STOP]);
		}
	}
}

bool CIFSup::UpdateMQeDB(CIFAppRS *rs)
{
	bool erro = false;
	m_CompCode = m_OpenCode;       /* use MQOPEN result for initial test  */
   
    memset(&m_md, '\0', sizeof(m_md));
    memcpy(m_md.StrucId, MQMD_STRUC_ID,
           sizeof(m_md.StrucId));
    memcpy(m_md.MsgId,           /* reset MsgId to get a new one    */
           MQMI_NONE, sizeof(m_md.MsgId) );

    memcpy(m_md.CorrelId,        /* reset CorrelId to get a new one */
           MQCI_NONE, sizeof(m_md.CorrelId) );
    m_md.Version     =  MQMD_VERSION_1;
    m_md.Expiry      =  MQEI_UNLIMITED;
    m_md.Report      =  MQRO_COA + MQRO_COD + MQRO_EXCEPTION;
    m_md.MsgType     =  MQMT_REQUEST;
    memcpy(m_md.Format,MQFMT_STRING,sizeof(m_md.Format));
    m_md.Priority    =  MQPRI_PRIORITY_AS_Q_DEF ;
    m_md.Persistence =  MQPER_PERSISTENT;
    memset(m_md.ReplyToQMgr,
           0x00,
           sizeof(m_md.ReplyToQMgr));
    memcpy(m_md.ReplyToQMgr,
           pMainSrv->pInitSrv->m_QueueMgr,
           pMainSrv->pInitSrv->m_QueueMgr.GetLength());
    memset(m_md.ReplyToQ,
           0x00,
           sizeof(m_md.ReplyToQ));
    memcpy(m_md.ReplyToQ,
           pMainSrv->pInitSrv->m_MqQlBacenCidadeRep,
           pMainSrv->pInitSrv->m_MqQlBacenCidadeRep.GetLength());
    m_md.Encoding       = MQENC_NATIVE;
    m_md.CodedCharSetId = MQCCSI_Q_MGR;
	m_md.OriginalLength = m_buflen;

    memset(&m_pmo, '\0', sizeof(m_pmo));
    memcpy(m_pmo.StrucId, MQPMO_STRUC_ID,
           sizeof(m_pmo.StrucId));
    m_pmo.Version = MQPMO_VERSION_1;
    m_pmo.Options = MQPMO_SYNCPOINT;
 
	MontaBufferMQ(rs);

	MQPUT(m_Hcon,              /* connection handle               */
          m_Hobj,               /* object handle                   */
          &m_md,                /* message descriptor              */
          &m_pmo,               /* put options                     */
          m_buflen,             /* message length                  */
          m_buffermsg,          /* message buffer                  */
          &m_CompCode,          /* completion code                 */
          &m_Reason);           /* reason code                     */

	switch (m_CompCode)
    {
	    case MQCC_OK:
	         break;
		case MQCC_FAILED:
			 erro = true;
			 pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8030,FALSE,&m_Reason,&m_CompCode,NULL,NULL,NULL);
             switch (m_Reason)
			 {
                 case MQRC_Q_FULL:
					  pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8067,FALSE,&m_od.ObjectName,NULL,NULL,NULL,NULL);
                      break;
                 case MQRC_MSG_TOO_BIG_FOR_Q:
					  pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8068,FALSE,&m_od.ObjectName,NULL,NULL,NULL,NULL);
                      break;
                 default:
                      break; /* Perform error processing */
			 }
		     return erro;
		     break;
        default:
             break;          /* Perform error processing */
    }

     pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8061,TRUE,&pMainSrv->pInitSrv->m_QueueMgr,&pMainSrv->pInitSrv->m_MqQrCidadeBacenSup,&m_messlen,NULL,NULL);
	 DumpHeader(&m_md);
     pMainSrv->pInitSrv->m_WriteReg(m_szTaskName,TRUE,m_buflen,m_buffermsg);


	if (!erro)
	{
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
		    erro = true;
		}
	}
    if (!erro)
	{
		try
		{
			 m_pRS->Edit();
		}
		catch( CDBException * pEx )
		{
			TCHAR    szCause[255];
			char *   lpszCause = (char *)  &szCause;
			pEx->GetErrorMessage(szCause, 255);
			pEx->Delete( );
			pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8029,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)m_pRS->GetDefaultSQL(),lpszCause,NULL,NULL,NULL);
		    erro = true;
		}
	}

    if (!erro)
	{
		erro = UpdateDbRegApp();
	}
    if (!erro)
	{
		erro = MontaDbRegLog();
	}

    if (!erro)
	{
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
		    erro = true;
		}
	}
    if (!erro)
	{
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
		    erro = true;
		}
	}

    if (!erro)
	{
		UINT lenwrt = 0;
		BYTE *wrk;
		wrk = new BYTE[sizeof(STAUDITFILE)];
		pMainSrv->MontaAudit(lenwrt,wrk, &m_t, (BYTE *) &m_md , m_messlen, m_buffermsg);
		pMainSrv->WriteAudit(lenwrt,wrk);
		delete wrk;
	}

    if (erro)
	{
		try
		{
			if (m_pRS->GetRowStatus(1) == SQL_ROW_UPDATED)
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
			if (m_pRS->GetRowStatus(1) == SQL_ROW_UPDATED)
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
	return erro;
}


bool CIFSup::UpdateDbRegApp()
{
	bool rc = false;
	LPBYTE pbyte = NULL;;
	int i = 0;
	char wrk[25];
	CString datewrk;

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

	pbyte = (BYTE *) &m_md.MsgId;
    for ( i=0; i < sizeof(m_md.MsgId); i++) 
	{
        m_pRS->m_MQ_MSG_ID[i] = pbyte[i];
    }

//------------------------------------------------------------------------------------------
//  Status da Mensagem (S-SEND/X-Xml Erro/C-Cryptografia erro/R-Receive/P-Processado/E-Report
//------------------------------------------------------------------------------------------

	m_pRS->m_STATUS_MSG = "N";                

//------------------------------------------------------------------------------------------
//  Flag de processamento N-no insert / S-apos aplicativo ler
//------------------------------------------------------------------------------------------

	m_pRS->m_FLAG_PROC = "S";                

//------------------------------------------------------------------------------------------
//  Fila de destino do MQ
//------------------------------------------------------------------------------------------

	m_pRS->m_MQ_QN_DESTINO = pMainSrv->pInitSrv->m_MqQrCidadeBacenSup;

//------------------------------------------------------------------------------------------
//  Data e Hora do Put do MQ 
//------------------------------------------------------------------------------------------

	
	memset(&wrk,0x00,25);
	memcpy(&wrk,&m_md.PutDate,sizeof(m_md.PutDate));
	datewrk = wrk;
	memset(&wrk,0x00,25);
	memcpy(&wrk,&m_md.PutTime,sizeof(m_md.PutTime));
	datewrk += wrk;
	
	m_pRS->m_MQ_DATETIME_PUT.year	  = atoi(datewrk.Mid(0,4));
	m_pRS->m_MQ_DATETIME_PUT.month	  = atoi(datewrk.Mid(4,2));
	m_pRS->m_MQ_DATETIME_PUT.day	  = atoi(datewrk.Mid(6,2));
	m_pRS->m_MQ_DATETIME_PUT.hour	  = atoi(datewrk.Mid(8,2));
	m_pRS->m_MQ_DATETIME_PUT.minute   = atoi(datewrk.Mid(10,2));
	m_pRS->m_MQ_DATETIME_PUT.second   = atoi(datewrk.Mid(12,2));
	m_pRS->m_MQ_DATETIME_PUT.fraction = atoi(datewrk.Mid(14,2)) * 10;

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

	pbyte = (BYTE *) &m_md;


    for ( i=0; i < 512; i++) 
	{
        m_pRS->m_MQ_HEADER[i] = 0x00;
    }
    for ( i=0; i < sizeof(MQMD); i++) 
	{
        m_pRS->m_MQ_HEADER[i] = pbyte[i];
    }

	m_pRS->m_COD_MSG = "SUPORTE";

	return rc;
}

bool CIFSup::MontaDbRegLog()
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

	m_pRSLog->m_DB_DATETIME = m_pRS->m_DB_DATETIME;

//------------------------------------------------------------------------------------------
//  Status da Mensagem (N-Normal/X-Xml Erro/D-Decryptografia erro
//------------------------------------------------------------------------------------------

	m_pRSLog->m_STATUS_MSG = m_pRS->m_STATUS_MSG;

//------------------------------------------------------------------------------------------
//  Fila de origem MQ
//------------------------------------------------------------------------------------------

	m_pRSLog->m_MQ_QN_ORIGEM = pMainSrv->pInitSrv->m_MqQrCidadeBacenSup;

	
//------------------------------------------------------------------------------------------
//  Data e Hora do Put do MQ 
//------------------------------------------------------------------------------------------

	memset(&wrk,0x00,25);
	memcpy(&wrk,&m_md.PutDate,sizeof(m_md.PutDate));
	datewrk = wrk;
	memset(&wrk,0x00,25);
	memcpy(&wrk,&m_md.PutTime,sizeof(m_md.PutTime));
	datewrk += wrk;
	
	m_pRSLog->m_MQ_DATETIME.year	    = atoi(datewrk.Mid(0,4));
	m_pRSLog->m_MQ_DATETIME.month	    = atoi(datewrk.Mid(4,2));
	m_pRSLog->m_MQ_DATETIME.day			= atoi(datewrk.Mid(6,2));
	m_pRSLog->m_MQ_DATETIME.hour	    = atoi(datewrk.Mid(8,2));
	m_pRSLog->m_MQ_DATETIME.minute      = atoi(datewrk.Mid(10,2));
	m_pRSLog->m_MQ_DATETIME.second      = atoi(datewrk.Mid(12,2));
	m_pRSLog->m_MQ_DATETIME.fraction    = atoi(datewrk.Mid(14,2)) * 10;

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


	m_pRSLog->m_COD_MSG = "SUPORTE";

    m_pRSLog->m_MSG = m_pRS->m_MSG;

	return rc;
}

bool CIFSup::MontaBufferMQ(CIFAppRS *rs)
{
	m_messlen = 0;

	if (rs->m_MSG.GetLength() > 0)
	{
		memcpy(&m_buffermsg[m_messlen],rs->m_MSG,rs->m_MSG.GetLength());
	}
	else
	{
		CString wrk = "SPBMSG";
		pMainSrv->pInitSrv->m_WriteLog(m_szTaskName,8065,FALSE,(LPVOID)(LPTSTR)(LPCTSTR)wrk,NULL,NULL,NULL,NULL);
		return true;
	}
	m_messlen += rs->m_MSG.GetLength();

    m_buflen = m_messlen;

	return false;
}