#if !defined(AFX_ControleRS_H__7F75E7A1_6449_11D3_A8A0_00104B2375F6__INCLUDED_)
#define AFX_ControleRS_H__7F75E7A1_6449_11D3_A8A0_00104B2375F6__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000
// ControleRS.h : header file
//

/////////////////////////////////////////////////////////////////////////////
// CBacenReq recordset

class CControleRS : public CRecordset
{
public:
	CControleRS(CDatabase* pDatabase = NULL,CString TblName = "");
	~CControleRS();
	DECLARE_DYNAMIC(CControleRS)
	BOOL Lock();
	BOOL Unlock();
	BOOL Islock();

	// Field/Param Data
	//{{AFX_FIELD(CControleRS, CRecordset)
	//}}AFX_FIELD
	CString				m_sTblName;

	CString				m_ParamISPB;
	
	CString		        m_ISPB;
	CString		        m_NOME_ISPB;
//	int					m_MSG_SEQ;
	CString		        m_STATUS_GERAL;
//	CString		        m_STATUS_CONECT;
//	TIMESTAMP_STRUCT	m_DTHR_CONECT;
//	TIMESTAMP_STRUCT	m_DTHR_DESCON;
	TIMESTAMP_STRUCT	m_DTHR_ECO;
	CString		        m_ULTMSG;
	TIMESTAMP_STRUCT	m_DTHR_ULTMSG;
	CString				m_CERTIFICADORA;
//	CString				m_NUM_CERTIFICADO;

	CString				m_sDrop;
	CString				m_sCreate;
	CString				m_sPriKey;
	CString				m_sDbName;
	CString				m_sMQServer;
	int					m_iPorta;
	int					m_iMaxLenMsg;

//	HANDLE				m_mutex;
	BOOL				m_islock;

// Overrides
	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CControleRS)
	public:
	virtual CString GetDefaultConnect();    // Default connection string
	virtual CString GetDefaultSQL();    // Default SQL for Recordset
	virtual void DoFieldExchange(CFieldExchange* pFX);  // RFX support
	//}}AFX_VIRTUAL

// Implementation
#ifdef _DEBUG
	virtual void AssertValid() const;
	virtual void Dump(CDumpContext& dc) const;
#endif
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif 