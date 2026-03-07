#if !defined(AFX_BACENREQ_H__7F75E7A1_6449_11D3_A8A0_00104B2375F6__INCLUDED_)
#define AFX_BACENREQ_H__7F75E7A1_6449_11D3_A8A0_00104B2375F6__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000
// BacenReq.h : header file
//

class CBacenReq : public CThreadMQ
{
public:
	CBacenReq(LPCTSTR lpszName, bool AutomaticThread, int HandleMQ, CMainSrv *MainSrv) 
		: CThreadMQ(lpszName, AutomaticThread, HandleMQ, MainSrv) {};
	void	RunThread(LPVOID MainSrv);
	void	ProcessaQueue();
	bool	UpdateDB();
	bool	MontaDbRegApp();
	bool	MontaDbRegLog();
	bool	ChecarXml();
	bool	CheckAssDeCryptBufferMQ();
	bool	AtualizaCtr();
	bool	ReadCtr();
	bool	FuncEco();
	bool	FuncLog();
	bool	FuncUltMsg();
	bool	GeraEcoR1(CString& xml);
	bool	GeraUltMsgR1(CString& xml);
	bool	GeraLogR1(CString& NUOpLog,CString& xml);
	bool	GeraReport();

public:
	bool RunInitDBeMQ();
	bool RunTermDBeMQ();
	CBCDatabase *m_pDb1;
	CBCDatabase *m_pDb2;
	CBCDatabase *m_pDb3;
	CBCDatabase *m_pDb4;
	CBacenAppRS *m_pRS;
	CSTRLogRS   *m_pRSLog;
	CControleRS *m_pRSCtr;
	CIFAppRS	*m_pRSApp;

    MQOD     m_od;					  /* Object Descriptor             */
    MQMD     m_md;					  /* Message Descriptor            */
    MQGMO    m_gmo;					  /* get message options           */
	MQBO	 m_bo;                    /* begin options             */

    MQHCONN  m_Hcon;                  /* connection handle             */
    MQHOBJ   m_Hobj;                  /* object handle                 */
    MQLONG   m_O_options;             /* MQOPEN options                */
    MQLONG   m_C_options;             /* MQCLOSE options               */
    MQLONG   m_CompCode;              /* completion code               */
    MQLONG   m_OpenCode;              /* MQOPEN completion code        */
    MQLONG   m_Reason;                /* reason code                   */
    MQLONG   m_CReason;               /* reason code for MQCONN        */
    MQBYTE*  m_buffermsg;             /* message buffer                */
    MQLONG   m_buflen;                /* buffer length                 */
    MQLONG   m_messlen;               /* message length received       */
    char     m_QMName[50];            /* queue manager name            */
	SYSTEMTIME m_t;
	CString  m_NuOpe;
	CString  m_CodMsg;
	CString  m_TipoIdEmissor;
	CString  m_IdEmissor;
	CString  m_TipoIdDestinatario;
	CString  m_IdDestinatario;
	CString	 m_StatusMsg;
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_BACENREQ_H__7F75E7A1_6449_11D3_A8A0_00104B2375F6__INCLUDED_)
