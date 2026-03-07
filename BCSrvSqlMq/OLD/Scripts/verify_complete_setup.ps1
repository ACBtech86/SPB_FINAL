# Complete BCSrvSqlMq Setup Verification
# This script verifies all components are ready

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BCSrvSqlMq - Complete Setup Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# 1. Check PostgreSQL Service
Write-Host "1. PostgreSQL Service..." -NoNewline
$pgService = Get-Service postgresql-x64-18 -ErrorAction SilentlyContinue
if ($pgService -and $pgService.Status -eq 'Running') {
    Write-Host " ✅ Running" -ForegroundColor Green
} else {
    Write-Host " ❌ Not Running" -ForegroundColor Red
    $allGood = $false
}

# 2. Check IBM MQ Queue Manager
Write-Host "2. IBM MQ Queue Manager..." -NoNewline
$qmStatus = & dspmq 2>$null | Select-String "QM.61377677.01.*Running"
if ($qmStatus) {
    Write-Host " ✅ Running" -ForegroundColor Green
} else {
    Write-Host " ❌ Not Running" -ForegroundColor Red
    $allGood = $false
}

# 3. Check psqlODBC 32-bit Driver
Write-Host "3. psqlODBC 32-bit Driver..." -NoNewline
$driver = Test-Path "C:\Program Files (x86)\psqlODBC\1600\bin\psqlodbc35w.dll"
if ($driver) {
    Write-Host " ✅ Installed" -ForegroundColor Green
} else {
    Write-Host " ❌ Not Found" -ForegroundColor Red
    $allGood = $false
}

# 4. Check BCSrvSqlMq.exe
Write-Host "4. BCSrvSqlMq.exe..." -NoNewline
$exe = Test-Path "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release\BCSrvSqlMq.exe"
if ($exe) {
    $fileInfo = Get-Item "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release\BCSrvSqlMq.exe"
    Write-Host " ✅ Found ($([math]::Round($fileInfo.Length/1KB)) KB)" -ForegroundColor Green
} else {
    Write-Host " ❌ Not Found" -ForegroundColor Red
    $allGood = $false
}

# 5. Check CL32.dll
Write-Host "5. CL32.dll (CryptLib)..." -NoNewline
$cl32 = Test-Path "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\build\Release\CL32.dll"
if ($cl32) {
    Write-Host " ✅ Found" -ForegroundColor Green
} else {
    Write-Host " ❌ Not Found" -ForegroundColor Red
    $allGood = $false
}

# 6. Check BCSrvSqlMq.ini
Write-Host "6. BCSrvSqlMq.ini..." -NoNewline
$ini = Test-Path "c:\Users\AntonioBosco\OneDrive - Finvest\Documentos\BCSrvSqlMq\BCSrvSqlMq.ini"
if ($ini) {
    Write-Host " ✅ Found" -ForegroundColor Green
} else {
    Write-Host " ❌ Not Found" -ForegroundColor Red
    $allGood = $false
}

# 7. Test Database Connection
Write-Host "7. Database Connection..." -NoNewline
try {
    $connString = "DRIVER={PostgreSQL Unicode};SERVER=localhost;PORT=5432;DATABASE=bcspbstr;UID=postgres;PWD=Rama1248;"
    $conn = New-Object System.Data.Odbc.OdbcConnection($connString)
    $conn.Open()
    $conn.Close()
    Write-Host " ✅ Connected" -ForegroundColor Green
} catch {
    Write-Host " ❌ Failed" -ForegroundColor Red
    $allGood = $false
}

# 8. Check Database Tables
Write-Host "8. Database Tables..." -NoNewline
try {
    $connString = "DRIVER={PostgreSQL Unicode};SERVER=localhost;PORT=5432;DATABASE=bcspbstr;UID=postgres;PWD=Rama1248;"
    $conn = New-Object System.Data.Odbc.OdbcConnection($connString)
    $conn.Open()

    $expectedTables = @('spb_log_bacen', 'spb_bacen_to_local', 'spb_local_to_bacen', 'spb_controle')
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
    $reader = $cmd.ExecuteReader()

    $foundTables = @()
    while ($reader.Read()) {
        $foundTables += $reader[0]
    }

    $reader.Close()
    $conn.Close()

    $missingTables = $expectedTables | Where-Object { $foundTables -notcontains $_ }
    if ($missingTables.Count -eq 0) {
        Write-Host " ✅ All 4 tables exist" -ForegroundColor Green
    } else {
        Write-Host " ❌ Missing: $($missingTables -join ', ')" -ForegroundColor Red
        $allGood = $false
    }
} catch {
    Write-Host " ❌ Error checking tables" -ForegroundColor Red
    $allGood = $false
}

# 9. Check Working Directories
Write-Host "9. Working Directories..." -NoNewline
$dirs = @(
    "C:\BCSrvSqlMq\Traces",
    "C:\BCSrvSqlMq\AuditFiles"
)
$missingDirs = $dirs | Where-Object { !(Test-Path $_) }
if ($missingDirs.Count -eq 0) {
    Write-Host " ✅ All exist" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Creating..." -ForegroundColor Yellow
    foreach ($dir in $missingDirs) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }
    Write-Host "   ✅ Created" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "✅ ALL SYSTEMS READY!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can now:" -ForegroundColor White
    Write-Host "  1. Test run: cd build\Release && .\BCSrvSqlMq.exe" -ForegroundColor White
    Write-Host "  2. View logs: type C:\BCSrvSqlMq\Traces\*.log" -ForegroundColor White
    Write-Host "  3. Install service: .\BCSrvSqlMq.exe -install" -ForegroundColor White
} else {
    Write-Host "⚠️  SOME ISSUES DETECTED" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please fix the issues marked with ❌ above" -ForegroundColor Yellow
}

Write-Host ""
