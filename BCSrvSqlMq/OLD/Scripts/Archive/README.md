# Archived Troubleshooting Scripts

**Archive Date**: 01/03/2026 17:32:54,05
**Reason**: x64 migration successfully completed

These scripts were used during troubleshooting of error 2085 and related issues.
All issues have been resolved and these scripts are no longer needed for normal operation.

## Issues Resolved

1. **Error 2085** - MQRC_UNKNOWN_OBJECT_NAME
2. **Missing IF queue variables** - Added to InitSrv.h/cpp
3. **Wrong INI file location** - Service reads from build\Release\
4. **Queue configuration mismatches** - All 8 tasks now working

## Scripts Kept (in Scripts directory)

- INSTALAR.bat - Service installation
- INICIAR.bat - Start service
- VER-LOG.bat - View logs
- TESTAR-CRYPTO.bat/ps1 - OpenSSL testing
- rebuild_and_deploy.bat - Rebuild service
- send_test_message.bat/ps1 - Message testing
- test_console_mode.bat - Console mode
- setup_database.bat - Database setup
- setup_mq_queues.bat - Queue setup

## Reference

For complete migration documentation, see:
- X64_MIGRATION_SUCCESS.md
- QUICK_REFERENCE.md

