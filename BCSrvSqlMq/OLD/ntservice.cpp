// NTService.cpp
//
// Implementation of CNTService

#include <stdio.h>
#include <windows.h>
#include "NTService.h"

// static variables
CNTService* CNTService::m_pThis = NULL;

CNTService::CNTService(const char* szServiceName,const char* szDependencies)
{
    // copy the address of the current object so we can access it from
    // the static member callback functions. 
    // WARNING: This limits the application to only one CNTService object. 
    m_pThis = this;
    
    // Set the default service name and version
    strncpy(m_szServiceName, szServiceName, sizeof(m_szServiceName)-1);
	memset(m_szDependencies, 0x00, sizeof(m_szDependencies));
    strncpy(m_szDependencies, szDependencies, sizeof(m_szDependencies)-1);

    m_iMajorVersion = 1;	//versao
    m_iMinorVersion = 0;	//versao
    m_hEventSource = NULL;

    // set up the initial service status 
    m_hServiceStatus = NULL;
    m_Status.dwServiceType = SERVICE_WIN32_OWN_PROCESS;
    m_Status.dwCurrentState = SERVICE_STOPPED;
    m_Status.dwControlsAccepted = SERVICE_ACCEPT_STOP;
    m_Status.dwWin32ExitCode = 0;
    m_Status.dwServiceSpecificExitCode = 0;
    m_Status.dwCheckPoint = 0;
    m_Status.dwWaitHint = 0;
    m_bIsRunning = FALSE;
    m_bIsDebuging = FALSE;
	m_bIsShutDownNow = FALSE;
}

CNTService::~CNTService()
{
    if (m_hEventSource)
	{
        ::DeregisterEventSource(m_hEventSource);
    }
}

////////////////////////////////////////////////////////////////////////////////////////
// Default command line argument parsing

// Returns TRUE if it found an arg it recognised, FALSE if not
// Note: processing some arguments causes output to stdout to be generated.
BOOL CNTService::ParseStandardArgs(int argc, char* argv[])
{
    // See if we have any command line args we recognise
    if (argc <= 1) return FALSE;

    if (_stricmp(argv[1], "-v") == 0)
	{
        // Spit out version info
        printf("%s Versao %d.%d\n",
               m_szServiceName, m_iMajorVersion, m_iMinorVersion);
        printf("O servico%s esta instalado.\n",
               IsInstalled() ? "" : " nao");
        return TRUE;
    }
	
	if (_stricmp(argv[1], "-i") == 0)
	{
        // Request to install.
        if (IsInstalled())
		{
            printf("%s ja esta instalado.\n", m_szServiceName);
        }
		else
		{
			// Try and install the copy that's running
			if (Install())
			{
				printf("%s instalado.\n", m_szServiceName);
			}
			else 
			{
				printf("%s falhou para instalar. Erro %d\n", m_szServiceName, GetLastError());
			}
		}
		return TRUE; // say we processed the argument
    }
	
	if (_stricmp(argv[1], "-u") == 0)
	{
        // Request to uninstall.
        if (!IsInstalled())
		{
            printf("%s nao esta instalado.\n", m_szServiceName);
        }
		else 
		{
			// Try and remove the copy that's installed
			if (Uninstall())
			{
				// Get the executable file path
				char szFilePath[_MAX_PATH];
				::GetModuleFileName(NULL, szFilePath, sizeof(szFilePath));
				printf("%s removido.\n (Voce precisa deletar o arquivo %s)\n",
					   m_szServiceName, szFilePath);
			}
			else
			{
				printf("%s nao pode ser removido. Erro %d\n", m_szServiceName, GetLastError());
			}
		}
        return TRUE; // say we processed the argument
    }

	if (_stricmp(argv[1], "-d") == 0)
	{
		m_bIsDebuging = TRUE;
        printf("%s esta rodando em modo console.\n", m_szServiceName);
    }
         
    // Don't recognise the args
    return FALSE;
}

////////////////////////////////////////////////////////////////////////////////////////
// Install/uninstall routines

// Test if the service is currently installed
BOOL CNTService::IsInstalled()
{

    // Open the Service Control Manager
    SC_HANDLE hSCM = ::OpenSCManager(NULL, // local machine
                                     NULL, // ServicesActive database
                                     SC_MANAGER_ALL_ACCESS); // full access
    if (hSCM)
	{
        // Try to open the service
        SC_HANDLE hService = ::OpenService(hSCM,
                                           m_szServiceName,
                                           SERVICE_QUERY_CONFIG);
        if (hService)
		{
            ::CloseServiceHandle(hService);
			return TRUE;
        }

        ::CloseServiceHandle(hSCM);
		return FALSE;
    }

	LPVOID lpMsgBuf;
 
	FormatMessage( 
	FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
	NULL,
    GetLastError(),
    MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
    (LPTSTR) &lpMsgBuf,
    0,
    NULL 
	);

	LocalFree( lpMsgBuf );

    return FALSE;
}

BOOL CNTService::IsSqlInstalled()
{
	BOOL rt = FALSE;

    // Open the Service Control Manager
    SC_HANDLE hSCM = ::OpenSCManager(NULL, // local machine
                                     NULL, // ServicesActive database
                                     SC_MANAGER_ALL_ACCESS); // full access

    if (hSCM)
	{
        // Try to open the service
        SC_HANDLE hService = ::OpenService(hSCM,
                                           m_szDependencies,
                                           SERVICE_QUERY_CONFIG);
        if (hService)
		{
            ::CloseServiceHandle(hService);
			rt = TRUE;
        }

        ::CloseServiceHandle(hSCM);

    }

	return rt;
}

BOOL CNTService::Install()
{

    // Open the Service Control Manager
    SC_HANDLE hSCM = ::OpenSCManager(NULL, // local machine
                                     NULL, // ServicesActive database
                                     SC_MANAGER_ALL_ACCESS); // full access
    if (hSCM == 0)
	{
		return FALSE;
	}

    // Get the executable file path
    char szFilePath[_MAX_PATH];
    ::GetModuleFileName(NULL, szFilePath, sizeof(szFilePath));

	 SC_HANDLE hService;

	if (IsSqlInstalled())
	{
	    // Create the service com dependencia
		hService = ::CreateService(hSCM,
		                                 m_szServiceName,
                                         m_szServiceName,
                                         SERVICE_ALL_ACCESS,
                                         SERVICE_INTERACTIVE_PROCESS | SERVICE_WIN32_OWN_PROCESS ,
                                         SERVICE_AUTO_START ,        // start condition
                                         SERVICE_ERROR_NORMAL,
                                         szFilePath,
                                         NULL,
                                         NULL,
                                         (char *) m_szDependencies,
                                         NULL,
                                         NULL);
	}
	else
	{
	    // Create the service sem dependencia
		hService = ::CreateService(hSCM,
		                                 m_szServiceName,
                                         m_szServiceName,
                                         SERVICE_ALL_ACCESS,
                                         SERVICE_WIN32_OWN_PROCESS,
                                         SERVICE_AUTO_START ,        // start condition
                                         SERVICE_ERROR_NORMAL,
                                         szFilePath,
                                         NULL,
                                         NULL,
                                         NULL,
                                         NULL,
                                         NULL);
	}
    if (!hService)
	{
        ::CloseServiceHandle(hSCM);
        return FALSE;
    }

    // make registry entries to support logging messages
    // Add the source name as a subkey under the Application
    // key in the EventLog service portion of the registry.
    char szKey[256];
    HKEY hKey = NULL;
    strcpy(szKey, "SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\");
    strcat(szKey, m_szServiceName);
    if (::RegCreateKey(HKEY_LOCAL_MACHINE, szKey, &hKey) != ERROR_SUCCESS)
	{
        ::CloseServiceHandle(hService);
        ::CloseServiceHandle(hSCM);
        return FALSE;
    }

    // Add the Event ID message-file name to the 'EventMessageFile' subkey.
    ::RegSetValueEx(hKey,
                    "EventMessageFile",
                    0,
                    REG_EXPAND_SZ, 
                    (CONST BYTE*)szFilePath,
                    strlen(szFilePath) + 1);     

    // Set the supported types flags.
    DWORD dwData = EVENTLOG_ERROR_TYPE | EVENTLOG_WARNING_TYPE | EVENTLOG_INFORMATION_TYPE;
    ::RegSetValueEx(hKey,
                    "TypesSupported",
                    0,
                    REG_DWORD,
                    (CONST BYTE*)&dwData,
                     sizeof(DWORD));
    ::RegCloseKey(hKey);

    LogEvent(EVENTLOG_INFORMATION_TYPE, EVMSG_INSTALLED,m_szServiceName);

    // tidy up
    ::CloseServiceHandle(hService);
    ::CloseServiceHandle(hSCM);
    return TRUE;
}

BOOL CNTService::Uninstall()
{
    // Open the Service Control Manager
    SC_HANDLE hSCM = ::OpenSCManager(NULL, // local machine
                                     NULL, // ServicesActive database
                                     SC_MANAGER_ALL_ACCESS); // full access
    if (!hSCM) return FALSE;

    BOOL bResult = FALSE;
    SC_HANDLE hService = ::OpenService(hSCM,
                                       m_szServiceName,
                                       DELETE);
    if (hService)
	{
        if (::DeleteService(hService))
		{
            LogEvent(EVENTLOG_INFORMATION_TYPE, EVMSG_REMOVED,m_szServiceName);
            bResult = TRUE;
        }
		else
		{
            LogEvent(EVENTLOG_ERROR_TYPE, EVMSG_NOTREMOVED,m_szServiceName);
        }
        ::CloseServiceHandle(hService);
    }
    
    ::CloseServiceHandle(hSCM);
    return bResult;
}

///////////////////////////////////////////////////////////////////////////////////////
// Logging functions

// This function makes an entry into the application event log
void CNTService::LogEvent(WORD wType, DWORD dwID,
                          const char* pszS1,
                          const char* pszS2,
                          const char* pszS3)
{
    const char* ps[3];
    ps[0] = pszS1;
    ps[1] = pszS2;
    ps[2] = pszS3;

    int iStr = 0;
    
	for (int i = 0; i < 3; i++)
	{
        if (ps[i] != NULL) iStr++;
    }
        
    // Check the event source has been registered and if
    // not then register it now
    if (!m_hEventSource)
	{
        m_hEventSource = ::RegisterEventSource(NULL,  // local machine
                                               m_szServiceName); // source name
    }

    if (m_hEventSource)
	{
        ::ReportEvent(m_hEventSource,
                      wType,
                      0,
                      dwID,
                      NULL, // sid
                      iStr,
                      0,
                      ps,
                      NULL);
    }
}

//////////////////////////////////////////////////////////////////////////////////////////////
// Service startup and registration

BOOL CNTService::StartService()
{
	BOOL b = FALSE;
    
	SERVICE_TABLE_ENTRY st[] =
	{
	    {m_szServiceName, ServiceMain},
        {NULL, NULL}
    };
	
    // Register the handle console
    SetConsoleCtrlHandler(handler_console_routine,TRUE);

	if (m_bIsDebuging == TRUE)
	{
		CNTService* pService = m_pThis;
        pService->m_bIsRunning = TRUE;
        pService->m_Status.dwWin32ExitCode = 0;
        pService->m_Status.dwCheckPoint = 0;
        pService->m_Status.dwWaitHint = 0;
        pService->Run();
		b = TRUE;
	}
	else
	{
		b = ::StartServiceCtrlDispatcher(st);
    }
	
    // libera the handle console
    SetConsoleCtrlHandler(handler_console_routine,FALSE);

	return b;
}

// static member function (callback)
void CNTService::ServiceMain(DWORD dwArgc, LPTSTR* lpszArgv)
{
    // Get a pointer to the C++ object
    CNTService* pService = m_pThis;
    
    // Register the control request handler
    pService->m_hServiceStatus = RegisterServiceCtrlHandler(pService->m_szServiceName,
                                                           Handler);
    if (pService->m_hServiceStatus == NULL)
	{
        pService->LogEvent(EVENTLOG_ERROR_TYPE, EVMSG_CTRLHANDLERNOTINSTALLED);
        return;
    }


    // Start the initialisation
    if (pService->Initialize())
	{
        // Do the real work. 
        // When the Run function returns, the service has stopped.
        pService->m_bIsRunning = TRUE;
        pService->m_Status.dwWin32ExitCode = 0;
        pService->m_Status.dwCheckPoint = 0;
        pService->m_Status.dwWaitHint = 0;
        pService->Run();
		pService->LogEvent(EVENTLOG_INFORMATION_TYPE,EVMSG_STOPPED,pService->m_szServiceName);
        pService->m_bIsRunning = FALSE;
	}

    // Tell the service manager we are stopped
    pService->SetStatus(SERVICE_STOPPED);

}

///////////////////////////////////////////////////////////////////////////////////////////
// status functions

void CNTService::SetStatus(DWORD dwState)
{
    m_Status.dwCurrentState = dwState;
    ::SetServiceStatus(m_hServiceStatus, &m_Status);
}

///////////////////////////////////////////////////////////////////////////////////////////
// Service initialization

BOOL CNTService::Initialize()
{
    // Start the initialization
    SetStatus(SERVICE_START_PENDING);
    
    // Perform the actual initialization
    BOOL bResult = OnInit(); 
    
    // Set final state
    m_Status.dwWin32ExitCode = GetLastError();
    m_Status.dwCheckPoint = 0;
    m_Status.dwWaitHint = 0;

    if (!bResult)
	{
        LogEvent(EVENTLOG_ERROR_TYPE, EVMSG_FAILEDINIT,m_szServiceName);
        SetStatus(SERVICE_STOPPED);
        return FALSE;    
    }
    
    LogEvent(EVENTLOG_INFORMATION_TYPE, EVMSG_STARTED,m_szServiceName);
    SetStatus(SERVICE_START_PENDING);

    return TRUE;
}

///////////////////////////////////////////////////////////////////////////////////////////////
// main function to do the real work of the service

// This function performs the main work of the service. 
// When this function returns the service has stopped.
void CNTService::Run()
{
    while (m_bIsRunning)
	{
        Sleep(1000);
    }

    // nothing more to do
}

//////////////////////////////////////////////////////////////////////////////////////
// Control request handlers

// static member function (callback) to handle commands from the
// service control manager
void CNTService::Handler(DWORD dwOpcode)
{
    // Get a pointer to the object
    CNTService* pService = m_pThis;
    
    switch (dwOpcode)
	{
	    case SERVICE_CONTROL_STOP: // 1
		    pService->SetStatus(SERVICE_STOP_PENDING);
			pService->OnStop();
			break;

		case SERVICE_CONTROL_PAUSE: // 2
			pService->OnPause();
			break;

		case SERVICE_CONTROL_CONTINUE: // 3
			pService->OnContinue();
			break;

		case SERVICE_CONTROL_INTERROGATE: // 4
			pService->OnInterrogate(pService->m_Status.dwCurrentState);
			break;

		case SERVICE_CONTROL_SHUTDOWN: // 5
			pService->LogEvent(EVENTLOG_INFORMATION_TYPE, EVMSG_SHUTDOWN,pService->m_szServiceName);
			pService->OnShutdown();
			break;

		default:
			if (dwOpcode >= SERVICE_CONTROL_USER)
			{
				if (!pService->OnUserControl(dwOpcode))
				{
                pService->LogEvent(EVENTLOG_ERROR_TYPE, EVMSG_BADREQUEST,pService->m_szServiceName);
				}
			} 
			else
			{
				pService->LogEvent(EVENTLOG_ERROR_TYPE, EVMSG_BADREQUEST,pService->m_szServiceName);
			}
			break;
    }

    // Report current status
//    ::SetServiceStatus(pService->m_hServiceStatus, &pService->m_Status);
}

BOOL WINAPI CNTService::handler_console_routine(DWORD dwCtrlType)
{
    // Get a pointer to the object
    CNTService* pService = m_pThis;
    
    switch (dwCtrlType)
	{
		case CTRL_C_EVENT:
		case CTRL_LOGOFF_EVENT:
		case CTRL_BREAK_EVENT:
			break;
		case CTRL_CLOSE_EVENT:
			pService->OnShutdown();
			break;

		case CTRL_SHUTDOWN_EVENT: 
			pService->LogEvent(EVENTLOG_INFORMATION_TYPE, EVMSG_SHUTDOWN, pService->m_szServiceName);
			pService->m_bIsShutDownNow = TRUE;
			pService->OnShutdown();
			break;

		default:
			break;
    }
	return(TRUE);
}
        
// Called when the service is first initialized
BOOL CNTService::OnInit()
{
    MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"NtService OnInit Rotina dummy executada");
	return TRUE;
}

// Called when the service control manager wants to stop the service
void CNTService::OnStop()
{
    MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"NtService OnStop Rotina dummy executada");
}

// called when the service is interrogated
void CNTService::OnInterrogate(DWORD   Status)
{
    CNTService* pService = m_pThis;

    if (m_hServiceStatus) 
    { 
        pService->m_Status.dwCurrentState = Status; 
        if ((Status == SERVICE_START_PENDING) || (Status == SERVICE_STOP_PENDING)) 
        { 
            pService->m_Status.dwCheckPoint ++; 
            pService->m_Status.dwWaitHint = 15000;    // 15 sec. 
        } 
        else 
        { 
            pService->m_Status.dwCheckPoint = 0; 
            pService->m_Status.dwWaitHint = 0; 
        } 
 
        ::SetServiceStatus(m_hServiceStatus, &pService->m_Status); 
        return; 
    } 
 
//    MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"NtService OnInterrogate Rotina dummy executada");
}

// called when the service is paused
void CNTService::OnPause()
{
    MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"NtService OnPause Rotina dummy executada");
}

// called when the service is continued
void CNTService::OnContinue()
{
    MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"NtService OnContinue Rotina dummy executada");
}

// called when the service is shut down
void CNTService::OnShutdown()
{
    MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"NtService OnShutdown Rotina dummy executada");
}

// called when the service gets a user control message
BOOL CNTService::OnUserControl(DWORD dwOpcode)
{
    MsgToLog(EVENTLOG_ERROR_TYPE,EVMSG_MAIN,"NtService OnUserControl Rotina dummy executada");
    return FALSE; // say not handled
}


////////////////////////////////////////////////////////////////////////////////////////////
// Debugging support

void CNTService::MsgToLog(WORD wType, DWORD dwID, const char* pszTexto)
{
    CNTService* pService = m_pThis;
//    OutputDebugString(buf);
    pService->LogEvent(wType, dwID, pszTexto);
}
