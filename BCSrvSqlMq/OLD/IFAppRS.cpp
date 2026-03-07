// CIFAppRS.cpp : implementation file

// Fase 6: Removido #define _WIN32_WINNT 0x0400 (obsoleto, definido pelo CMake)

#include <afxdb.h>
#include "MsgSgr.h"
#include "CBCDb.h"
#include "IFAppRS.h"


/////////////////////////////////////////////////////////////////////////////
// CIFAppRS

IMPLEMENT_DYNAMIC(CIFAppRS, CRecordset)

CIFAppRS::CIFAppRS(CDatabase* pdb,CString TblName)
	: CRecordset(pdb)
{
	CBCDatabase * pbcdb = (CBCDatabase *) pdb;
	m_sDbName		= pbcdb->m_sDbName;
	m_sMQServer		= pbcdb->m_sMQServer;
	m_iPorta		= pbcdb->m_iPorta;
	m_iMaxLenMsg	= pbcdb->m_iMaxLenMsg;
	m_sTblName		= TblName;


	//{{AFX_FIELD_INIT(CIFAppRS)
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
    m_MQ_QN_DESTINO.Empty();
	m_MQ_DATETIME_PUT.year	  = 0;
	m_MQ_DATETIME_PUT.month	  = 0;
	m_MQ_DATETIME_PUT.day	  = 0;
	m_MQ_DATETIME_PUT.hour	  = 0;
	m_MQ_DATETIME_PUT.minute  = 0;
	m_MQ_DATETIME_PUT.second  = 0;
	m_MQ_DATETIME_PUT.fraction = 0;
    m_MQ_MSG_ID_COA.RemoveAll();
	m_MQ_DATETIME_COA.year	  = 0;
	m_MQ_DATETIME_COA.month	  = 0;
	m_MQ_DATETIME_COA.day	  = 0;
	m_MQ_DATETIME_COA.hour	  = 0;
	m_MQ_DATETIME_COA.minute  = 0;
	m_MQ_DATETIME_COA.second  = 0;
	m_MQ_DATETIME_COA.fraction = 0;
    m_MQ_MSG_ID_COD.RemoveAll();
	m_MQ_DATETIME_REP.year	  = 0;
	m_MQ_DATETIME_REP.month	  = 0;
	m_MQ_DATETIME_REP.day	  = 0;
	m_MQ_DATETIME_REP.hour	  = 0;
	m_MQ_DATETIME_REP.minute  = 0;
	m_MQ_DATETIME_REP.second  = 0;
	m_MQ_DATETIME_REP.fraction = 0;
    m_MQ_MSG_ID_REP.RemoveAll();
    m_MQ_HEADER.RemoveAll();
    m_SECURITY_HEADER.RemoveAll();
	m_NU_OPE.Empty();
	m_COD_MSG.Empty();
    m_MSG.Empty();

	m_nFields = 19;

	m_ParamNU_OPE.Empty();
	m_ParamMQ_QN_DESTINO.Empty();
	m_ParamFLAG_PROC.Empty();
    m_ParamMQ_MSG_ID.RemoveAll();
	m_index   = 0;
	m_nParams = 0;
	
	m_sDrop		=	"DROP TABLE ";
	m_sDrop		+=	GetDefaultSQL();

	m_sCreate	=	"CREATE TABLE ";
	m_sCreate	+=	GetDefaultSQL();
	m_sCreate	+=	" (									    		";
    m_sCreate	+=	" mq_msg_id       BYTEA						NULL,	";
    m_sCreate	+=	" mq_correl_id    BYTEA        				NULL,	";
    m_sCreate	+=	" db_datetime     TIMESTAMP             NOT NULL,	";
    m_sCreate	+=	" status_msg      CHAR(1)               NOT NULL,	";
    m_sCreate	+=	" flag_proc       CHAR(1)               NOT NULL,	";
    m_sCreate	+=	" mq_qn_destino   VARCHAR(48)           NOT NULL,	";
    m_sCreate	+=	" mq_datetime_put TIMESTAMP   	    		NULL,	";
    m_sCreate	+=	" mq_msg_id_coa   BYTEA						NULL,	";
    m_sCreate	+=	" mq_datetime_coa TIMESTAMP	    			NULL,	";
    m_sCreate	+=	" mq_msg_id_cod   BYTEA						NULL,	";
    m_sCreate	+=	" mq_datetime_cod TIMESTAMP	    			NULL,	";
    m_sCreate	+=	" mq_msg_id_rep   BYTEA						NULL,	";
    m_sCreate	+=	" mq_datetime_rep TIMESTAMP	    			NULL,	";
    m_sCreate	+=	" mq_header       BYTEA						NULL,	";
    m_sCreate	+=	" security_header BYTEA		       			NULL,	";
    m_sCreate	+=	" nu_ope          VARCHAR(23)        		NULL,	";
    m_sCreate	+=	" msg_len         INTEGER					NULL,	";
    m_sCreate	+=	" cod_msg         VARCHAR(9)            NOT NULL,	";
    m_sCreate	+=	" msg             TEXT	                	NULL	";
	m_sCreate	+=	" )											   	";

	m_sPriKey	=	" ALTER TABLE ";
	m_sPriKey	+=	GetDefaultSQL();
	m_sPriKey	+=	" ADD	";
	m_sPriKey	+=	" CONSTRAINT pk_";
	m_sPriKey	+=	GetDefaultSQL();
	m_sPriKey	+=	" PRIMARY KEY	";
	m_sPriKey	+=	" (													";
    m_sPriKey	+=	" db_datetime , 		    				    	";
    m_sPriKey	+=	" cod_msg ,			    					    	";
    m_sPriKey	+=	" mq_qn_destino    	    						   	";
	m_sPriKey	+=	" )													";

	m_sIndex1	=	" CREATE  INDEX ix1_";
	m_sIndex1	+=	GetDefaultSQL();
	m_sIndex1	+=	" ON ";
	m_sIndex1	+=	GetDefaultSQL();
	m_sIndex1	+=	"(													";
    m_sIndex1	+=	" mq_msg_id   	    					    		";
	m_sIndex1	+=	" )													";

	m_sIndex2	=	" CREATE  INDEX ix2_";
	m_sIndex2	+=	GetDefaultSQL();
	m_sIndex2	+=	" ON ";
	m_sIndex2	+=	GetDefaultSQL();
	m_sIndex2	+=	"(													";
    m_sIndex2	+=	" mq_qn_destino , 	    					   		";
    m_sIndex2	+=	" flag_proc   	    					    		";
	m_sIndex2	+=	" )													";

	m_sIndex3	=	" CREATE  INDEX ix3_";
	m_sIndex3	+=	GetDefaultSQL();
	m_sIndex3	+=	" ON ";
	m_sIndex3	+=	GetDefaultSQL();
	m_sIndex3	+=	"(													";
    m_sIndex3	+=	" nu_ope   	    					    			";
	m_sIndex3	+=	" )													";

	m_sTrigger	=	"CREATE TRIGGER [TRIGGER_"; 
	m_sTrigger	+=	GetDefaultSQL();
	m_sTrigger	+=	"] ON ";
	m_sTrigger	+=	GetDefaultSQL();
	m_sTrigger	+=	"\r\n";
    m_sTrigger	+=	"FOR INSERT AS ";
	m_sTrigger	+=	"\r\n";
    m_sTrigger	+=	"declare @server varchar(15), @porta integer , @queuename varchar(48), @result int ";
	m_sTrigger	+=	"\r\n";
    m_sTrigger	+=	"set @server = '";
    m_sTrigger	+=	m_sMQServer;
    m_sTrigger	+=	"'";
	m_sTrigger	+=	"\r\n";
    m_sTrigger	+=	"set @porta = ";
	char szSrvPorta[10];
	_itoa(m_iPorta,szSrvPorta,10);
    m_sTrigger	+=	szSrvPorta;
	m_sTrigger	+=	"\r\n";
    m_sTrigger	+=	"select @queuename = i.MQ_QN_DESTINO from inserted i ";
	m_sTrigger	+=	"\r\n";
    m_sTrigger	+=	"exec @result = master..xp_sqltomq @server, @porta, @queuename ";
	m_sTrigger	+=	"\r\n";
    m_sTrigger	+=	"if @result > 0 ";
	m_sTrigger	+=	"\r\n";
    m_sTrigger	+=	"begin ";
	m_sTrigger	+=	"\r\n";
    m_sTrigger	+=	"    RAISERROR ('Erro na Comnica��o TCPIP com servi�o SPB', 16,1) WITH LOG ";
	m_sTrigger	+=	"\r\n";
    m_sTrigger	+=	"    ROLLBACK TRANSACTION ";
	m_sTrigger	+=	"\r\n";
    m_sTrigger	+=	"end ";
}

CIFAppRS::~CIFAppRS()
{
    m_ParamMQ_MSG_ID.RemoveAll();
    m_MQ_MSG_ID.RemoveAll();
    m_MQ_CORREL_ID.RemoveAll();
    m_MQ_MSG_ID_COA.RemoveAll();
    m_MQ_MSG_ID_COD.RemoveAll();
    m_MQ_MSG_ID_REP.RemoveAll();
    m_MQ_HEADER.RemoveAll();
    m_SECURITY_HEADER.RemoveAll();
}

CString CIFAppRS::GetDefaultConnect()
{
	return m_sDbName;
}

CString CIFAppRS::GetDefaultSQL()
{
	return m_sTblName;
}

void CIFAppRS::DoFieldExchange(CFieldExchange* pFX)
{
	//{{AFX_FIELD_MAP(CIFAppRS)
	pFX->SetFieldType(CFieldExchange::outputColumn);
	//}}AFX_FIELD_MAP
	RFX_Binary(pFX, _T("mq_msg_id")			,m_MQ_MSG_ID,24);
	RFX_Binary(pFX, _T("mq_correl_id")		,m_MQ_CORREL_ID,24);
	RFX_Date  (pFX, _T("db_datetime")		,m_DB_DATETIME);
	RFX_Text  (pFX, _T("status_msg")		,m_STATUS_MSG);
	RFX_Text  (pFX, _T("flag_proc")			,m_FLAG_PROC);
	RFX_Text  (pFX, _T("mq_qn_destino")		,m_MQ_QN_DESTINO);
	RFX_Date  (pFX, _T("mq_datetime_put")	,m_MQ_DATETIME_PUT);
	RFX_Binary(pFX, _T("mq_msg_id_coa")		,m_MQ_MSG_ID_COA,24);
	RFX_Date  (pFX, _T("mq_datetime_coa")	,m_MQ_DATETIME_COA);
	RFX_Binary(pFX, _T("mq_msg_id_cod")		,m_MQ_MSG_ID_COD,24);
	RFX_Date  (pFX, _T("mq_datetime_cod")	,m_MQ_DATETIME_COD);
	RFX_Binary(pFX, _T("mq_msg_id_rep")		,m_MQ_MSG_ID_REP,24);
	RFX_Date  (pFX, _T("mq_datetime_rep")	,m_MQ_DATETIME_REP);
	RFX_Binary(pFX, _T("mq_header")			,m_MQ_HEADER,512);
	RFX_Binary(pFX, _T("security_header")	,m_SECURITY_HEADER,332);
	RFX_Text  (pFX, _T("nu_ope")			,m_NU_OPE);
	RFX_Int   (pFX, _T("msg_len")			,m_MSG_LEN);
	RFX_Text  (pFX, _T("cod_msg")			,m_COD_MSG);
    RFX_Text  (pFX, _T("msg")	    		,m_MSG,m_iMaxLenMsg, SQL_LONGVARCHAR,0);
	if (m_index == 1)
	{
		m_nParams = 1;
		pFX->SetFieldType( CFieldExchange::param );
		RFX_Binary(pFX, _T("mq_msg_id"),	 m_ParamMQ_MSG_ID,24);
	}
	if (m_index == 2)
	{
		m_nParams = 2;
		pFX->SetFieldType( CFieldExchange::param );
		RFX_Text  (pFX, _T("mq_qn_destino"), m_ParamMQ_QN_DESTINO);
		RFX_Text  (pFX, _T("flag_proc"),     m_ParamFLAG_PROC);
	}
	if (m_index == 3)
	{
		m_nParams = 1;
		pFX->SetFieldType( CFieldExchange::param );
		RFX_Text  (pFX, _T("nu_ope"),		 m_ParamNU_OPE);
	}
}

/////////////////////////////////////////////////////////////////////////////
// CIFAppRS diagnostics

#ifdef _DEBUG
void CIFAppRS::AssertValid() const
{
	CRecordset::AssertValid();
}

void CIFAppRS::Dump(CDumpContext& dc) const
{
	CRecordset::Dump(dc);
}
#endif //_DEBUG
