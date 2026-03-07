// Test ODBC connection exactly like BCSrvSqlMq does
#include <windows.h>
#include <sql.h>
#include <sqlext.h>
#include <iostream>
#include <string>

int main() {
    SQLHENV hEnv = NULL;
    SQLHDBC hDbc = NULL;
    SQLRETURN ret;

    std::cout << "==============================================\n";
    std::cout << "Test ODBC Connection (32-bit)\n";
    std::cout << "==============================================\n\n";

    // Allocate environment handle
    ret = SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &hEnv);
    if (!SQL_SUCCEEDED(ret)) {
        std::cout << "[ERRO] Failed to allocate environment handle\n";
        return 1;
    }

    // Set ODBC version
    SQLSetEnvAttr(hEnv, SQL_ATTR_ODBC_VERSION, (void*)SQL_OV_ODBC3, 0);

    // Allocate connection handle
    ret = SQLAllocHandle(SQL_HANDLE_DBC, hEnv, &hDbc);
    if (!SQL_SUCCEEDED(ret)) {
        std::cout << "[ERRO] Failed to allocate connection handle\n";
        SQLFreeHandle(SQL_HANDLE_ENV, hEnv);
        return 1;
    }

    // Connection string - EXACTLY like BCSrvSqlMq uses
    std::string connStr = "DRIVER={PostgreSQL Unicode};"
                          "SERVER=localhost;"
                          "PORT=5432;"
                          "DATABASE=bcspbstr;"
                          "UID=postgres;"
                          "PWD=Rama1248;";

    std::cout << "Connection String:\n";
    std::cout << "  DRIVER={PostgreSQL Unicode}\n";
    std::cout << "  SERVER=localhost\n";
    std::cout << "  PORT=5432\n";
    std::cout << "  DATABASE=bcspbstr\n";
    std::cout << "  UID=postgres\n";
    std::cout << "  PWD=****\n\n";

    std::cout << "Attempting to connect...\n\n";

    SQLCHAR outConnStr[1024];
    SQLSMALLINT outConnStrLen;

    ret = SQLDriverConnect(hDbc, NULL, (SQLCHAR*)connStr.c_str(), SQL_NTS,
                          outConnStr, sizeof(outConnStr), &outConnStrLen,
                          SQL_DRIVER_NOPROMPT);

    if (SQL_SUCCEEDED(ret)) {
        std::cout << "==============================================\n";
        std::cout << "[SUCCESS] ODBC Connection Successful!\n";
        std::cout << "==============================================\n\n";
        std::cout << "BCSrvSqlMq should be able to connect!\n\n";

        // Test a simple query
        SQLHSTMT hStmt;
        SQLAllocHandle(SQL_HANDLE_STMT, hDbc, &hStmt);
        ret = SQLExecDirect(hStmt, (SQLCHAR*)"SELECT version();", SQL_NTS);
        if (SQL_SUCCEEDED(ret)) {
            SQLCHAR version[256];
            SQLFetch(hStmt);
            SQLGetData(hStmt, 1, SQL_C_CHAR, version, sizeof(version), NULL);
            std::cout << "PostgreSQL: " << version << "\n\n";
        }
        SQLFreeHandle(SQL_HANDLE_STMT, hStmt);

        SQLDisconnect(hDbc);
    } else {
        std::cout << "==============================================\n";
        std::cout << "[ERROR] ODBC Connection Failed!\n";
        std::cout << "==============================================\n\n";

        // Get error details
        SQLCHAR sqlState[6];
        SQLCHAR message[256];
        SQLINTEGER nativeError;
        SQLSMALLINT messageLen;

        SQLGetDiagRec(SQL_HANDLE_DBC, hDbc, 1, sqlState, &nativeError,
                     message, sizeof(message), &messageLen);

        std::cout << "SQL State: " << sqlState << "\n";
        std::cout << "Native Error: " << nativeError << "\n";
        std::cout << "Message: " << message << "\n\n";

        std::cout << "Possible causes:\n";
        std::cout << "1. Driver name mismatch\n";
        std::cout << "2. Wrong password\n";
        std::cout << "3. pg_hba.conf not allowing password auth\n";
        std::cout << "4. Need SSL parameters\n\n";
    }

    SQLFreeHandle(SQL_HANDLE_DBC, hDbc);
    SQLFreeHandle(SQL_HANDLE_ENV, hEnv);

    std::cout << "Press Enter to exit...\n";
    std::cin.get();

    return SQL_SUCCEEDED(ret) ? 0 : 1;
}
