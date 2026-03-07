// NTService.cpp
// 
// This is the main program file containing the entry point.

#include <afx.h>
#include "NTServApp.h"
#include "InitSrv.h"

int main(int argc, char* argv[])
{
    // Create the service object
	char m_ARQINI[MAX_PATH];
	char m_ServiceName[MAX_PATH];
	
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

	GetPrivateProfileString("Servico", "ServiceName","BCSrvSqlMQ", m_ServiceName, MAX_PATH, m_ARQINI);

    CInitSrv InitSrv(m_ServiceName,"MSSQLServer");
    
    // Parse for standard arguments (install, uninstall, version etc.)
    if (!InitSrv.ParseStandardArgs(argc, argv)) {

        // Didn't find any standard args so start the service
        // Uncomment the DebugBreak line below to enter the debugger
        // when the service is started.
        //DebugBreak();
        InitSrv.StartService();
    }

    // When we get here, the service has been stopped
    return InitSrv.m_Status.dwWin32ExitCode;
}
