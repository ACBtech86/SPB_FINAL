# ============================================================================
# List ALL Queues in Queue Manager
# ============================================================================

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "ALL QUEUES IN QUEUE MANAGER QM.61377677.01" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$env:PATH += ";C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"

# Create MQSC commands
$mqscCommands = @"
DISPLAY QUEUE(*)
END
"@

Write-Host "Running MQSC commands..." -ForegroundColor Yellow
Write-Host ""

# Execute via pipeline
$mqscCommands | runmqsc QM.61377677.01

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
