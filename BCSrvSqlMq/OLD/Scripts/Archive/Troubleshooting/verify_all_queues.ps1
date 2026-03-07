# ============================================================================
# Verify All 16 Queues Exist
# ============================================================================

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "VERIFY ALL 16 QUEUES EXIST" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$env:PATH += ";C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"

# Check Local Queues (QL.*)
Write-Host "[1/2] Checking LOCAL QUEUES (QL.61377677.01.*)..." -ForegroundColor Yellow
Write-Host ""

$localQueues = @"
DISPLAY QUEUE(QL.61377677.01.ENTRADA.BACEN)
DISPLAY QUEUE(QL.61377677.01.SAIDA.BACEN)
DISPLAY QUEUE(QL.61377677.01.REPORT.BACEN)
DISPLAY QUEUE(QL.61377677.01.SUPORTE.BACEN)
DISPLAY QUEUE(QL.61377677.01.ENTRADA.IF)
DISPLAY QUEUE(QL.61377677.01.SAIDA.IF)
DISPLAY QUEUE(QL.61377677.01.REPORT.IF)
DISPLAY QUEUE(QL.61377677.01.SUPORTE.IF)
END
"@

$result = $localQueues | runmqsc QM.61377677.01 2>&1 | Select-String "QUEUE\(|AMQ8"
$result | ForEach-Object { Write-Host $_ }

Write-Host ""
Write-Host "[2/2] Checking REMOTE QUEUES (QR.61377677.01.*)..." -ForegroundColor Yellow
Write-Host ""

$remoteQueues = @"
DISPLAY QUEUE(QR.61377677.01.ENTRADA.BACEN)
DISPLAY QUEUE(QR.61377677.01.SAIDA.BACEN)
DISPLAY QUEUE(QR.61377677.01.REPORT.BACEN)
DISPLAY QUEUE(QR.61377677.01.SUPORTE.BACEN)
DISPLAY QUEUE(QR.61377677.01.ENTRADA.IF)
DISPLAY QUEUE(QR.61377677.01.SAIDA.IF)
DISPLAY QUEUE(QR.61377677.01.REPORT.IF)
DISPLAY QUEUE(QR.61377677.01.SUPORTE.IF)
END
"@

$result = $remoteQueues | runmqsc QM.61377677.01 2>&1 | Select-String "QUEUE\(|AMQ8"
$result | ForEach-Object { Write-Host $_ }

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Expected: 16 queues found (8 local + 8 remote)" -ForegroundColor Cyan
Write-Host "If any queue shows AMQ8147E (not found), it needs to be created!" -ForegroundColor Red
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
