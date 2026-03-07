// CBacenAppRS.cpp : implementation file
//
// Fase 6: Removido #define _WIN32_WINNT 0x0400 (obsoleto, definido pelo CMake)
 
#include <afxdb.h>
#include "CBCDb.h"
#include "BacenAppRS.h"
#include "MsgSgr.h"


/////////////////////////////////////////////////////////////////////////////
// CBacenAppRS

IMPLEMENT_DYNAMIC(CBacenAppRS, CRecordset)

CBacenAppRS::CBacenAppRS(CDatabase* pdb,CString TblName)
	: CRecordset(pdb)
{
	CBCDatabase * pbcdb = (CBCDatabase *) pdb;
	m_sDbName		= pbcdb->m_sDbName;
	m_sMQServer		= pbcdb->m_sMQServer;
	m_iPorta		= pbcdb->m_iPorta;
	m_iMaxLenMsg	= pbcdb->m_iMaxLenMsg;
	m_sTblName		= TblName;
	//{{AFX_FIELD_INIT(CBacenAppRS)
	//}}AFX_FIELD_INIT
    m_MQ_MSG_ID.RemoveAll();
    m_MQ_CORREL_ID.RemoveAll();
	m_DB_DATETIME.year	  = 0;
	m_DB_DATETIME.month	  = 0;
	m_DB_DATETIME.day	  = 0;
	m_DB_DATETIME.hour	  = 0;
	m_DB_DATETIME.minute  = 0;
	m_DB_DATETIME.second  = 0;
	m_DB_DATETIME.fraction = 0;
	m_STATUS_MSG.Empty();
	m_FLAG_PROC.Empty();
	m_MQ_QN_ORIGEM.Empty();
	m_MQ_DATETIME.year	  = 0;
	m_MQ_DATETIME.month	  = 0;
	m_MQ_DATETIME.day	  = 0;
	m_MQ_DATETIME.hour	  = 0;
	m_MQ_DATETIME.minute  = 0;
	m_MQ_DATETIME.second  = 0;
	m_MQ_DATETIME.fraction = 0;
    m_MQ_HEADER.RemoveAll();
    m_SECURITY_HEADER.RemoveAll();
	m_NU_OPE.Empty();
	m_COD_MSG.Empty();
    m_MSG.Empty();

	m_nFields = 12;

	m_ParamMQ_MSG_ID.RemoveAll();
	m_ParamNU_OPE.Empty();

	m_nParams = 1;
	m_index	  = 0;

	m_sDrop		=	"DROP TABLE ";
	m_sDrop		+=	GetDefaultSQL();

	m_sCreate	=	"CREATE TABLE ";
	m_sCreate	+=	GetDefaultSQL();
	m_sCreate	+=	" (									    			";
    m_sCreate	+=	" mq_msg_id       BYTEA                 NOT NULL,	";
    m_sCreate	+=	" mq_correl_id    BYTEA                 NOT NULL,	";
    m_sCreate	+=	" db_datetime     TIMESTAMP             NOT NULL,	";
    m_sCreate	+=	" status_msg      CHAR(1)               NOT NULL,	";
    m_sCreate	+=	" flag_proc       CHAR(1)               NOT NULL,	";
    m_sCreate	+=	" mq_qn_origem    VARCHAR(48)           NOT NULL,	";
    m_sCreate	+=	" mq_datetime     TIMESTAMP             NOT NULL,	";
    m_sCreate	+=	" mq_header       BYTEA                 NOT NULL,	";
    m_sCreate	+=	" security_header BYTEA                 NOT NULL,	";
    m_sCreate	+=	" nu_ope          VARCHAR(23)               NULL,	";
    m_sCreate	+=	" cod_msg         VARCHAR(9)                NULL,	";
    m_sCreate	+=	" msg             TEXT                       NULL 	";
	m_sCreate	+=	" )											   	";

	m_sPriKey	=	" ALTER TABLE ";
	m_sPriKey	+=	GetDefaultSQL();
	m_sPriKey	+=	" ADD	";
	m_sPriKey	+=	" CONSTRAINT pk_";
	m_sPriKey	+=	GetDefaultSQL();
	m_sPriKey	+=	" PRIMARY KEY	";
	m_sPriKey	+=	" (													";
    m_sPriKey	+=	" db_datetime,	    					    		";
    m_sPriKey	+=	" mq_msg_id   	    					    		";
	m_sPriKey	+=	" )													";

	m_sIndex1	=	" CREATE  INDEX ix1_";
	m_sIndex1	+=	GetDefaultSQL();
	m_sIndex1	+=	" ON ";
	m_sIndex1	+=	GetDefaultSQL();
	m_sIndex1	+=	"(													";
    m_sIndex1	+=	" nu_ope		    						    	";
	m_sIndex1	+=	" )													";

	m_sIndex2	=	" CREATE  INDEX ix2_";
	m_sIndex2	+=	GetDefaultSQL();
	m_sIndex2	+=	" ON ";
	m_sIndex2	+=	GetDefaultSQL();
	m_sIndex2	+=	"(													";
    m_sIndex2	+=	" flag_proc, 		    					    	";
    m_sIndex2	+=	" mq_qn_origem		    				    		";
	m_sIndex2	+=	" )													";
}

CBacenAppRS::~CBacenAppRS()
{
    m_MQ_MSG_ID.RemoveAll();
    m_MQ_CORREL_ID.RemoveAll();
    m_MQ_HEADER.RemoveAll();
    m_SECURITY_HEADER.RemoveAll();
}

CString CBacenAppRS::GetDefaultConnect()
{
	return m_sDbName;
}

CString CBacenAppRS::GetDefaultSQL()
{
	return m_sTblName;
}

void CBacenAppRS::DoFieldExchange(CFieldExchange* pFX)
{
	//{{AFX_FIELD_MAP(CBacenAppRS)
	pFX->SetFieldType(CFieldExchange::outputColumn);
	//}}AFX_FIELD_MAP
	RFX_Binary(pFX, _T("mq_msg_id")			,m_MQ_MSG_ID,24);
	RFX_Binary(pFX, _T("mq_correl_id")		,m_MQ_CORREL_ID,24);
	RFX_Date  (pFX, _T("db_datetime")		,m_DB_DATETIME);
	RFX_Text  (pFX, _T("status_msg")		,m_STATUS_MSG);
	RFX_Text  (pFX, _T("flag_proc")			,m_FLAG_PROC);
	RFX_Text  (pFX, _T("mq_qn_origem")		,m_MQ_QN_ORIGEM);
	RFX_Date  (pFX, _T("mq_datetime")		,m_MQ_DATETIME);
	RFX_Binary(pFX, _T("mq_header")			,m_MQ_HEADER,512);
	RFX_Binary(pFX, _T("security_header")	,m_SECURITY_HEADER,332);
	RFX_Text  (pFX, _T("nu_ope")			,m_NU_OPE);
	RFX_Text  (pFX, _T("cod_msg")			,m_COD_MSG);
    RFX_Text  (pFX, _T("msg")				,m_MSG, m_iMaxLenMsg, SQL_LONGVARCHAR,0);
	if (m_index == 1)
	{
		m_nParams = 1;
		pFX->SetFieldType( CFieldExchange::param );
		RFX_Binary(pFX, _T("mq_msg_id")		,m_ParamMQ_MSG_ID,24);
	}
	if (m_index == 2)
	{
		m_nParams = 1;
		pFX->SetFieldType( CFieldExchange::param );
		RFX_Text  (pFX, _T("nu_ope"),       m_ParamNU_OPE);
	}
}

/////////////////////////////////////////////////////////////////////////////
// CBacenAppRS diagnostics

#ifdef _DEBUG
void CBacenAppRS::AssertValid() const
{
	CRecordset::AssertValid();
}

void CBacenAppRS::Dump(CDumpContext& dc) const
{
	CRecordset::Dump(dc);
}
#endif //_DEBUG
