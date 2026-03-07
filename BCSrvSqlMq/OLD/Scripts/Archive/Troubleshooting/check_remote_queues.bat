@echo off
REM Check if REMOTE queues exist

echo Checking REMOTE queues (QR.*)...
echo.

echo DISPLAY QUEUE(QR.61377677.01.ENTRADA.BACEN) > %TEMP%\mqsc_check.txt
echo DISPLAY QUEUE(QR.61377677.01.SAIDA.BACEN) >> %TEMP%\mqsc_check.txt
echo DISPLAY QUEUE(QR.61377677.01.REPORT.BACEN) >> %TEMP%\mqsc_check.txt
echo DISPLAY QUEUE(QR.61377677.01.SUPORTE.BACEN) >> %TEMP%\mqsc_check.txt
echo DISPLAY QUEUE(QR.61377677.01.ENTRADA.IF) >> %TEMP%\mqsc_check.txt
echo DISPLAY QUEUE(QR.61377677.01.SAIDA.IF) >> %TEMP%\mqsc_check.txt
echo DISPLAY QUEUE(QR.61377677.01.REPORT.IF) >> %TEMP%\mqsc_check.txt
echo DISPLAY QUEUE(QR.61377677.01.SUPORTE.IF) >> %TEMP%\mqsc_check.txt
echo END >> %TEMP%\mqsc_check.txt

type %TEMP%\mqsc_check.txt | runmqsc QM.61377677.01

echo.
echo.
echo If you see "AMQ8147E: WebSphere MQ queue not found" - the remote queues DO NOT EXIST!
echo.
pause
