// CBCDb.h

#ifndef _CBCDB_H_
#define _CBCDB_H_

class CBCDatabase : public CDatabase
{
public:
	CBCDatabase();

	// Legacy constructor - now builds DSN-less connection string from InitSrv parameters
	CBCDatabase(CString DbName,CString MQServer,int Porta,int MaxLenMsg)
	{
		// DbName now contains the full DSN-less connection string (built in InitSrv)
		m_sDbName		= DbName;
		m_sMQServer		= MQServer;
		m_iPorta		= Porta;
		m_iMaxLenMsg	= MaxLenMsg;
		::CDatabase();
	};

	void SetTransactions() {m_bTransactions = TRUE;};

	CString m_sDbName;		// Connection string (DSN-less ODBC connection string)
	CString	m_sMQServer;	// MQ Server hostname
	int		m_iPorta;		// Monitor port
	int		m_iMaxLenMsg;	// Maximum message length
};

#endif // _CBCDB_H_
