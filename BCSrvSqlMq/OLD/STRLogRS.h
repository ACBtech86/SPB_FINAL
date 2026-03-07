#if !defined(AFX_STRLOGRS_H__7F75E7A1_6449_11D3_A8A0_00104B2375F6__INCLUDED_)
#define AFX_STRLOGRS_H__7F75E7A1_6449_11D3_A8A0_00104B2375F6__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000
// STRLogRS.h : header file
//

/////////////////////////////////////////////////////////////////////////////
// CBacenReq recordset

class CSTRLogRS : public CRecordset
{
public:
	CSTRLogRS(CDatabase* pDatabase = NULL,CString TblName = "");
	~CSTRLogRS();
	DECLARE_DYNAMIC(CSTRLogRS)

// Field/Param Data
	//{{AFX_FIELD(CSTRLogRS, CRecordset)
	//}}AFX_FIELD
	CString				m_sTblName;

	CByteArray			m_ParamMQ_MSG_ID;
	CString				m_ParamNU_OPE;
	
	CByteArray		 	m_MQ_MSG_ID;
	CByteArray		 	m_MQ_CORREL_ID;
	TIMESTAMP_STRUCT	m_DB_DATETIME;
	CString				m_STATUS_MSG;
	CString				m_MQ_QN_ORIGEM;
	TIMESTAMP_STRUCT	m_MQ_DATETIME;
	CByteArray		 	m_MQ_HEADER;
	CByteArray			m_SECURITY_HEADER;
	CString				m_NU_OPE;
	CString				m_COD_MSG;
    CString				m_MSG;

	CString				m_sDrop;
	CString				m_sCreate;
	CString				m_sPriKey;
	CString				m_sIndex1;
	CString				m_sDbName;
	CString				m_sMQServer;
	int					m_iPorta;
	int					m_iMaxLenMsg;


// Overrides
	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CSTRLogRS)
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