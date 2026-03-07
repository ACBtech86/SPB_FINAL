// ThreadMQ.h

// Fase 6: Migração MSXML → pugixml
// #import "msxml.dll" named_guids raw_interfaces_only
#include <pugixml.hpp>

// Migração CryptLib → OpenSSL (27/02/2026)
#include "OpenSSLWrapper.h"
#include <openssl/evp.h>
#include <openssl/x509.h>
#include <openssl/bio.h>

#ifndef _THREADMQ_H_
#define _THREADMQ_H_

// Modernização C++20: Includes padrão
#include <thread>
#include <mutex>
#include <memory>
#include <atomic>
#include <string>

// Fase 6: Macros MSXML removidas (não são mais necessárias com pugixml)
// #define CHECKHR(x) {m_hr = x; if (FAILED(m_hr)) goto CleanUp;}
// #define SAFERELEASE(p) {if (p) {(p)->Release(); p = NULL;}}

// Modernização C++20: Macros → constexpr
namespace ThreadEvent {
    constexpr int TIMER = 0;
    constexpr int STOP = 1;
    constexpr int POST = 2;
}

constexpr int QTD_THREAD_EVENTS = 3;

// Manter compatibilidade
#define THREAD_EVENT_TIMER		ThreadEvent::TIMER
#define THREAD_EVENT_STOP		ThreadEvent::STOP
#define THREAD_EVENT_POST		ThreadEvent::POST

struct _BITFIELDS
{
    unsigned short a : 4;
    unsigned short b : 4;
};

class CMainSrv;

class CThreadMQ : public CObject
{
public:
	CThreadMQ();
	CThreadMQ(LPCTSTR lpszName, bool AutomaticThread, int HandleMQ, CMainSrv *MainSrv);
	~CThreadMQ();
	BOOL Lock();
	BOOL Unlock();
	static		DWORD WINAPI TaskThread(LPVOID MainSrv);
virtual	void	RunThread(LPVOID MainSrv);
virtual	void	RunInit();
virtual	void	RunWait();
virtual	void	RunWaitPost();
virtual	void	RunTerm();
virtual	void	ProcessaQueue();
virtual	void	DumpHeader(MQMD* InQmd);
virtual bool	AnsiToUnicode(int &lenmsg, LPBYTE msg);
virtual bool	UnicodeToAnsi(int &lenmsg, LPBYTE msg);
virtual bool    UnicodeToAnsi(BSTR psz,LPSTR &pstr);
 
virtual	int		ReadPublicKey();
virtual	int		ReadPrivatKey();
     
virtual	int		funcAssinar(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg);
virtual	int		funcLog(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg);
virtual	int		funcCript(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg);
virtual	int		funcVerifyAss(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg);
virtual	int		funcStrLog(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg);
virtual	int		funcDeCript(LPSECHDR lpSecHeader, int &lentmp, LPBYTE msg);

// Fase 6: Funções migradas de MSXML para pugixml
virtual bool ReportError(const pugi::xml_parse_result& result);
virtual bool CheckLoad(pugi::xml_document& doc);
virtual bool WalkTree(pugi::xml_node node, int level);
virtual bool LoadDocumentSync(pugi::xml_document& doc, const char* pData, size_t ulLen);
virtual bool SaveDocument(pugi::xml_document& doc, const char* pFileName);
virtual bool SetTag(pugi::xml_document& doc, const char* pwText, std::string& pwValue);
virtual bool FindTag(pugi::xml_document& doc, const char* pwParent, const char* pwText, std::string& pwValue);

public:
	void		AtualizaStatus();

public:
	CString			m_ServiceName;
	// Modernização C++20: Threading moderno
	std::unique_ptr<std::thread>	m_thread;
	std::thread::id	m_threadId;
	DWORD			m_dwThreadId;  // Manter para compatibilidade com logs
	int				m_HandleMQ;
	bool			m_AutomaticThread;
	// Modernização C++20: std::atomic para flags thread-safe
	std::atomic<bool>	m_ServicoIsRunning;
	std::atomic<bool>	m_ThreadIsRunning;
	HANDLE			m_hThreadHandle;  // Manter para compatibilidade temporária
	char			m_szTaskName[41];
	char			m_szQueueName[49];
	LPTSTR			m_lpTaskName;
	CMainSrv		*pMainSrv;
	// TODO Fase 4: Substituir eventos Win32 por std::condition_variable
	HANDLE			m_hEvent[QTD_THREAD_EVENTS];
    LARGE_INTEGER	pDueTime;
    LONG			lPeriod;
	// Modernização C++20: HANDLE → std::mutex
	std::mutex		m_mutex;
    // Fase 6: Migrado de MSXML para pugixml
    pugi::xml_document  m_xmlDoc;
    pugi::xml_node      m_xmlNode;
    // Fase 6: HRESULT removido (pugixml usa bool)

	// Migração CryptLib → OpenSSL (27/02/2026)
	EVP_PKEY*		m_publicKey;			// Chave pública (substituiu m_cryptPublicContext)
	EVP_PKEY*		m_privateKey;			// Chave privada (substituiu m_cryptPrivateContext)
	X509*			m_certificate;			// Certificado X.509 (substituiu m_cryptContext)
	BIO*			m_certBio;				// BIO para arquivo de certificado
	BIO*			m_keyBio;				// BIO para arquivo de chave

	BYTE			m_cryptSerialNumberPrv[32];
	BYTE			m_cryptSerialNumberPub[32];
};


#endif // _THREADMQ_H_
