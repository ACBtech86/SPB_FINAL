// MsgSgr.h
 
#ifndef _MSGSGR_H_
#define _MSGSGR_H_

#define MAXMSGLENGTH		8000
#define MINMSGLENGTH		sizeof(_COMHDR)

/*---------------------------------------------------------------------------------------------
	constantes                
---------------------------------------------------------------------------------------------*/

#define FILE_CLOSE			0x00		// arquivo fechado
#define FILE_OPEN			0x01		// arquivo aberto

/*---------------------------------------------------------------------------------------------
	define return code                
---------------------------------------------------------------------------------------------*/

#define Resposta_OK			0		//`Resposta OK

/*---------------------------------------------------------------------------------------------
	define da Handle do arquivo               
---------------------------------------------------------------------------------------------*/

#define TASKS_MONITOR		0x00		// Task Monitor
#define TASKS_BACENREQ		0x01		// Task da BACEN REQ.
#define TASKS_BACENRSP		0x02		// Task da BACEN RSP.
#define TASKS_BACENREP		0x03		// Task da BACEN REP.
#define TASKS_BACENSUP		0x04		// Task da BACEN SUP.
#define TASKS_IFREQ			0x05		// Task da BACEN REQ.
#define TASKS_IFRSP			0x06		// Task da BACEN RSP.
#define TASKS_IFREP			0x07		// Task da BACEN REP.
#define TASKS_IFSUP			0x08		// Task da BACEN SUP.

#define TASKS_COUNT			9			// Tasks + Monitor

/*---------------------------------------------------------------------------------------------
	define da Funcoes do STR               
---------------------------------------------------------------------------------------------*/

#define FUNC_POST			0x01		// funcão POST
#define FUNC_NOP			0xFF		// funcão NOP

/*---------------------------------------------------------------------------------------------
	define das estruturas de mensagem:
---------------------------------------------------------------------------------------------*/

#pragma pack( push, enter_include1 )
#pragma pack(1)

/*---------------------------------------------------------------------------------------------
	Header da comunicação TCPIP               
---------------------------------------------------------------------------------------------*/

typedef struct _COMHDR				// Header da comunicação TCPIP
{
	unsigned short	usMsgLength;	// Tamanho da mensagem
	BYTE			ucIdHeader[4];	// Id do Header
	BYTE			ucFuncSgr;		// Funcão 
	unsigned short	usRc;			// Return Code 
	unsigned short	usDatLength;	// Tamanho do Dados  
} COMHDR, FAR * LPCOMHDR;


/*---------------------------------------------------------------------------------------------
	Header de segurança              
---------------------------------------------------------------------------------------------*/

typedef struct _SECHDR				       // Header de Segurança SPB
{
	BYTE			TamSecHeader[2];	   // tamanho do header de segurança = 332 bytes
	BYTE			Versao;				   // Versão do protocolo de segurança
										   // 00h - Em Claro
										   // 01h - Primeira Versão
	BYTE			CodErro;			   // Código de erro
	BYTE			Reservado[2];		   // reservado para uso futuro - 0000h
	BYTE			AlgAssymKey;		   // algoritimo da chave assimétrica destino
										   // 01h - RSA com 1024 bits
	BYTE			AlgSymKey;			   // algoritimo da chave simétrica
										   // 01h - Triple-DES com 168 bits
	BYTE			AlgAssymKeyLocal;	   // algoritimo da chave assimétrica local usado na assinatura
										   // 01h - RSA com 1024 bits
	BYTE			AlgHash;			   // algoritimo de Hash
										   // 01h - MD5
										   // 02h - SHA-1
	BYTE			CADest;				   // CA do certificado destino
										   // 01h - Certsign
										   // 02h - Serpro
	BYTE			NumSerieCertDest[32];  // Numero de série do certificado Destino
										   // Identificador único do certificado na CA
	BYTE			CALocal;			   // CA do certificado Local
										   // 01h - Certsign
										   // 02h - Serpro
	BYTE			NumSerieCertLocal[32]; // Numero de série do certificado Local 
										   // Identificador único do certificado na CA
	BYTE			IniSymKeyCifr;		   // Valor fixo x'00'
	BYTE			SymKeyCifr[127];	   // Chave simétrica cifrada
										   // Inicia com 3DES, o resto com "FF"
	BYTE			IniHashCifrSign;	   // Valor fixo x'00'
	BYTE			HashCifrSign[127];	   // Hash Cifrado Assinatura digital
										   // Inicia com Hash, o resto com "FF"
} SECHDR, FAR * LPSECHDR;


/*---------------------------------------------------------------------------------------------
	Strutura do AuditFile               
---------------------------------------------------------------------------------------------*/

typedef struct _ST_AUDITFILE			
{
	unsigned short  AUD_TAMREG;			// tamanho do registro do AuditFile	
	BYTE			AUD_AAAAMMDD[8];
	BYTE			AUD_HHMMDDSS[8];
	BYTE			AUD_MQ_HEADER[512];
	BYTE    		AUD_SEC_HEADER[sizeof(SECHDR)];
    BYTE			AUD_SPBDOC[32767];
	unsigned short  AUD_TAMREG_PREV;	// tamanho do registro do AuditFile
} STAUDITFILE;

/*---------------------------------------------------------------------------------------------
	Status Task               
---------------------------------------------------------------------------------------------*/

typedef struct _ST_TASKSTATUS			
{
	int				bTaskNum;					// Numero da Task (HANDLEDB)	
	BYTE			bTaskName[10];				// Nome da Task
	BYTE			iTaskAutomatic;				// Task is Auto/Manual
	BYTE			iTaskIsRunning;				// Task is Running
} STTASKSTATUS;


/*---------------------------------------------------------------------------------------------
	strutura principal de mensagem               
---------------------------------------------------------------------------------------------*/

//#pragma warning( disable : 4200 )	// Disable warning messages C4200
typedef struct _MI_MSG
{
	COMHDR	hdr;
	BYTE    mdata[8000];
} MIMSG, FAR * LPMIMSG;
//#pragma warning( default : 4200 )	// default warning messages C4200

#pragma pack( pop, enter_include1 )

#endif 
