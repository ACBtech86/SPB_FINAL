// CControleRS.cpp : implementation file
//
// Fase 6: Removido #define _WIN32_WINNT 0x0400 (obsoleto, definido pelo CMake)
 
#include <afxdb.h>
#include "CBCDb.h"
#include "ControleRS.h"
#include "MsgSgr.h"


/////////////////////////////////////////////////////////////////////////////
// CControleRS

IMPLEMENT_DYNAMIC(CControleRS, CRecordset)

CControleRS::CControleRS(CDatabase* pdb,CString TblName)
	: CRecordset(pdb)
{
	CBCDatabase * pbcdb = (CBCDatabase *) pdb;
	m_sDbName		= pbcdb->m_sDbName;
	m_sMQServer		= pbcdb->m_sMQServer;
	m_iPorta		= pbcdb->m_iPorta;
	m_iMaxLenMsg	= pbcdb->m_iMaxLenMsg;
	m_sTblName		= TblName;
//	CString strMutex = "Mutex=" + m_sTblName;
	m_islock		= FALSE;
//	m_mutex			= CreateMutex(NULL,FALSE,(LPCTSTR) strMutex );
	//{{AFX_FIELD_INIT(CControleRS)
	//}}AFX_FIELD_INIT
	CString				m_ParamISPB;
	
	m_ISPB.Empty();
	m_NOME_ISPB.Empty();
//	m_MSG_SEQ		= 0;
	m_STATUS_GERAL.Empty();
//	m_STATUS_CONECT.Empty();
//	m_DTHR_CONECT.year		= 0;
//	m_DTHR_CONECT.month		= 0;
//	m_DTHR_CONECT.day		= 0;
//	m_DTHR_CONECT.hour		= 0;
//	m_DTHR_CONECT.minute	= 0;
//	m_DTHR_CONECT.second	= 0;
//	m_DTHR_CONECT.fraction	= 0;
//	m_DTHR_DESCON.year		= 0;
//	m_DTHR_DESCON.month		= 0;
//	m_DTHR_DESCON.day		= 0;
//	m_DTHR_DESCON.hour		= 0;
//	m_DTHR_DESCON.minute	= 0;
//	m_DTHR_DESCON.second	= 0;
//	m_DTHR_DESCON.fraction	= 0;
	m_DTHR_ECO.year			= 0;
	m_DTHR_ECO.month		= 0;
	m_DTHR_ECO.day			= 0;
	m_DTHR_ECO.hour			= 0;
	m_DTHR_ECO.minute		= 0;
	m_DTHR_ECO.second		= 0;
	m_DTHR_ECO.fraction		= 0;
	m_ULTMSG.Empty();
	m_DTHR_ULTMSG.year		= 0;
	m_DTHR_ULTMSG.month		= 0;
	m_DTHR_ULTMSG.day		= 0;
	m_DTHR_ULTMSG.hour		= 0;
	m_DTHR_ULTMSG.minute	= 0;
	m_DTHR_ULTMSG.second	= 0;
	m_DTHR_ULTMSG.fraction	= 0;
	m_CERTIFICADORA.Empty();

	m_nFields = 11 - 1 - 3 ; // retirando numero de sequencia

	m_ParamISPB.Empty();

	m_nParams = 1;

	m_sDrop		=	"DROP TABLE ";
	m_sDrop		+=	GetDefaultSQL();

	m_sCreate	=	"CREATE TABLE ";
	m_sCreate	+=	GetDefaultSQL();
	m_sCreate	+=	" (									    			";
    m_sCreate	+=	" ispb            VARCHAR(8)             NOT NULL,	";
    m_sCreate	+=	" nome_ispb       VARCHAR(15)            NOT NULL,	";
    m_sCreate	+=	" msg_seq         SMALLINT                   NULL,	";
    m_sCreate	+=	" status_geral    CHAR(1)                NOT NULL,	";
//    m_sCreate	+=	" status_conect   CHAR(1)                NOT NULL,	";
//    m_sCreate	+=	" dthr_conect     TIMESTAMP                  NULL,	";
//    m_sCreate	+=	" dthr_descon     TIMESTAMP                  NULL,	";
    m_sCreate	+=	" dthr_eco        TIMESTAMP                  NULL,	";
    m_sCreate	+=	" ultmsg          VARCHAR(23)                NULL,	";
    m_sCreate	+=	" dthr_ultmsg     TIMESTAMP                  NULL,	";
    m_sCreate	+=	" certificadora   VARCHAR(50)                NULL,	";
	m_sCreate	+=	" )											   	    ";

	m_sPriKey	=	" ALTER TABLE ";
	m_sPriKey	+=	GetDefaultSQL();
	m_sPriKey	+=	" ADD	";
	m_sPriKey	+=	" CONSTRAINT pk_";
	m_sPriKey	+=	GetDefaultSQL();
	m_sPriKey	+=	" PRIMARY KEY	";
	m_sPriKey	+=	" (													";
    m_sPriKey	+=	" ispb  	    		        			    	";
	m_sPriKey	+=	" )													";

}

CControleRS::~CControleRS()
{
//	if (m_mutex)
//	{
//		ReleaseMutex(m_mutex);
//		CloseHandle(m_mutex);
		m_islock		= FALSE;
//	}
//	m_mutex			= NULL;
}

BOOL CControleRS::Islock()
{
	return m_islock;
}

BOOL CControleRS::Lock()
{
//	if (m_mutex)
//	{
//		WaitForSingleObject(m_mutex, INFINITE);
		m_islock		= TRUE;
//	}
	return false;
}

BOOL CControleRS::Unlock()
{
//	if (m_mutex)
//	{
//		ReleaseMutex(m_mutex);
//	}
	m_islock		= FALSE;
	return false;
}


CString CControleRS::GetDefaultConnect()
{
	return m_sDbName;
}

CString CControleRS::GetDefaultSQL()
{
	return m_sTblName;
}

void CControleRS::DoFieldExchange(CFieldExchange* pFX)
{
	//{{AFX_FIELD_MAP(CControleRS)
	pFX->SetFieldType(CFieldExchange::outputColumn);
	//}}AFX_FIELD_MAP
	RFX_Text  (pFX, _T("ispb")		    	,m_ISPB);
	RFX_Text  (pFX, _T("nome_ispb")	    	,m_NOME_ISPB);
//	RFX_Int   (pFX, _T("msg_seq")		    ,m_MSG_SEQ);
	RFX_Text  (pFX, _T("status_geral")		,m_STATUS_GERAL);
//	RFX_Text  (pFX, _T("status_conect")		,m_STATUS_CONECT);
//	RFX_Date  (pFX, _T("dthr_conect")		,m_DTHR_CONECT);
//	RFX_Date  (pFX, _T("dthr_descon")		,m_DTHR_DESCON);
	RFX_Date  (pFX, _T("dthr_eco")			,m_DTHR_ECO);
	RFX_Text  (pFX, _T("ultmsg")			,m_ULTMSG);
	RFX_Date  (pFX, _T("dthr_ultmsg")		,m_DTHR_ULTMSG);
	RFX_Text  (pFX, _T("certificadora")		,m_CERTIFICADORA);
	if (m_nParams == 1)
	{
		pFX->SetFieldType( CFieldExchange::param );
		RFX_Text(pFX, _T("ispb")			,m_ParamISPB);
	}
}

/////////////////////////////////////////////////////////////////////////////
// CControleRS diagnostics

#ifdef _DEBUG
void CControleRS::AssertValid() const
{
	CRecordset::AssertValid();
}

void CControleRS::Dump(CDumpContext& dc) const
{
	CRecordset::Dump(dc);
}
#endif //_DEBUG
