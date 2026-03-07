// BCMsgSqlMq.cpp - x64 Logging DLL Implementation
// Created: 2026-02-27
// Purpose: Replace 32-bit BCMsgSqlMq.dll with x64 version

#include "BCMsgSqlMq.h"
#include <stdio.h>
#include <time.h>
#include <string>
#include <mutex>

// Global state
static FILE* g_logFile = nullptr;
static std::mutex g_logMutex;
static UINT g_traceLevel = 0;
static std::string g_logFilePath;

// Helper to get timestamp
static std::string GetTimestamp() {
    time_t now = time(nullptr);
    struct tm timeinfo;
    localtime_s(&timeinfo, &now);

    char buffer[64];
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", &timeinfo);
    return std::string(buffer);
}

// Helper to convert LPVOID to string for logging
static std::string PtrToString(LPVOID ptr) {
    if (ptr == nullptr) return "NULL";

    // Try to interpret as integer pointer
    int* intPtr = static_cast<int*>(ptr);
    char buffer[32];
    sprintf_s(buffer, sizeof(buffer), "%d", *intPtr);
    return std::string(buffer);
}

// OpenLog - Opens log file
// Parameters appear to be: logPath, appName, serverName (based on typical logging patterns)
extern "C" BOOL CALLBACK OpenLog(LPTSTR param1, LPTSTR param2, LPTSTR param3) {
    std::lock_guard<std::mutex> lock(g_logMutex);

    try {
        // Close existing log if open
        if (g_logFile != nullptr) {
            fclose(g_logFile);
            g_logFile = nullptr;
        }

        // Build log file path
        // param1 is likely the log directory
        // param2 is likely the application name
        std::string logDir = param1 ? param1 : "C:\\BCSrvSqlMq\\Logs";
        std::string appName = param2 ? param2 : "BCSrvSqlMq";

        // Create filename with date
        time_t now = time(nullptr);
        struct tm timeinfo;
        localtime_s(&timeinfo, &now);

        char dateStr[32];
        strftime(dateStr, sizeof(dateStr), "%Y%m%d", &timeinfo);

        g_logFilePath = logDir + "\\" + appName + "_" + dateStr + ".log";

        // Create directory if it doesn't exist
        CreateDirectoryA(logDir.c_str(), nullptr);

        // Open log file in append mode
        fopen_s(&g_logFile, g_logFilePath.c_str(), "a");

        if (g_logFile == nullptr) {
            return FALSE;
        }

        // Write header
        fprintf(g_logFile, "\n========================================\n");
        fprintf(g_logFile, "Log opened: %s\n", GetTimestamp().c_str());
        fprintf(g_logFile, "Application: %s\n", appName.c_str());
        if (param3) {
            fprintf(g_logFile, "Server: %s\n", param3);
        }
        fprintf(g_logFile, "========================================\n\n");
        fflush(g_logFile);

        return TRUE;
    }
    catch (...) {
        return FALSE;
    }
}

// WriteLog - Writes log message
// taskName: Name of the task/thread
// msgId: Message ID
// flag: Type flag (TRUE for error, FALSE for info)
// p1-p5: Additional parameters for message formatting
extern "C" BOOL CALLBACK WriteLog(LPTSTR taskName, UINT msgId, BOOL flag,
                                   LPVOID p1, LPVOID p2, LPVOID p3, LPVOID p4, LPVOID p5) {
    std::lock_guard<std::mutex> lock(g_logMutex);

    try {
        if (g_logFile == nullptr) {
            return FALSE;
        }

        // Write log entry
        fprintf(g_logFile, "[%s] [%s] [MsgID:%u] ",
                GetTimestamp().c_str(),
                flag ? "ERROR" : "INFO",
                msgId);

        if (taskName) {
            fprintf(g_logFile, "[Task:%s] ", taskName);
        }

        // Write parameters if present
        bool hasParams = false;
        if (p1 || p2 || p3 || p4 || p5) {
            fprintf(g_logFile, "Params: ");
            hasParams = true;
        }

        if (p1) fprintf(g_logFile, "p1=%s ", PtrToString(p1).c_str());
        if (p2) fprintf(g_logFile, "p2=%s ", PtrToString(p2).c_str());
        if (p3) fprintf(g_logFile, "p3=%s ", PtrToString(p3).c_str());
        if (p4) fprintf(g_logFile, "p4=%s ", PtrToString(p4).c_str());
        if (p5) fprintf(g_logFile, "p5=%s ", PtrToString(p5).c_str());

        fprintf(g_logFile, "\n");
        fflush(g_logFile);

        return TRUE;
    }
    catch (...) {
        return FALSE;
    }
}

// WriteReg - Writes binary/registry data
// taskName: Name of the task
// flag: Type flag
// size: Size of data
// data: Pointer to data
extern "C" BOOL CALLBACK WriteReg(LPTSTR taskName, BOOL flag, UINT size, LPVOID data) {
    std::lock_guard<std::mutex> lock(g_logMutex);

    try {
        if (g_logFile == nullptr) {
            return FALSE;
        }

        fprintf(g_logFile, "[%s] [REGISTRY] [%s] ",
                GetTimestamp().c_str(),
                flag ? "WRITE" : "READ");

        if (taskName) {
            fprintf(g_logFile, "[Task:%s] ", taskName);
        }

        fprintf(g_logFile, "Size:%u bytes", size);

        // Write hex dump if data present and size reasonable
        if (data && size > 0 && size <= 1024) {
            fprintf(g_logFile, " Data: ");
            unsigned char* bytes = static_cast<unsigned char*>(data);
            for (UINT i = 0; i < size && i < 64; i++) {
                fprintf(g_logFile, "%02X ", bytes[i]);
            }
            if (size > 64) {
                fprintf(g_logFile, "... (%u more bytes)", size - 64);
            }
        }

        fprintf(g_logFile, "\n");
        fflush(g_logFile);

        return TRUE;
    }
    catch (...) {
        return FALSE;
    }
}

// CloseLog - Closes log file
extern "C" BOOL CALLBACK CloseLog() {
    std::lock_guard<std::mutex> lock(g_logMutex);

    try {
        if (g_logFile != nullptr) {
            fprintf(g_logFile, "\n========================================\n");
            fprintf(g_logFile, "Log closed: %s\n", GetTimestamp().c_str());
            fprintf(g_logFile, "========================================\n\n");
            fflush(g_logFile);

            fclose(g_logFile);
            g_logFile = nullptr;
        }

        return TRUE;
    }
    catch (...) {
        return FALSE;
    }
}

// Trace - Sets trace level
extern "C" BOOL CALLBACK Trace(UINT level) {
    std::lock_guard<std::mutex> lock(g_logMutex);

    try {
        g_traceLevel = level;

        if (g_logFile != nullptr) {
            fprintf(g_logFile, "[%s] [TRACE] Level set to: %u\n",
                    GetTimestamp().c_str(), level);
            fflush(g_logFile);
        }

        return TRUE;
    }
    catch (...) {
        return FALSE;
    }
}
