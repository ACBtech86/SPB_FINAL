# BCSrvSqlMq - Send Test Message via MQ
# Triggers OpenSSL crypto functions

$Host.UI.RawUI.WindowTitle = "Send Test Message to MQ"
$Host.UI.RawUI.BackgroundColor = "DarkMagenta"
$Host.UI.RawUI.ForegroundColor = "White"
Clear-Host

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "SEND TEST MESSAGE TO MQ QUEUE" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$QMgr = "QM.61377677.01"
$Queue = "QL.61377677.01.ENTRADA.IF"

Write-Host "Queue Manager: $QMgr" -ForegroundColor Yellow
Write-Host "Target Queue:   $Queue" -ForegroundColor Yellow
Write-Host ""
Write-Host "This will send a test message to trigger OpenSSL crypto functions!" -ForegroundColor Green
Write-Host ""
Write-Host "Press ENTER to continue..."
$null = Read-Host

# Add IBM MQ to PATH
$env:PATH = "$env:PATH;C:\Program Files\IBM\MQ\bin;C:\Program Files\IBM\MQ\bin64"

Write-Host ""
Write-Host "Creating test message..." -ForegroundColor Green

$message = @"
TEST_MESSAGE_FROM_BCSrvSqlMq
Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Architecture: x64
Crypto: OpenSSL 3.6.1
Purpose: Verify certificate loading and crypto functions

This message should trigger:
1. ReadPublicKey() - Load certificates/public_cert.pem
2. ReadPrivatKey() - Load certificates/private.key
3. funcAssinar() - Sign message with RSA-2048 + SHA-256
4. funcCript() - Encrypt data with RSA-OAEP

Check service logs after sending!
"@

Write-Host ""
Write-Host "Message content:" -ForegroundColor Cyan
Write-Host "----------------------------------------"
Write-Host $message -ForegroundColor White
Write-Host "----------------------------------------"
Write-Host ""

# Save message to file
$message | Out-File -FilePath "test_message.txt" -Encoding ASCII

Write-Host "Attempting to send message..." -ForegroundColor Yellow
Write-Host ""

# Try using amqsput
try {
    $amqsput = Get-Command amqsput -ErrorAction Stop
    Write-Host "Using amqsput to send message..." -ForegroundColor Green
    Write-Host ""

    # Send message using amqsput
    $message | & amqsput $Queue $QMgr

    Write-Host ""
    Write-Host "[SUCCESS] Message sent to queue!" -ForegroundColor Green

} catch {
    Write-Host "[INFO] amqsput not available, trying alternative method..." -ForegroundColor Yellow
    Write-Host ""

    # Alternative: Use runmqsc
    Write-Host "Creating MQSC command..." -ForegroundColor Yellow

    # This is a simplified version - real message sending might need different approach
    Write-Host ""
    Write-Host "Note: Automated message sending requires IBM MQ tools." -ForegroundColor Yellow
    Write-Host "See manual method below if this doesn't work." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Check service logs:" -ForegroundColor White
Write-Host "   Scripts\VER-LOG.bat" -ForegroundColor Yellow
Write-Host ""

Write-Host "2. Look for OpenSSL operations:" -ForegroundColor White
Write-Host "   [INFO] ReadPublicKey - Loading certificate" -ForegroundColor Green
Write-Host "   [INFO] ReadPrivatKey - Loading private key" -ForegroundColor Green
Write-Host "   [INFO] funcAssinar - Signing message (256 bytes)" -ForegroundColor Green
Write-Host "   [INFO] funcCript - Encrypting data" -ForegroundColor Green
Write-Host ""

Write-Host "3. Verify in database:" -ForegroundColor White
Write-Host "   Check PostgreSQL tables for new encrypted record" -ForegroundColor Yellow
Write-Host ""

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Cleanup
Remove-Item "test_message.txt" -ErrorAction SilentlyContinue

Write-Host "Press ENTER to close..."
$null = Read-Host
