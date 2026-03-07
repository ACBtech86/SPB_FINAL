// INITSRV.cpp

#include <afx.h>
#include <afxmt.h>
#include <afxdb.h>
#include "MsgSgr.h"
#include "NTServApp.h"
#include "winsock2.h"
// Migração CryptLib → OpenSSL (27/02/2026)
#include "OpenSSLWrapper.h"
#include "InitSrv.h"
#include "MainSrv.h"

CInitSrv::CInitSrv(const char* szServiceName,const char* szDependencies)
:CNTService(szServiceName,szDependencies)
{
	m_iStartParam	= 0;
	m_iIncParam		= 1;
	m_iState		= m_iStartParam;

	DWORD tambuf, i;

	tambuf = GetModuleFileName(NULL,m_ARQINI,MAX_PATH);
	
	for (i = tambuf; i != 0; i--)
	{
		if (m_ARQINI[i] == '\\')
		{
			m_ARQINI[i] = 0;
			break;
		}
	}

	strcat(m_ARQINI, "\\BCSrvSqlMq.ini");
}

BOOL CInitSrv::OnInit()
{
    HKEY hkey;
	char szKey[512];
	strcpy(szKey, "SYSTEM\\CurrentControlSet\\Services\\");
	strcat(szKey, m_szServiceName);
	strcat(szKey, "\\Parameters");

    if (RegOpenKeyEx(HKEY_LOCAL_MACHINE,
                     szKey,
                     0,
                     KEY_QUERY_VALUE,
                     &hkey) == ERROR_SUCCESS)
	{
        // Yes we are installed
        DWORD dwType = 0;
        DWORD dwSize = sizeof(m_iStartParam);
        RegQueryValueEx(hkey,
                        "Start",
                        NULL,
                        &dwType,
                        (BYTE*)&m_iStartParam,
                        &dwSize);
        dwSize = sizeof(m_iIncParam);
        RegQueryValueEx(hkey,
                        "Inc",
                        NULL,
                        &dwType,
                        (BYTE*)&m_iIncParam,
                        &dwSize);
        RegCloseKey(hkey);
    }

	// Set the initial state
	m_iState = m_iStartParam;

	pMainSrv = NULL;

	return TRUE;
}

void CInitSrv::Run()
{
	// Carrega Dll de mensagens e log
	m_hDllMsg = LoadLibrary("BCMsgSqlMq");
	if (m_hDllMsg != NULL)
	{
		m_OpenLog = (LPOPENLOG) GetProcAddress(m_hDllMsg,"OpenLog");
		if (!m_OpenLog)
		{
			FreeLibrary(m_hDllMsg);
			m_hDllMsg = NULL;
			MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"Erro na Carga da fun��o OpenLog da BCMsgSqlMq.Dll.");
			return;
		}
		m_WriteLog = (LPWRITELOG) GetProcAddress(m_hDllMsg,"WriteLog");
		if (!m_WriteLog)
		{
			FreeLibrary(m_hDllMsg);
			m_hDllMsg = NULL;
			MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"Erro na Carga da fun��o WriteLog da BCMsgSqlMq.Dll.");
			return;
		}
		m_WriteReg = (LPWRITEREG) GetProcAddress(m_hDllMsg,"WriteReg");
		if (!m_WriteReg)
		{
			FreeLibrary(m_hDllMsg);
			m_hDllMsg = NULL;
			MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"Erro na Carga da fun��o WriteReg da BCMsgSqlMq.Dll.");
			return;
		}
		m_CloseLog = (LPCLOSELOG) GetProcAddress(m_hDllMsg,"CloseLog");
		if (!m_CloseLog)
		{
			FreeLibrary(m_hDllMsg);
			m_hDllMsg = NULL;
			MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"Erro na Carga da fun��o CloseLog da BCMsgSqlMq.Dll.");
			return;
		}
		m_Trace = (LPTRACE) GetProcAddress(m_hDllMsg,"Trace");
		if (!m_Trace)
		{
			FreeLibrary(m_hDllMsg);
			m_hDllMsg = NULL;
			MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"Erro na Carga da fun��o Trace da BCMsgSqlMq.Dll.");
			return;
		}
	}
	else
	{
			return;
	}

	if (GetKeyAll())
	{
		SetKeyAll();
	}

	CriaDir( m_DirAudFile, NULL);
	CriaDir( m_DirTraces, NULL);
	CString pathlog(' ',255);
	char  workpath[255];

	pathlog = m_DirTraces;
	
	strcpy((char*) &workpath,pathlog);
	char filepgm[] = "TRACE_SPB_";				// nome do servi�o

	memset(&m_sMail,0x00, sizeof(SMAIL));
	if (!m_ServerMail.IsEmpty())
	{
		m_sMail.pServerMail = const_cast<LPTSTR>((LPCSTR) m_ServerMail);
	}
	if (!m_SerderMail.IsEmpty())
	{
		m_sMail.pSerderMail = const_cast<LPTSTR>((LPCSTR) m_SerderMail);
		m_sMail.pSerderName = const_cast<LPTSTR>((LPCSTR) m_SerderName);
	}
	if (!m_DestMail.IsEmpty())
	{
		m_sMail.pDestMail   = const_cast<LPTSTR>((LPCSTR) m_DestMail);
		m_sMail.pDestName   = const_cast<LPTSTR>((LPCSTR) m_DestName);
	}

	if (!m_CC1Mail.IsEmpty())
	{
		m_sMail.pCC1Mail   = const_cast<LPTSTR>((LPCSTR) m_CC1Mail);
		m_sMail.pCC1Name   = const_cast<LPTSTR>((LPCSTR) m_CC1Name);
	}

	if (!m_CC2Mail.IsEmpty())
	{
		m_sMail.pCC2Mail   = const_cast<LPTSTR>((LPCSTR) m_CC2Mail);
		m_sMail.pCC2Name   = const_cast<LPTSTR>((LPCSTR) m_CC2Name);
	}
	if (!m_CC3Mail.IsEmpty())
	{
		m_sMail.pCC3Mail   = const_cast<LPTSTR>((LPCSTR) m_CC3Mail);
		m_sMail.pCC3Name   = const_cast<LPTSTR>((LPCSTR) m_CC3Name);
	}
	if (!m_CC4Mail.IsEmpty())
	{
		m_sMail.pCC4Mail   = const_cast<LPTSTR>((LPCSTR) m_CC4Mail);
		m_sMail.pCC4Name   = const_cast<LPTSTR>((LPCSTR) m_CC4Name);
	}
	if (!m_CC5Mail.IsEmpty())
	{
		m_sMail.pCC5Mail   = const_cast<LPTSTR>((LPCSTR) m_CC5Mail);
		m_sMail.pCC5Name   = const_cast<LPTSTR>((LPCSTR) m_CC5Name);
	}

	m_OpenLog((char*) &workpath, (char*) &filepgm,(char*) &m_sMail);

 	WSADATA		WsaData;
	pMainSrv = new CMainSrv();

	if (pMainSrv)
	{

		WORD wVersionRequested;
		wVersionRequested = MAKEWORD( 2, 2 ); 
		int err = WSAStartup(wVersionRequested, &WsaData);
		if ( err != 0 ) 
		{
			MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"Erro no WSAStartup (verifique Winsock Dll).");
			OnStop();
		}
		else
		{
			if (LOBYTE( WsaData.wVersion ) != 2 ||
			    HIBYTE( WsaData.wVersion ) != 2 ) 
			{
				MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"Vers�o do Winsock diferente de 2.0.");
				OnStop();
			}
			else
			{
				if (!pMainSrv->PreparaTasks(this))
					OnStop();
			}
			
			if (m_SecurityEnable.Compare("N") != 0)
			{
				// Inicializar OpenSSL
				if (!OpenSSLCrypto::InitCrypto())
				{
					char taskName[] = "InitSrv";
					int errorCode = 8098;
					m_WriteLog(taskName, errorCode, FALSE, &errorCode, NULL, NULL, NULL, NULL);
				}
			}

			SetStatus(SERVICE_RUNNING);

			pMainSrv->WaitTasks();
			delete pMainSrv;
			pMainSrv = NULL;

			if (m_SecurityEnable.Compare("N") != 0)
			{
				// Limpar recursos OpenSSL
				OpenSSLCrypto::CleanupCrypto();
			}
			
			WSACleanup();
		}
		if (pMainSrv)
		{
			delete pMainSrv;
			pMainSrv = NULL;
		}
	}

	if (m_hDllMsg != NULL)
	{
		m_CloseLog();
		FreeLibrary(m_hDllMsg);
		m_hDllMsg = NULL;
	}


	m_bIsRunning = FALSE;
	MsgToLog(EVENTLOG_INFORMATION_TYPE,EVMSG_MAIN,"Terminando task INITSRV.\r\n");


}

// Process shutdown requests

void CInitSrv::OnShutdown()
{
	OnStop();
}

void CInitSrv::OnStop()
{

	if (pMainSrv)
	{
		SetEvent(pMainSrv->m_hEvent[MAIN_EVENT_STOP]);
	}
}

void CInitSrv::OnPause()
{

	if (pMainSrv)
	{
		SetEvent(pMainSrv->m_hEvent[MAIN_EVENT_PAUSE]);
	}
}

void CInitSrv::OnContinue()
{

	if (pMainSrv)
	{
		SetEvent(pMainSrv->m_hEvent[MAIN_EVENT_CONTINUE]);
	}
}

// Process user control requests
BOOL CInitSrv::OnUserControl(DWORD dwOpcode)
{
    switch (dwOpcode)
	{
		case SERVICE_CONTROL_USER + 0:
			// Save the current status in the registry
			SaveStatus();
			return TRUE;

	    default:
		    break;
    }

    return FALSE; // say not handled
}

// Save the current status in the registry
void CInitSrv::SaveStatus()
{
    HKEY hkey = NULL;
	char szKey[512];
	strcpy(szKey, "SYSTEM\\CurrentControlSet\\Services\\");
	strcat(szKey, m_szServiceName);
	strcat(szKey, "\\Status");
    DWORD dwDisp;
	DWORD dwErr;
	char emptyClass[] = "";
    dwErr = RegCreateKeyEx(	HKEY_LOCAL_MACHINE,
                           	szKey,
                   			0,
                   			emptyClass,
                   			REG_OPTION_NON_VOLATILE,
                   			KEY_WRITE,
                   			NULL,
                   			&hkey,
                   			&dwDisp);
	if (dwErr != ERROR_SUCCESS)
	{
		MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"BCSrvSqlMQ SaveStatus Failed to create Status key");
		return;
	}	

    // Set the registry values
    RegSetValueEx(hkey,
                  "Current",
                  0,
                  REG_DWORD,
                  (BYTE*)&m_iState,
                  sizeof(m_iState));


    // Finished with key
    RegCloseKey(hkey);

}

long CInitSrv::SetKeyRegistryValue(LPCTSTR KeyPath, LPCTSTR KeyName, LPCTSTR KeyValue)
{
	long	lResult;

	lResult = WritePrivateProfileString(KeyPath, KeyName, KeyValue, m_ARQINI);

	return !lResult;
}

long CInitSrv::GetKeyRegistryValue(LPCTSTR KeyPath, LPCTSTR KeyName, LPCTSTR KeyValue)
{
	long	lResult = 0;

	int VLen = 256;
	char *Value = new char[VLen];

	GetPrivateProfileString(KeyPath, KeyName,"NONE", Value, VLen, m_ARQINI);

	if (strncmp(Value,"NONE",4) == 0)
	   	lResult = 1;

 	strcpy((char *)KeyValue,(char *)Value);

	delete Value;
	return lResult;
}

long CInitSrv::SetKeyRegistryValueBin(LPCTSTR KeyPath, LPCTSTR KeyName, LPBYTE KeyValue, int KeyValueLen)
{
	long	lResult;
    int 	i,vlen;

	union BYTE_INT    // Declare union type
	{
		unsigned int    i;
		BYTE			b1[2];
		CELL			b2;
	
	} byte_int;

	LPBYTE Value = new BYTE[KeyValueLen * 2 + 1];

	for (i = 0,vlen = 0; i < KeyValueLen; i++)
	{
		byte_int.i = 0;
    	byte_int.b1[1] = KeyValue[i];
        Value[vlen++] = hex2char[byte_int.b2.byte4];
        Value[vlen++] = hex2char[byte_int.b2.byte3];
 	} 
 	Value[vlen] = 0x00;
	
	lResult = WritePrivateProfileString(KeyPath, KeyName, (char *) Value, m_ARQINI);
	delete Value;

	return lResult;
} 

long CInitSrv::GetKeyRegistryValueBin(LPCTSTR KeyPath, LPCTSTR KeyName, LPBYTE KeyValue, int KeyValueLen)
{
	long	lResult = 0;
    int 	i, count;

	union BYTE_INT    // Declare union type
	{
		BYTE			b1[2];
		CELL			b2;
	
	} byte_int;

	int VLen = 0;
	char *Value = new char[2048];

	VLen = GetPrivateProfileString(KeyPath, KeyName,"NONE", Value, 2048, m_ARQINI);

	if (strncmp(Value,"NONE",4) == 0)
	{
	   	lResult = 1;
		delete Value;
		return lResult;
  	}

	for (i = 0,count = 0; i < VLen;)
	{
		byte_int.b1[0] = Value[i++];
		byte_int.b1[1] = Value[i++];
		if (byte_int.b2.byte4 == 4)
		{
			byte_int.b2.byte3 += 9;
		}
		if (byte_int.b2.byte2 == 4)
		{
			byte_int.b2.byte1 += 9;
		} 		
		byte_int.b2.byte4 = byte_int.b2.byte1;
		if (count <= KeyValueLen)
			KeyValue[count++] = byte_int.b1[1];
	}	
		KeyValueLen = --count;

		delete Value;

	return lResult;
}

bool CInitSrv::GetKeyAll()
{
	bool rt = false;
	char *szValue = new char[256];
	UINT itrace = 0;
	
	DWORD nSize = MAX_COMPUTERNAME_LENGTH + 1;	

	GetComputerName((char *) &m_ComputerName, &nSize);

	if (GetKeyRegistryValue(SES_SRV, KEY_SRVTRACE, szValue) == 0)
	{
		m_SrvTrace = szValue;	
	}
	else
	{
		m_SrvTrace = "N";
		rt = true;
	}

	if (m_SrvTrace == "S")
	{
		itrace = 1;
	}
	if (m_SrvTrace == "D")
	{
		itrace = 2;
	}

	if (m_Trace)
		m_Trace(itrace);

	if (GetKeyRegistryValue(SES_DIR, KEY_DIRTRACES, szValue) == 0)
	{
		m_DirTraces = szValue;	
	}
	else
	{
		m_DirTraces  = "C:\\BCSRVSQLMQ\\Traces";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_DIR, KEY_DIRAUDFILE, szValue) == 0)
	{
		m_DirAudFile = szValue;	
	}
	else
	{
		m_DirAudFile = "C:\\BCSRVSQLMQ\\AuditFiles";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_DIR, KEY_DIRTRACES, szValue) == 0)
	{
		m_DirTraces = szValue;	
	}
	else
	{
		m_DirTraces  = "C:\\BCSRVSQLMQ\\Traces";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_DB, KEY_DBSERVER, szValue) == 0)
	{
		m_DBServer = szValue;	
		if (m_DBServer.IsEmpty())
		{
			m_DBServer = m_ComputerName;
		}
	}
	else
	{
		m_DBServer = m_ComputerName;
		rt = true;
	}


	if (GetKeyRegistryValue(SES_DB, KEY_DBMAME, szValue) == 0)
	{
		m_DBName = szValue;	
	}
	else
	{
		m_DBName = "BCSPB";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_DB, KEY_DBALIASNAME, szValue) == 0)
	{
		m_DBAliasName = szValue;
	}
	else
	{
		m_DBAliasName = "BCSPBSTR";
		rt = true;
	}

	// Database Port
	if (GetKeyRegistryValue(SES_DB, KEY_DBPORT, szValue) == 0)
	{
		m_DBPort = atoi(szValue);
		if (m_DBPort == 0)
			m_DBPort = 5432; // PostgreSQL default port
	}
	else
	{
		m_DBPort = 5432;
		rt = true;
	}

	// Database Username
	if (GetKeyRegistryValue(SES_DB, KEY_DBUSERNAME, szValue) == 0)
	{
		m_DBUserName = szValue;
	}
	else
	{
		m_DBUserName = "postgres";
		rt = true;
	}

	// Database Password
	if (GetKeyRegistryValue(SES_DB, KEY_DBPASSWORD, szValue) == 0)
	{
		m_DBPassword = szValue;
	}
	else
	{
		m_DBPassword = "";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_DB, KEY_DBTBCONTROLE, szValue) == 0)
	{
		m_DbTbControle = szValue;	
	}
	else
	{
		m_DbTbControle = "CONTROLE";
		rt = true;
	}

		if (GetKeyRegistryValue(SES_DB, KEY_DBTBSTRLOG, szValue) == 0)
	{
		m_DbTbStrLog = szValue;	
	}
	else
	{
		m_DbTbStrLog = "BCIDADE_STR_LOG";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_DB, KEY_DBTBBACENCIDADEAPP, szValue) == 0)
	{
		m_DbTbBacenCidadeApp = szValue;	
	}
	else
	{
		m_DbTbBacenCidadeApp = "BACEN_TO_BCIDADE_APP";
		rt = true;
	}


	if (GetKeyRegistryValue(SES_DB, KEY_DBTBCIDADEBACENAPP, szValue) == 0)
	{
		m_DbTbCidadeBacenApp = szValue;
	}
	else
	{
		m_DbTbCidadeBacenApp = "BCIDADE_TO_BACEN_APP";
		rt = true;
	}

	// Build DSN-less ODBC connection string for PostgreSQL
	// This eliminates the need to configure ODBC DSN via ODBC Administrator
	CString sDbPort;
	sDbPort.Format("%d", m_DBPort);
	m_DBName = "DRIVER={PostgreSQL Unicode};";
	m_DBName += "SERVER=" + m_DBServer + ";";
	m_DBName += "PORT=" + sDbPort + ";";
	m_DBName += "DATABASE=" + m_DBAliasName + ";";  // Using DBAliasName as actual DB name
	m_DBName += "UID=" + m_DBUserName + ";";
	m_DBName += "PWD=" + m_DBPassword + ";";
	// Log the connection string (without password for security)
	CString sLogConnStr = m_DBName;
	int nPwdPos = sLogConnStr.Find("PWD=");
	if (nPwdPos >= 0)
	{
		int nPwdEnd = sLogConnStr.Find(";", nPwdPos);
		if (nPwdEnd >= 0)
			sLogConnStr = sLogConnStr.Left(nPwdPos) + "PWD=****" + sLogConnStr.Mid(nPwdEnd);
	}
	m_WriteLog(m_szServiceName, 8003, FALSE, (LPVOID)(LPCTSTR)sLogConnStr, NULL, NULL, NULL, NULL);

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQSERVER, szValue) == 0)
	{
		m_MQServer = szValue;	
		if (m_MQServer.IsEmpty())
		{
			m_MQServer = m_ComputerName;
		}
	}
	else
	{
		m_MQServer = m_ComputerName;
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQUEUEMGR, szValue) == 0)
	{
		m_QueueMgr = szValue;	
	}
	else
	{
		m_QueueMgr = "QM.61377677.01";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQLBACENCIDADEREQ, szValue) == 0)
	{
		m_MqQlBacenCidadeReq = szValue;	
	}
	else
	{
		m_MqQlBacenCidadeReq = "QL.REQ.00038166.61377677.01";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQLBACENCIDADERSP, szValue) == 0)
	{
		m_MqQlBacenCidadeRsp = szValue;	
	}
	else
	{
		m_MqQlBacenCidadeRsp = "QL.RSP.00038166.61377677.01";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQLBACENCIDADEREP, szValue) == 0)
	{
		m_MqQlBacenCidadeRep = szValue;	
	}
	else
	{
		m_MqQlBacenCidadeRep = "QL.REP.00038166.61377677.01";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQLBACENCIDADESUP, szValue) == 0)
	{
		m_MqQlBacenCidadeSup = szValue;	
	}
	else
	{
		m_MqQlBacenCidadeSup = "QL.SUP.00038166.61377677.01";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEBACENREQ, szValue) == 0)
	{
		m_MqQrCidadeBacenReq = szValue;	
	}
	else
	{
		m_MqQrCidadeBacenReq = "QR.REQ.61377677.00038166.01";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEBACENRSP, szValue) == 0)
	{
		m_MqQrCidadeBacenRsp = szValue;	
	}
	else
	{
		m_MqQrCidadeBacenRsp = "QR.RSP.61377677.00038166.01";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEBACENREP, szValue) == 0)
	{
		m_MqQrCidadeBacenRep = szValue;	
	}
	else
	{
		m_MqQrCidadeBacenRep = "QR.REP.61377677.00038166.01";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEBACENSUP, szValue) == 0)
	{
		m_MqQrCidadeBacenSup = szValue;
	}
	else
	{
		m_MqQrCidadeBacenSup = "QR.SUP.61377677.00038166.01";
		rt = true;
	}

	// IF Local Queues
	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQLIFCIDADEREQ, szValue) == 0)
	{
		m_MqQlIFCidadeReq = szValue;
	}
	else
	{
		m_MqQlIFCidadeReq = "QL.61377677.01.ENTRADA.IF";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQLIFCIDADERSP, szValue) == 0)
	{
		m_MqQlIFCidadeRsp = szValue;
	}
	else
	{
		m_MqQlIFCidadeRsp = "QL.61377677.01.SAIDA.IF";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQLIFCIDADEREP, szValue) == 0)
	{
		m_MqQlIFCidadeRep = szValue;
	}
	else
	{
		m_MqQlIFCidadeRep = "QL.61377677.01.REPORT.IF";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQLIFCIDADESUP, szValue) == 0)
	{
		m_MqQlIFCidadeSup = szValue;
	}
	else
	{
		m_MqQlIFCidadeSup = "QL.61377677.01.SUPORTE.IF";
		rt = true;
	}

	// IF Remote Queues
	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEIFREQ, szValue) == 0)
	{
		m_MqQrCidadeIFReq = szValue;
	}
	else
	{
		m_MqQrCidadeIFReq = "QR.61377677.01.ENTRADA.IF";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEIFRSP, szValue) == 0)
	{
		m_MqQrCidadeIFRsp = szValue;
	}
	else
	{
		m_MqQrCidadeIFRsp = "QR.61377677.01.SAIDA.IF";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEIFREP, szValue) == 0)
	{
		m_MqQrCidadeIFRep = szValue;
	}
	else
	{
		m_MqQrCidadeIFRep = "QR.61377677.01.REPORT.IF";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEIFSUP, szValue) == 0)
	{
		m_MqQrCidadeIFSup = szValue;
	}
	else
	{
		m_MqQrCidadeIFSup = "QR.61377677.01.SUPORTE.IF";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_MQSERIES, KEY_MQQUEUETIMEOUT, szValue) == 0)
	{
		m_QueueTimeout = atoi(szValue);	
	}
	else
	{
		m_QueueTimeout = 30;
		rt = true;
	}

	if (GetKeyRegistryValue(SES_SRV, KEY_MONITORPORT, szValue) == 0)
	{
		m_MonitorPort = atoi(szValue);
	}
	else
	{
		m_MonitorPort = 14499;
		rt = true;
	}

	if (GetKeyRegistryValue(SES_SRV, KEY_SRVTIMEOUT, szValue) == 0)
	{
		m_SrvTimeout = atoi(szValue);	
	}
	else
	{
		m_SrvTimeout = 120;
		rt = true;
	}


	if (GetKeyRegistryValue(SES_SRV, KEY_MAXLENMSG, szValue) == 0)
	{
		m_MaxLenMsg = atoi(szValue);	
	}
	else
	{
		m_MaxLenMsg = 1000;
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_SERVEREMAIL, szValue) == 0)
	{
		m_ServerMail = szValue;	
	}
	else
	{
		m_ServerMail.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_SENDEREMAIL, szValue) == 0)
	{
		m_SerderMail = szValue;	
	}
	else
	{
		m_SerderMail.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_SENDERNAME, szValue) == 0)
	{
		m_SerderName = szValue;	
	}
	else
	{
		m_SerderName.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_DESTEMAIL, szValue) == 0)
	{
		m_DestMail = szValue;	
	}
	else
	{
		m_DestMail.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_DESTNAME, szValue) == 0)
	{
		m_DestName = szValue;	
	}
	else
	{
		m_DestName.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_CC1EMAIL, szValue) == 0)
	{
		m_CC1Mail = szValue;	
	}
	else
	{
		m_CC1Mail.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_CC1NAME, szValue) == 0)
	{
		m_CC1Name = szValue;	
	}
	else
	{
		m_CC1Name.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_CC2EMAIL, szValue) == 0)
	{
		m_CC2Mail = szValue;	
	}
	else
	{
		m_CC2Mail.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_CC2NAME, szValue) == 0)
	{
		m_CC2Name = szValue;	
	}
	else
	{
		m_CC2Name.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_CC3EMAIL, szValue) == 0)
	{
		m_CC3Mail = szValue;	
	}
	else
	{
		m_CC3Mail.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_CC3NAME, szValue) == 0)
	{
		m_CC3Name = szValue;	
	}
	else
	{
		m_CC3Name.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_CC4EMAIL, szValue) == 0)
	{
		m_CC4Mail = szValue;	
	}
	else
	{
		m_CC4Mail.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_CC4NAME, szValue) == 0)
	{
		m_CC4Name = szValue;	
	}
	else
	{
		m_CC4Name.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_CC5EMAIL, szValue) == 0)
	{
		m_CC5Mail = szValue;	
	}
	else
	{
		m_CC5Mail.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_EMAIL, KEY_CC5NAME, szValue) == 0)
	{
		m_CC5Name = szValue;	
	}
	else
	{
		m_CC5Name.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_SECURITY, KEY_UNICODEENA, szValue) == 0)
	{
		m_UnicodeEnable = szValue;	
	}
	else
	{
		m_UnicodeEnable = "S";
		rt = true;
	}

	if (GetKeyRegistryValue(SES_SECURITY, KEY_SECURITYENA, szValue) == 0)
	{
		m_SecurityEnable = szValue;	
	}
	else
	{
		m_SecurityEnable = "N";
		rt = true;
	}

	if (m_SecurityEnable.Compare("S") == 0)
	{
		m_UnicodeEnable = "S";
	}

	if (GetKeyRegistryValue(SES_SECURITY, KEY_SECURITYDB, szValue) == 0)
	{
		m_SecurityDB = szValue;
	}
	else
	{
		m_SecurityDB = "Public Keys";
		rt = true;
	}

	// Read certificate file path (OpenSSL migration - 2026-03-01)
	if (GetKeyRegistryValue(SES_SECURITY, KEY_CERTIFICATEFILE, szValue) == 0)
	{
		m_CertificateFile = szValue;
	}
	else
	{
		m_CertificateFile.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_SECURITY, KEY_PRIVATEKEY, szValue) == 0)
	{
		m_PrivateKeyFile = szValue;
	}
	else
	{
		m_PrivateKeyFile.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_SECURITY, KEY_PUB_KEYLABEL, szValue) == 0)
	{
		m_PublicKeyLabel = szValue;	
	}
	else
	{
		m_PublicKeyLabel.Empty();
		rt = true;
	}

	if (GetKeyRegistryValue(SES_SECURITY, KEY_PRV_KEYLABEL, szValue) == 0)
	{
		m_PrivateKeyLabel = szValue;	
	}
	else
	{
		m_PrivateKeyLabel.Empty();
		rt = true;
	}
	if (GetKeyRegistryValue(SES_SECURITY, KEY_PRV_PASSWORD, szValue) == 0)
	{
		m_KeyPassword = szValue;	
	}
	else
	{
		m_KeyPassword.Empty();
		rt = true;
	}

	delete szValue;
	return rt;
}

void CInitSrv::SetKeyAll()
{
	char buffer[256];

	SetKeyRegistryValue(SES_SRV, KEY_SRVTRACE, m_SrvTrace);
	UINT itrace = 0;
	if (m_SrvTrace == "S")
	{
		itrace = 1;
	}
	if (m_SrvTrace == "D")
	{
		itrace = 2;
	}

	if (m_Trace)
		m_Trace(itrace);
	

	SetKeyRegistryValue(SES_DIR, KEY_DIRTRACES, m_DirTraces);
	SetKeyRegistryValue(SES_DIR, KEY_DIRAUDFILE, m_DirAudFile);

	SetKeyRegistryValue(SES_DB, KEY_DBALIASNAME, m_DBAliasName);
	SetKeyRegistryValue(SES_DB, KEY_DBSERVER, m_DBServer);
	SetKeyRegistryValue(SES_DB, KEY_DBMAME, m_DBName);

	SetKeyRegistryValue(SES_DB, KEY_DBTBCONTROLE,       m_DbTbControle);
	SetKeyRegistryValue(SES_DB, KEY_DBTBSTRLOG,         m_DbTbStrLog);
	SetKeyRegistryValue(SES_DB, KEY_DBTBBACENCIDADEAPP, m_DbTbBacenCidadeApp);
	SetKeyRegistryValue(SES_DB, KEY_DBTBCIDADEBACENAPP, m_DbTbCidadeBacenApp);

	SetKeyRegistryValue(SES_MQSERIES, KEY_MQSERVER, m_MQServer);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQUEUEMGR, m_QueueMgr);

	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQLBACENCIDADEREQ, m_MqQlBacenCidadeReq);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQLBACENCIDADERSP, m_MqQlBacenCidadeRsp);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQLBACENCIDADEREP, m_MqQlBacenCidadeRep);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQLBACENCIDADESUP, m_MqQlBacenCidadeSup);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEBACENREQ, m_MqQrCidadeBacenReq);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEBACENRSP, m_MqQrCidadeBacenRsp);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEBACENREP, m_MqQrCidadeBacenRep);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEBACENSUP, m_MqQrCidadeBacenSup);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQLIFCIDADEREQ, m_MqQlIFCidadeReq);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQLIFCIDADERSP, m_MqQlIFCidadeRsp);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQLIFCIDADEREP, m_MqQlIFCidadeRep);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQLIFCIDADESUP, m_MqQlIFCidadeSup);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEIFREQ, m_MqQrCidadeIFReq);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEIFRSP, m_MqQrCidadeIFRsp);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEIFREP, m_MqQrCidadeIFRep);
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQRCIDADEIFSUP, m_MqQrCidadeIFSup);

	_itoa( m_QueueTimeout, buffer, 10 );
	SetKeyRegistryValue(SES_MQSERIES, KEY_MQQUEUETIMEOUT, (LPCTSTR) &buffer);

	_itoa( m_MonitorPort, buffer, 10 );
	SetKeyRegistryValue(SES_SRV, KEY_MONITORPORT, (LPCTSTR) &buffer);

	_itoa( m_SrvTimeout, buffer, 10 );
	SetKeyRegistryValue(SES_SRV, KEY_SRVTIMEOUT, (LPCTSTR) &buffer);

	_itoa( m_MaxLenMsg, buffer, 10 );
	SetKeyRegistryValue(SES_SRV, KEY_MAXLENMSG, (LPCTSTR) &buffer);

	SetKeyRegistryValue(SES_EMAIL, KEY_SERVEREMAIL, m_ServerMail);
	SetKeyRegistryValue(SES_EMAIL, KEY_SENDEREMAIL, m_SerderMail);
	SetKeyRegistryValue(SES_EMAIL, KEY_SENDERNAME, m_SerderName);
	SetKeyRegistryValue(SES_EMAIL, KEY_DESTEMAIL, m_DestMail);
	SetKeyRegistryValue(SES_EMAIL, KEY_DESTNAME, m_DestName);
	SetKeyRegistryValue(SES_EMAIL, KEY_CC1EMAIL, m_CC1Mail);
	SetKeyRegistryValue(SES_EMAIL, KEY_CC1NAME, m_CC1Name);
	SetKeyRegistryValue(SES_EMAIL, KEY_CC2EMAIL, m_CC2Mail);
	SetKeyRegistryValue(SES_EMAIL, KEY_CC2NAME, m_CC2Name);
	SetKeyRegistryValue(SES_EMAIL, KEY_CC3EMAIL, m_CC3Mail);
	SetKeyRegistryValue(SES_EMAIL, KEY_CC3NAME, m_CC3Name);
	SetKeyRegistryValue(SES_EMAIL, KEY_CC4EMAIL, m_CC4Mail);
	SetKeyRegistryValue(SES_EMAIL, KEY_CC4NAME, m_CC4Name);
	SetKeyRegistryValue(SES_EMAIL, KEY_CC5EMAIL, m_CC5Mail);
	SetKeyRegistryValue(SES_EMAIL, KEY_CC5NAME, m_CC5Name);

	SetKeyRegistryValue(SES_SECURITY, KEY_UNICODEENA, m_UnicodeEnable);
	SetKeyRegistryValue(SES_SECURITY, KEY_SECURITYENA, m_SecurityEnable);
	SetKeyRegistryValue(SES_SECURITY, KEY_SECURITYDB, m_SecurityDB);
	SetKeyRegistryValue(SES_SECURITY, KEY_CERTIFICATEFILE, m_CertificateFile);
	SetKeyRegistryValue(SES_SECURITY, KEY_PRIVATEKEY, m_PrivateKeyFile);
	SetKeyRegistryValue(SES_SECURITY, KEY_PUB_KEYLABEL, m_PublicKeyLabel);
	SetKeyRegistryValue(SES_SECURITY, KEY_PRV_KEYLABEL, m_PrivateKeyLabel);
	SetKeyRegistryValue(SES_SECURITY, KEY_PRV_PASSWORD, m_KeyPassword);

	return;
}

void CInitSrv::CriaDir(LPCTSTR lpPathName,LPSECURITY_ATTRIBUTES lpSecurityAttributes)
{
	CString wrkall,wrk;

	wrk.Empty();
	wrkall = lpPathName;

	while (wrkall.GetLength() > 0)
	{
		int pos = wrkall.Find("\\",0);
		if (pos == -1)
		{
			wrk += wrkall.Mid(0);
			wrkall.Empty();
		}
		else
		{
			wrk += wrkall.Mid(0, pos);
			wrkall = wrkall.Mid(pos + 1);
		}
		if (wrk.GetLength() == 0)
			continue;
		if (wrk.GetAt(wrk.GetLength() - 1) == ':')
		{
			wrk += "\\";
			continue;
		}
		int rt = CreateDirectory( wrk, NULL);
		if (!rt)
		{
			DWORD rc = GetLastError();
			if (rc != ERROR_ALREADY_EXISTS)
			{
//				DWORD rc = GetLastError();
				CString str;
				LPVOID lpMsgBuf;
				FormatMessage(	FORMAT_MESSAGE_ALLOCATE_BUFFER | 
							    FORMAT_MESSAGE_FROM_SYSTEM | 
								FORMAT_MESSAGE_IGNORE_INSERTS, 
								NULL,
								GetLastError(),
								MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
							    (LPTSTR) &lpMsgBuf,    0,    NULL );
				str.Format("Erro Criando Diretorio %s erro %s.",wrk,lpMsgBuf);
				MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,str);
				LocalFree( lpMsgBuf );
			}
		}
		wrk += "\\";

	}
}