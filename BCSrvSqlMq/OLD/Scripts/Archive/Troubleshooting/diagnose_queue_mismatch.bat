@echo off
REM ============================================================================
REM Diagnose Queue Name Mismatch - Compare INI vs Actual MQ Queues
REM ============================================================================

color 0E
title Queue Name Diagnostic

cls
echo.
echo ============================================================================
echo QUEUE NAME DIAGNOSTIC - Finding the Mismatch
echo ============================================================================
echo.

set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"

echo [Step 1] Actual Queue Names in MQ (Local Queues):
echo ============================================================================
echo.
(
echo DISPLAY QUEUE^(QL*^)
echo END
) | runmqsc QM.61377677.01 2>nul | findstr /C:"QUEUE(" | findstr "QL.61377677"
echo.

echo [Step 2] Actual Queue Names in MQ (Remote Queues):
echo ============================================================================
echo.
(
echo DISPLAY QUEUE^(QR*^)
echo END
) | runmqsc QM.61377677.01 2>nul | findstr /C:"QUEUE(" | findstr "QR.61377677"
echo.

echo [Step 3] ALL Queues in Queue Manager (for comparison):
echo ============================================================================
echo.
(
echo DISPLAY QUEUE^(*^) WHERE^(QTYPE EQ QLOCAL^)
echo END
) | runmqsc QM.61377677.01 2>nul | findstr /C:"QUEUE("
echo.

echo [Step 4] Queue Names Expected by BCSrvSqlMq.ini:
echo ============================================================================
echo.
echo Reading from BCSrvSqlMq.ini...
echo.
findstr /C:"QL" /C:"QR" "C:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\BCSrvSqlMq.ini" | findstr /V "^;"
echo.

echo ============================================================================
echo LOOK FOR MISMATCHES!
echo ============================================================================
echo.
echo Compare the queue names above:
echo   - MQ actual names (from DISPLAY QUEUE)
echo   - INI expected names (from BCSrvSqlMq.ini)
echo.
echo Common issues:
echo   1. Case mismatch (e.g., "entrada" vs "ENTRADA")
echo   2. Wrong QTYPE (should be QLOCAL for QL.*, QREMOTE for QR.*)
echo   3. Typos or extra spaces
echo   4. Queue doesn't exist
echo.

pause
