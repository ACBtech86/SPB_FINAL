# IBM MQ Queue Check - PowerShell Version
# This will DEFINITELY stay open!

$Host.UI.RawUI.WindowTitle = "MQ Queue Check - PowerShell"
$Host.UI.RawUI.BackgroundColor = "DarkBlue"
$Host.UI.RawUI.ForegroundColor = "White"
Clear-Host

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "IBM MQ QUEUE CHECK - PowerShell Version" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$QMgr = "QM.61377677.01"
Write-Host "Queue Manager: $QMgr" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press ENTER to start checking queues..."
$null = Read-Host

Write-Host ""
Write-Host "[STEP 1/4] Setting up environment..." -ForegroundColor Green
$env:PATH = "$env:PATH;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"
Write-Host "OK" -ForegroundColor Green
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "[STEP 2/4] Creating MQSC script..." -ForegroundColor Green
$mqsc = @"
DISPLAY QLOCAL('QL.61377677.01.*')
DISPLAY QREMOTE('QR.61377677.01.*')
"@
$mqsc | Out-File -FilePath "check_temp.mqsc" -Encoding ASCII
Write-Host "OK - Script created" -ForegroundColor Green
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "[STEP 3/4] Running MQ query..." -ForegroundColor Green
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "MQ OUTPUT:" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

try {
    $output = cmd /c "runmqsc $QMgr < check_temp.mqsc 2>&1"
    $output | ForEach-Object { Write-Host $_ }

    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host ""

    # Analyze output
    if ($output -match "AMQ8147") {
        Write-Host "[RESULT] Queues DO NOT exist - need to create them!" -ForegroundColor Yellow
    } elseif ($output -match "QUEUE\(QL\.61377677") {
        Write-Host "[RESULT] Queues EXIST - ready to use!" -ForegroundColor Green
    } else {
        Write-Host "[RESULT] Inconclusive - check output above" -ForegroundColor Yellow
    }

} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "[STEP 4/4] Cleaning up..." -ForegroundColor Green
Remove-Item "check_temp.mqsc" -ErrorAction SilentlyContinue
Write-Host "OK" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "COMPLETE!" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This window will stay open."
Write-Host ""
Write-Host "Press ENTER to close..."
$null = Read-Host
