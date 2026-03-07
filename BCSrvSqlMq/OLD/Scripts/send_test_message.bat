@echo off
REM ============================================================================
REM BCSrvSqlMq - Send Test Message to MQ Queue
REM This will trigger the service to process a message with OpenSSL
REM ============================================================================

color 0E
title Send Test Message to MQ

echo.
echo ============================================================================
echo SEND TEST MESSAGE TO MQ QUEUE
echo ============================================================================
echo.

set QMGR=QM.61377677.01
set QUEUE=QL.61377677.01.ENTRADA.IF

echo Queue Manager: %QMGR%
echo Target Queue:   %QUEUE%
echo.
echo This will send a test message to trigger the service.
echo The service will process it with OpenSSL crypto functions!
echo.
echo Press ENTER to send test message, or Ctrl+C to cancel...
pause >nul

REM Set PATH
set "PATH=%PATH%;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"

echo.
echo Creating test message...
echo.

REM Create test message content
echo TEST_MESSAGE_FROM_BCSrvSqlMq_OPENSSL_MIGRATION > test_message.txt
echo Timestamp: %date% %time% >> test_message.txt
echo Architecture: x64 >> test_message.txt
echo Crypto: OpenSSL 3.6.1 >> test_message.txt
echo Purpose: Verify certificate loading and signing >> test_message.txt

echo Message content:
type test_message.txt
echo.
echo.

echo Sending message to queue %QUEUE%...
echo.

REM Create MQSC script to put message
echo * Put test message to queue > put_message.mqsc
echo DEFINE QLOCAL(TEMP.TEST.QUEUE) REPLACE >> put_message.mqsc
echo PUT %QUEUE% >> put_message.mqsc

REM Try using amqsput (sample program) instead
echo Attempting to put message using amqsput...
echo.

REM Check if amqsput exists
where amqsput >nul 2>&1
if %errorlevel% EQU 0 (
    echo Found amqsput - using it to send message
    echo.
    echo Instructions:
    echo 1. The program will start
    echo 2. Type your message or press Ctrl+Z then ENTER to use file
    echo 3. Press ENTER twice to send
    echo.
    pause
    type test_message.txt | amqsput %QMGR% %QUEUE%
) else (
    echo amqsput not found, trying alternative method...
    echo.
    echo Creating MQSC script...

    REM Alternative: Use runmqsc with inline message
    echo DEFINE QLOCAL('TEST.INPUT.QUEUE') REPLACE > send_test.mqsc
    echo PUT TEST.INPUT.QUEUE >> send_test.mqsc

    runmqsc %QMGR% < send_test.mqsc

    del send_test.mqsc >nul 2>&1
)

echo.
echo ============================================================================
echo MESSAGE SENT (or attempted)
echo ============================================================================
echo.
echo NEXT STEPS:
echo.
echo 1. Check service logs:
echo    Scripts\VER-LOG.bat
echo.
echo 2. Look for these log entries:
echo    [INFO] ReadPublicKey - Loading certificate
echo    [INFO] ReadPrivatKey - Loading private key
echo    [INFO] funcAssinar - Signing message
echo    [INFO] funcCript - Encrypting data
echo.
echo 3. This proves OpenSSL is working in production!
echo.

REM Cleanup
del test_message.txt >nul 2>&1
del put_message.mqsc >nul 2>&1

pause
