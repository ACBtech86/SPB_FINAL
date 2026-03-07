@echo off
REM ============================================================================
REM BCSrvSqlMq Scripts Cleanup
REM Organizes scripts after successful x64 migration
REM ============================================================================

color 0E
title Scripts Cleanup - x64 Migration Complete

cls
echo.
echo ============================================================================
echo BCSrvSqlMq Scripts Cleanup
echo ============================================================================
echo.
echo This will organize the Scripts directory after successful migration:
echo   - Keep essential operational scripts
echo   - Archive troubleshooting scripts
echo   - Delete redundant scripts
echo.
echo Press Ctrl+C to cancel, or
pause

cd /d "%~dp0"

REM Create Archive directory
echo.
echo [1/3] Creating Archive directory...
if not exist "Archive" mkdir Archive
if not exist "Archive\Troubleshooting" mkdir "Archive\Troubleshooting"

REM ============================================================================
REM Move troubleshooting scripts to Archive
REM ============================================================================
echo.
echo [2/3] Moving troubleshooting scripts to Archive...

REM Queue diagnostics
move check_mq_queues.bat "Archive\Troubleshooting\" 2>nul
move check_mq_queues_debug.bat "Archive\Troubleshooting\" 2>nul
move check_queues_ultra_simple.bat "Archive\Troubleshooting\" 2>nul
move check_queues.ps1 "Archive\Troubleshooting\" 2>nul
move check_remote_queues.bat "Archive\Troubleshooting\" 2>nul
move create_all_16_queues.bat "Archive\Troubleshooting\" 2>nul
move list_all_queues.ps1 "Archive\Troubleshooting\" 2>nul
move list_all_queues_simple.bat "Archive\Troubleshooting\" 2>nul
move verify_all_queues.ps1 "Archive\Troubleshooting\" 2>nul

REM Permission diagnostics
move check_current_permissions.bat "Archive\Troubleshooting\" 2>nul
move check_mqm_group.bat "Archive\Troubleshooting\" 2>nul
move grant_permissions_each_queue.bat "Archive\Troubleshooting\" 2>nul
move grant_permissions_nt_authority.bat "Archive\Troubleshooting\" 2>nul
move grant_permissions_to_system.bat "Archive\Troubleshooting\" 2>nul
move fix_mq_permissions.bat "Archive\Troubleshooting\" 2>nul
move add_system_to_mqm.bat "Archive\Troubleshooting\" 2>nul
move diagnose_mq_permissions.bat "Archive\Troubleshooting\" 2>nul
move show_service_account.bat "Archive\Troubleshooting\" 2>nul

REM Error 2085 specific
move debug_error_2085.ps1 "Archive\Troubleshooting\" 2>nul
move diagnose_queue_mismatch.bat "Archive\Troubleshooting\" 2>nul
move rebuild_with_real_headers.bat "Archive\Troubleshooting\" 2>nul
move view_log_quick.bat "Archive\Troubleshooting\" 2>nul

REM Tracing/debugging
move enable_mq_trace.bat "Archive\Troubleshooting\" 2>nul
move disable_mq_trace.bat "Archive\Troubleshooting\" 2>nul
move check_mq_errors.bat "Archive\Troubleshooting\" 2>nul
move check_queue_managers.bat "Archive\Troubleshooting\" 2>nul
move check_latest_log.bat "Archive\Troubleshooting\" 2>nul

REM Old/redundant scripts
move RESTART-AND-CHECK.bat "Archive\Troubleshooting\" 2>nul
move test_rebuilt_binary.bat "Archive\Troubleshooting\" 2>nul
move test_mq_simple.bat "Archive\Troubleshooting\" 2>nul

REM ============================================================================
REM Delete redundant scripts
REM ============================================================================
echo.
echo [3/3] Deleting redundant scripts...

del /Q VER-ERRO.bat 2>nul
del /Q TESTAR-TUDO.bat 2>nul
del /Q TestarServico.bat 2>nul
del /Q DESBLOQUEAR.bat 2>nul
del /Q DIAGNOSTICO.bat 2>nul

REM ============================================================================
REM Create README for Archive
REM ============================================================================
echo.
echo Creating Archive README...

(
echo # Archived Troubleshooting Scripts
echo.
echo **Archive Date**: %DATE% %TIME%
echo **Reason**: x64 migration successfully completed
echo.
echo These scripts were used during troubleshooting of error 2085 and related issues.
echo All issues have been resolved and these scripts are no longer needed for normal operation.
echo.
echo ## Issues Resolved
echo.
echo 1. **Error 2085** - MQRC_UNKNOWN_OBJECT_NAME
echo 2. **Missing IF queue variables** - Added to InitSrv.h/cpp
echo 3. **Wrong INI file location** - Service reads from build\Release\
echo 4. **Queue configuration mismatches** - All 8 tasks now working
echo.
echo ## Scripts Kept (in Scripts directory^)
echo.
echo - INSTALAR.bat - Service installation
echo - INICIAR.bat - Start service
echo - VER-LOG.bat - View logs
echo - TESTAR-CRYPTO.bat/ps1 - OpenSSL testing
echo - rebuild_and_deploy.bat - Rebuild service
echo - send_test_message.bat/ps1 - Message testing
echo - test_console_mode.bat - Console mode
echo - setup_database.bat - Database setup
echo - setup_mq_queues.bat - Queue setup
echo.
echo ## Reference
echo.
echo For complete migration documentation, see:
echo - X64_MIGRATION_SUCCESS.md
echo - QUICK_REFERENCE.md
echo.
) > "Archive\README.md"

echo.
echo ============================================================================
echo Cleanup Complete!
echo ============================================================================
echo.
echo Archived: 30+ troubleshooting scripts
echo Deleted: 5 redundant scripts
echo Kept: 10 essential operational scripts
echo.
echo Archive location: Scripts\Archive\Troubleshooting\
echo.
pause
