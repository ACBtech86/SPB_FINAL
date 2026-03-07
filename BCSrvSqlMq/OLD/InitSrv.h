// InitSrv.h

#ifndef _INITSRV_H_
#define _INITSRV_H_

#include "ntservice.h"

typedef BOOL (CALLBACK* LPOPENLOG) (LPTSTR, LPTSTR,LPTSTR);
typedef BOOL (CALLBACK* LPWRITELOG) (LPTSTR, UINT, BOOL, LPVOID,LPVOID,LPVOID,LPVOID,LPVOID);
typedef BOOL (CALLBACK* LPWRITEREG) (LPTSTR, BOOL, UINT, LPVOID);
typedef BOOL (CALLBACK* LPCLOSELOG) ();
typedef BOOL (CALLBACK* LPTRACE) (UINT);

const char SES_DIR[]				= "Diretorios";
const char KEY_DIRTRACES[]			= "DirTraces";
const char KEY_DIRAUDFILE[]			= "DirAudFile";
const char SES_DB[]					= "DataBase";
const char KEY_DBALIASNAME[]		= "DBAliasName";
const char KEY_DBSERVER[]			= "DBServer";
const char KEY_DBMAME[]				= "DBName";
const char KEY_DBPORT[]				= "DBPort";
const char KEY_DBUSERNAME[]			= "DBUserName";
const char KEY_DBPASSWORD[]			= "DBPassword";
const char SES_MQSERIES[]			= "MQSeries";
const char KEY_MQSERVER[]			= "MQServer";
const char KEY_MQQUEUEMGR[]			= "QueueManager";
const char KEY_MQQLBACENCIDADEREQ[]	= "QLBacenCidadeReq";
const char KEY_MQQLBACENCIDADERSP[] = "QLBacenCidadeRsp";
const char KEY_MQQLBACENCIDADEREP[] = "QLBacenCidadeRep";
const char KEY_MQQLBACENCIDADESUP[] = "QLBacenCidadeSup";
const char KEY_MQQRCIDADEBACENREQ[] = "QRCidadeBacenReq";
const char KEY_MQQRCIDADEBACENRSP[] = "QRCidadeBacenRsp";
const char KEY_MQQRCIDADEBACENREP[] = "QRCidadeBacenRep";
const char KEY_MQQRCIDADEBACENSUP[] = "QRCidadeBacenSup";
const char KEY_MQQLIFCIDADEREQ[]	= "QLIFCidadeReq";
const char KEY_MQQLIFCIDADERSP[]	= "QLIFCidadeRsp";
const char KEY_MQQLIFCIDADEREP[]	= "QLIFCidadeRep";
const char KEY_MQQLIFCIDADESUP[]	= "QLIFCidadeSup";
const char KEY_MQQRCIDADEIFREQ[]	= "QRCidadeIFReq";
const char KEY_MQQRCIDADEIFRSP[]	= "QRCidadeIFRsp";
const char KEY_MQQRCIDADEIFREP[]	= "QRCidadeIFRep";
const char KEY_MQQRCIDADEIFSUP[]	= "QRCidadeIFSup";
const char KEY_MQQUEUETIMEOUT[]		= "QueueTimeout";

const char KEY_DBTBCONTROLE[]		= "DbTbControle";
const char KEY_DBTBSTRLOG[]			= "DbTbStrLog";
const char KEY_DBTBBACENCIDADEAPP[] = "DbTbBacenCidadeApp";
const char KEY_DBTBCIDADEBACENAPP[] = "DbTbCidadeBacenApp";

const char SES_SRV[]				= "Servico";
const char KEY_MONITORPORT[]		= "MonitorPort";
const char KEY_SRVTRACE[]			= "Trace";
const char KEY_SRVTIMEOUT[]			= "SrvTimeout";
const char KEY_MAXLENMSG[]			= "MaxLenMsg";

const char SES_EMAIL[]				= "E-Mail";
const char KEY_SERVEREMAIL[]		= "ServerEmail";
const char KEY_SENDEREMAIL[]		= "SenderEmail";
const char KEY_SENDERNAME[]			= "SenderName";
const char KEY_DESTEMAIL[]			= "DestEmail";
const char KEY_DESTNAME[]			= "DestName";
const char KEY_CC1EMAIL[]			= "CC1Email";
const char KEY_CC1NAME[]			= "CC1Name";
const char KEY_CC2EMAIL[]			= "CC2Email";
const char KEY_CC2NAME[]			= "CC2Name";
const char KEY_CC3EMAIL[]			= "CC3Email";
const char KEY_CC3NAME[]			= "CC3Name";
const char KEY_CC4EMAIL[]			= "CC4Email";
const char KEY_CC4NAME[]			= "CC4Name";
const char KEY_CC5EMAIL[]			= "CC5Email";
const char KEY_CC5NAME[]			= "CC5Name";

const char SES_SECURITY[]			= "Security";
const char KEY_UNICODEENA[]			= "UnicodeEnable";
const char KEY_SECURITYENA[]		= "SecurityEnable";
const char KEY_SECURITYDB[]			= "SecurityDB";
const char KEY_CERTIFICATEFILE[]	= "CertificateFile";
const char KEY_PRIVATEKEY[]			= "PrivateKeyFile";
const char KEY_PUB_KEYLABEL[]		= "PublicKeyLabel";
const char KEY_PRV_KEYLABEL[]		= "PrivateKeyLabel";
const char KEY_PRV_PASSWORD[]		= "KeyPassword";


typedef struct S_MAIL
{
	LPTSTR pServerMail;				// pointer do endere�o do MAIL SERVER (SMTP)
	LPTSTR pSerderMail;				// pointer do email origen 
	LPTSTR pSerderName;				// pointer do Nome do email origem
	LPTSTR pDestMail;				// pointer do email destino 
	LPTSTR pDestName;				// pointer do Nome do email destino
	LPTSTR pCC1Mail;				// pointer do email copia 1
	LPTSTR pCC1Name;				// pointer do Nome do email copia 1
	LPTSTR pCC2Mail;				// pointer do email copia 2
	LPTSTR pCC2Name;				// pointer do Nome do email copia 2
	LPTSTR pCC3Mail;				// pointer do email copia 3
	LPTSTR pCC3Name;				// pointer do Nome do email copia 3
	LPTSTR pCC4Mail;				// pointer do email copia 4
	LPTSTR pCC4Name;				// pointer do Nome do email copia 4
	LPTSTR pCC5Mail;				// pointer do email copia 5
	LPTSTR pCC5Name;				// pointer do Nome do email copia 5
	LPTSTR pSubject;				// pointer do subject (Max 256 bytes).
	LPTSTR pTexto;					// pointer do texto do email.
} SMAIL;

typedef	struct CELL 
{
   	unsigned byte1 : 4;  //           0000????
   	unsigned byte2 : 4;  //           ????0000
   	unsigned byte3 : 4;  // 0000????
   	unsigned byte4 : 4;  // ????0000
} cell;

const unsigned char hex2char[] = 
{
	0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37,	0x38, 0x39, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46
};


class CMainSrv; 

class CInitSrv : public CNTService
{
public:
	CInitSrv(const char* szServiceName,const char* szDependencies);
	virtual BOOL OnInit();
    virtual void Run();
    virtual void OnStop();
    virtual void OnShutdown();
    virtual void OnPause();
    virtual void OnContinue();
    virtual BOOL OnUserControl(DWORD dwOpcode);
	long SetKeyRegistryValue(LPCTSTR KeyPath, LPCTSTR KeyName, LPCTSTR KeyValue);
	long GetKeyRegistryValue(LPCTSTR KeyPath, LPCTSTR KeyName, LPCTSTR KeyValue);
	long SetKeyRegistryValueBin(LPCTSTR KeyPath, LPCTSTR KeyName, LPBYTE KeyValue, int KeyValueLen);
	long GetKeyRegistryValueBin(LPCTSTR KeyPath, LPCTSTR KeyName, LPBYTE KeyValue, int KeyValueLen);

    void SaveStatus();
	bool GetKeyAll();
	void SetKeyAll();
	void CriaDir(LPCTSTR lpPathName,LPSECURITY_ATTRIBUTES lpSecurityAttributes);

	// Control parameters
	int m_iStartParam;
	int m_iIncParam;
	
	// Current state
	int m_iState;

	// variaveis arquivo INI
	CString			m_DirTraces;
	CString			m_DirAudFile;
	CString			m_DBAliasName;
	CString         m_DBServer;
	CString			m_DBName;
	CString			m_DBUserName;
	CString			m_DBPassword;
	int				m_DBPort;
	CString			m_SrvTrace;
	int				m_SrvTimeout;
	CString         m_MQServer;
	// Queue Manager
	CString			m_QueueMgr;
	int				m_QueueTimeout;
	// Local Queue Bacen Cidade
	CString			m_MqQlBacenCidadeReq;
	CString			m_MqQlBacenCidadeRsp;
	CString			m_MqQlBacenCidadeSup;
	CString			m_MqQlBacenCidadeRep;
	// Remote Queue Cidade Bacen
	CString			m_MqQrCidadeBacenReq;
	CString			m_MqQrCidadeBacenRsp;
	CString			m_MqQrCidadeBacenSup;
	CString			m_MqQrCidadeBacenRep;
	// Local Queue IF Cidade
	CString			m_MqQlIFCidadeReq;
	CString			m_MqQlIFCidadeRsp;
	CString			m_MqQlIFCidadeSup;
	CString			m_MqQlIFCidadeRep;
	// Remote Queue Cidade IF
	CString			m_MqQrCidadeIFReq;
	CString			m_MqQrCidadeIFRsp;
	CString			m_MqQrCidadeIFSup;
	CString			m_MqQrCidadeIFRep;
	// Tabelas SQL Controle
	CString			m_DbTbControle;
	// Tabelas SQL Bacen Cidade
	CString			m_DbTbStrLog;
	CString			m_DbTbBacenCidadeApp;
	// Tabelas SQL Cidade Bacen 
	CString			m_DbTbCidadeBacenApp;

	int				m_MonitorPort;
	char			m_ARQINI[MAX_PATH];
	int				m_MaxLenMsg;

	// Areas do email 
	SMAIL			m_sMail;				// strutura do E-mail
	CString			m_ServerMail;			// pointer do endere�o do MAIL SERVER (SMTP)
	CString			m_SerderMail;			// pointer do email origen 
	CString			m_SerderName;			// pointer do Nome do email origem
	CString			m_DestMail;				// pointer do email destino 
	CString			m_DestName;				// pointer do Nome do email destino
	CString			m_CC1Mail;				// pointer do email copia 1
	CString			m_CC1Name;				// pointer do Nome do email copia 1
	CString			m_CC2Mail;				// pointer do email copia 2
	CString			m_CC2Name;				// pointer do Nome do email copia 2
	CString			m_CC3Mail;				// pointer do email copia 3
	CString			m_CC3Name;				// pointer do Nome do email copia 3
	CString			m_CC4Mail;				// pointer do email copia 4
	CString			m_CC4Name;				// pointer do Nome do email copia 4
	CString			m_CC5Mail;				// pointer do email copia 5
	CString			m_CC5Name;				// pointer do Nome do email copia 5
	
	// Areas do security
	CString			m_UnicodeEnable;		// unicode enable (S/N)
	CString			m_SecurityEnable;		// security enable (S/N)
	CString			m_SecurityDB;			// Alias odbc
	CString			m_CertificateFile;		// certificate file (PEM format)
	CString			m_PrivateKeyFile;		// private key file
	CString			m_PublicKeyLabel;		// public key label
	CString			m_PrivateKeyLabel;		// private key label
	CString			m_KeyPassword;			// private key password

	// Servico SubTask
	CMainSrv *pMainSrv;
	char			m_ComputerName[MAX_COMPUTERNAME_LENGTH + 1];	

	// Servico de msg e log
	HINSTANCE		m_hDllMsg;
	LPOPENLOG		m_OpenLog;
	LPWRITELOG		m_WriteLog;
	LPWRITEREG		m_WriteReg;
	LPCLOSELOG		m_CloseLog;
	LPTRACE			m_Trace;
};

#endif // _INITSRV_H_
