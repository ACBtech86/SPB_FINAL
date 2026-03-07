# Debug Error 2085 - Check exact error from MQ logs

Write-Host "`n=== CHECKING INI FILE QUEUE NAMES ===" -ForegroundColor Cyan
Write-Host "Looking for any hidden characters or spaces...`n" -ForegroundColor Yellow

$iniPath = "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\BCSrvSqlMq.ini"
Get-Content $iniPath | Select-String "QR|QL" | ForEach-Object {
    $line = $_.Line
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($line)
    Write-Host "$line" -ForegroundColor White
    Write-Host "  Length: $($line.Length) chars, Bytes: $($bytes.Length)" -ForegroundColor Gray
}

Write-Host "`n=== ENABLING DETAILED MQ LOGGING ===" -ForegroundColor Cyan

$mqscCmd = @"
ALTER QMGR LOGGEREVT(ENABLED)
END
"@

$mqscCmd | & 'C:\Program Files\IBM\MQ\bin\runmqsc' QM.61377677.01

Write-Host "`n=== RESTARTING SERVICE TO CAPTURE ERROR ===" -ForegroundColor Cyan

net start BCSrvSqlMq | Out-Null
Write-Host "Service started, waiting 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

net stop BCSrvSqlMq | Out-Null
Write-Host "Service stopped`n" -ForegroundColor Yellow

Write-Host "=== CHECKING MQ ERROR LOGS ===" -ForegroundColor Cyan
Write-Host "Looking for error 2085 details...`n" -ForegroundColor Yellow

$errorLog = "C:\ProgramData\IBM\MQ\qmgrs\QM!61377677!01\errors\AMQERR01.LOG"
if (Test-Path $errorLog) {
    Get-Content $errorLog -Tail 200 | Select-String "2085|MQOPEN|MQRC_UNKNOWN|Object\(" -Context 2,2 | ForEach-Object {
        Write-Host $_.Line -ForegroundColor Red
        $_.Context.PreContext | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        $_.Context.PostContext | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        Write-Host ""
    }
} else {
    Write-Host "Error log not found at: $errorLog" -ForegroundColor Red
}

Write-Host "`n=== DONE ===" -ForegroundColor Cyan
Write-Host "If you see object names in the error log, compare them carefully with the INI file!" -ForegroundColor Yellow
