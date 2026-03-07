// BCMsgSqlMq.h - x64 Logging DLL
// Created: 2026-02-27
// Purpose: Replace 32-bit BCMsgSqlMq.dll with x64 version

#ifndef _BCMSGSQLMQ_H_
#define _BCMSGSQLMQ_H_

#include <windows.h>

#ifdef BCMSGSQLMQ_EXPORTS
#define BCMSGSQLMQ_API __declspec(dllexport)
#else
#define BCMSGSQLMQ_API __declspec(dllimport)
#endif

// Function prototypes matching original DLL interface
extern "C" {
    BCMSGSQLMQ_API BOOL CALLBACK OpenLog(LPTSTR param1, LPTSTR param2, LPTSTR param3);
    BCMSGSQLMQ_API BOOL CALLBACK WriteLog(LPTSTR taskName, UINT msgId, BOOL flag, LPVOID p1, LPVOID p2, LPVOID p3, LPVOID p4, LPVOID p5);
    BCMSGSQLMQ_API BOOL CALLBACK WriteReg(LPTSTR taskName, BOOL flag, UINT size, LPVOID data);
    BCMSGSQLMQ_API BOOL CALLBACK CloseLog();
    BCMSGSQLMQ_API BOOL CALLBACK Trace(UINT level);
}

#endif // _BCMSGSQLMQ_H_
