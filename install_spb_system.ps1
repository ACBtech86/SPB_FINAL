# SPB System Installation Script
# ==============================================================================
# Installs complete SPB system on a clean Windows machine
# Requirements: Windows 10/11 Pro (64-bit), Administrator privileges
# ==============================================================================

#Requires -RunAsAdministrator

param(
    [string]$InstallDir = "C:\SPB",
    [string]$PostgreSQLVersion = "16",
    [string]$PythonVersion = "3.12.9",
    [string]$IBMMQVersion = "9.3.0.0",
    [switch]$SkipIBMMQ = $false,
    [switch]$SkipPostgreSQL = $false,
    [switch]$SkipPython = $false
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ==============================================================================
# Configuration
# ==============================================================================

$Config = @{
    InstallDir = $InstallDir
    PostgreSQL = @{
        Version = $PostgreSQLVersion
        Port = 5432
        SuperUser = "postgres"
        Password = "postgres"  # Change this!
        Databases = @("BCSPB", "BCSPBSTR", "BCSPB_TEST")
    }
    Python = @{
        Version = $PythonVersion
        URL = "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe"
    }
    IBMMQ = @{
        QueueManager = "QM.36266751.01"
        Queues = @(
            "QL.REQ.00038166.36266751.01",
            "QL.RES.00038166.36266751.01",
            "QL.REQ.00000000.36266751.01",
            "QL.RES.00000000.36266751.01",
            "QL.REQ.00038166.36266751.02",
            "QL.RES.00038166.36266751.02",
            "QL.REQ.SELIC.36266751.01",
            "QL.RES.SELIC.36266751.01"
        )
    }
    Git = @{
        Repository = "https://github.com/yourusername/novo_spb.git"  # Update this!
    }
}

# ==============================================================================
# Utility Functions
# ==============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n[STEP] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Yellow
}

function Test-CommandExists {
    param([string]$Command)
    try {
        if (Get-Command $Command -ErrorAction SilentlyContinue) {
            return $true
        }
    } catch {
        return $false
    }
    return $false
}

function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
    return $connection.TcpTestSucceeded
}

# ==============================================================================
# Installation Functions
# ==============================================================================

function Install-Chocolatey {
    Write-Step "Installing Chocolatey Package Manager"

    if (Test-CommandExists "choco") {
        Write-Success "Chocolatey already installed"
        return
    }

    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

    refreshenv
    Write-Success "Chocolatey installed"
}

function Install-Git {
    Write-Step "Installing Git"

    if (Test-CommandExists "git") {
        Write-Success "Git already installed"
        return
    }

    choco install git -y
    refreshenv
    Write-Success "Git installed"
}

function Install-Python {
    Write-Step "Installing Python $($Config.Python.Version) (64-bit)"

    if ($SkipPython) {
        Write-Info "Skipping Python installation"
        return
    }

    # Check if Python is already installed
    if (Test-CommandExists "py") {
        $pyVersion = & py --version 2>&1
        $pyArch = & py -c "import platform; print(platform.architecture()[0])" 2>&1

        if ($pyVersion -match "3.12" -and $pyArch -match "64bit") {
            Write-Success "Python 3.12 (64-bit) already installed: $pyVersion"
            return
        } else {
            Write-Info "Python found but wrong version or architecture: $pyVersion ($pyArch)"
        }
    }

    # Download Python installer
    $installerPath = "$env:TEMP\python-installer.exe"
    Write-Info "Downloading Python from $($Config.Python.URL)"
    Invoke-WebRequest -Uri $Config.Python.URL -OutFile $installerPath

    # Install Python
    Write-Info "Installing Python (this may take a few minutes)..."
    Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait

    Remove-Item $installerPath -Force
    refreshenv

    # Verify installation
    $pyVersion = & py --version 2>&1
    $pyArch = & py -c "import platform; print(platform.architecture()[0])" 2>&1

    if ($pyArch -match "64bit") {
        Write-Success "Python installed: $pyVersion ($pyArch)"
    } else {
        throw "Python installation failed: Architecture is $pyArch (expected 64bit)"
    }
}

function Install-PostgreSQL {
    Write-Step "Installing PostgreSQL $($Config.PostgreSQL.Version)"

    if ($SkipPostgreSQL) {
        Write-Info "Skipping PostgreSQL installation"
        return
    }

    # Check if PostgreSQL is already installed
    if (Test-Port -Port $Config.PostgreSQL.Port) {
        Write-Success "PostgreSQL already running on port $($Config.PostgreSQL.Port)"
        return
    }

    # Install using Chocolatey
    choco install postgresql$($Config.PostgreSQL.Version) --params "/Password:$($Config.PostgreSQL.Password)" -y
    refreshenv

    # Wait for PostgreSQL to start
    Write-Info "Waiting for PostgreSQL to start..."
    Start-Sleep -Seconds 10

    # Verify installation
    if (Test-Port -Port $Config.PostgreSQL.Port) {
        Write-Success "PostgreSQL installed and running"
    } else {
        throw "PostgreSQL installation failed: Service not responding on port $($Config.PostgreSQL.Port)"
    }
}

function Setup-PostgreSQLDatabases {
    Write-Step "Setting up PostgreSQL databases"

    $env:PGPASSWORD = $Config.PostgreSQL.Password
    $psqlPath = "C:\Program Files\PostgreSQL\$($Config.PostgreSQL.Version)\bin\psql.exe"

    if (-not (Test-Path $psqlPath)) {
        Write-Info "Searching for psql.exe..."
        $psqlPath = (Get-ChildItem "C:\Program Files\PostgreSQL" -Recurse -Filter "psql.exe" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
    }

    if (-not $psqlPath) {
        throw "psql.exe not found. Please install PostgreSQL manually."
    }

    foreach ($dbName in $Config.PostgreSQL.Databases) {
        Write-Info "Creating database: $dbName"

        # Check if database exists
        $checkDb = & $psqlPath -U $Config.PostgreSQL.SuperUser -h localhost -p $Config.PostgreSQL.Port -t -c "SELECT 1 FROM pg_database WHERE datname='$dbName'" 2>&1

        if ($checkDb -match "1") {
            Write-Success "Database $dbName already exists"
        } else {
            # Create database
            & $psqlPath -U $Config.PostgreSQL.SuperUser -h localhost -p $Config.PostgreSQL.Port -c "CREATE DATABASE `"$dbName`";" 2>&1
            Write-Success "Database $dbName created"
        }
    }

    Remove-Item Env:\PGPASSWORD
}

function Install-IBMMQ {
    Write-Step "Installing IBM MQ"

    if ($SkipIBMMQ) {
        Write-Info "Skipping IBM MQ installation"
        return
    }

    Write-Info "IBM MQ requires manual installation:"
    Write-Info "1. Download IBM MQ $($Config.IBMMQ.Version) from IBM website"
    Write-Info "2. Run the installer with default options"
    Write-Info "3. Install as Windows service"
    Write-Info "4. After installation, run this script again to configure queues"
    Write-Info ""
    Write-Info "IBM MQ Download: https://www.ibm.com/products/mq/advanced"

    # Check if IBM MQ is installed
    if (Test-CommandExists "dspmq") {
        Write-Success "IBM MQ is already installed"
        return
    }

    throw "IBM MQ not found. Please install manually and run this script again."
}

function Setup-IBMMQQueues {
    Write-Step "Setting up IBM MQ queues"

    if (-not (Test-CommandExists "dspmq")) {
        Write-Info "IBM MQ not installed, skipping queue setup"
        return
    }

    # Check if queue manager exists
    $qmExists = & dspmq 2>&1 | Select-String -Pattern $Config.IBMMQ.QueueManager -Quiet

    if (-not $qmExists) {
        Write-Info "Creating queue manager: $($Config.IBMMQ.QueueManager)"
        & crtmqm $Config.IBMMQ.QueueManager
    }

    # Start queue manager
    Write-Info "Starting queue manager..."
    & strmqm $Config.IBMMQ.QueueManager
    Start-Sleep -Seconds 5

    # Create queues using MQSC commands
    $mqscCommands = @"
* Define local queues for SPB system
$(foreach ($queue in $Config.IBMMQ.Queues) { "DEFINE QLOCAL('$queue') REPLACE" })

* Set queue manager properties
ALTER QMGR CHLAUTH(DISABLED)
REFRESH SECURITY TYPE(CONNAUTH)

* End
END
"@

    $mqscFile = "$env:TEMP\spb_queues.mqsc"
    $mqscCommands | Out-File -FilePath $mqscFile -Encoding ASCII

    Write-Info "Creating queues..."
    & runmqsc $Config.IBMMQ.QueueManager < $mqscFile

    Remove-Item $mqscFile -Force
    Write-Success "IBM MQ queues configured"
}

function Clone-Repository {
    Write-Step "Cloning SPB repository"

    if (Test-Path "$($Config.InstallDir)\.git") {
        Write-Success "Repository already cloned"
        return
    }

    if (-not (Test-Path $Config.InstallDir)) {
        New-Item -ItemType Directory -Path $Config.InstallDir -Force | Out-Null
    }

    Write-Info "Cloning from $($Config.Git.Repository)"
    Write-Info "Note: Update the repository URL in the script configuration!"

    Push-Location $Config.InstallDir
    git clone $Config.Git.Repository .
    Pop-Location

    Write-Success "Repository cloned to $($Config.InstallDir)"
}

function Install-PythonDependencies {
    Write-Step "Installing Python dependencies"

    $projects = @(
        @{Name="SPBSite"; Path="spbsite"; RequirementsFile="requirements.txt"},
        @{Name="spb-shared"; Path="spb-shared"; RequirementsFile="requirements.txt"},
        @{Name="BCSrvSqlMq"; Path="BCSrvSqlMq"; RequirementsFile="requirements.txt"}
    )

    foreach ($project in $projects) {
        $projectPath = Join-Path $Config.InstallDir $project.Path
        $reqFile = Join-Path $projectPath $project.RequirementsFile

        if (-not (Test-Path $reqFile)) {
            Write-Info "Requirements file not found for $($project.Name), skipping"
            continue
        }

        Write-Info "Installing dependencies for $($project.Name)..."
        Push-Location $projectPath

        & py -m pip install --upgrade pip
        & py -m pip install -r $project.RequirementsFile

        Pop-Location
        Write-Success "$($project.Name) dependencies installed"
    }

    # Install spb-shared as editable package
    Write-Info "Installing spb-shared as editable package..."
    Push-Location (Join-Path $Config.InstallDir "spb-shared")
    & py -m pip install -e .
    Pop-Location
    Write-Success "spb-shared installed as editable package"
}

function Setup-DatabaseSchema {
    Write-Step "Setting up database schema"

    $spbSharedPath = Join-Path $Config.InstallDir "spb-shared"

    if (-not (Test-Path $spbSharedPath)) {
        Write-Info "spb-shared not found, skipping schema setup"
        return
    }

    Write-Info "Creating database tables..."
    Write-Info "Note: This requires Alembic migrations or SQLAlchemy create_all()"
    Write-Info "Run manually: cd spb-shared && py -c 'from spb_shared.models import create_tables; import asyncio; asyncio.run(create_tables())'"

    # Note: This would need to be implemented in spb-shared
    Write-Success "Database schema setup instructions provided"
}

function Create-EnvironmentFile {
    Write-Step "Creating environment configuration"

    $envContent = @"
# SPB System Environment Configuration
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:$($Config.PostgreSQL.Password)@localhost:$($Config.PostgreSQL.Port)/BCSPB
DATABASE_URL_STR=postgresql+asyncpg://postgres:$($Config.PostgreSQL.Password)@localhost:$($Config.PostgreSQL.Port)/BCSPBSTR
DATABASE_URL_TEST=postgresql+asyncpg://postgres:$($Config.PostgreSQL.Password)@localhost:$($Config.PostgreSQL.Port)/BCSPB_TEST

# IBM MQ Configuration
MQ_QUEUE_MANAGER=$($Config.IBMMQ.QueueManager)
MQ_CHANNEL=SYSTEM.DEF.SVRCONN
MQ_HOST=localhost
MQ_PORT=1414

# Application Configuration
SECRET_KEY=$(New-Guid)
DEBUG=false
LOG_LEVEL=INFO

# ISPB Configuration
ISPB_FINVEST=36266751
ISPB_BACEN=00038166
"@

    $envFile = Join-Path $Config.InstallDir ".env"
    $envContent | Out-File -FilePath $envFile -Encoding UTF8

    Write-Success "Environment file created: $envFile"
    Write-Info "Please review and update the .env file with your specific configuration"
}

function Test-Installation {
    Write-Step "Testing installation"

    $tests = @{
        "Python 64-bit" = { (& py -c "import platform; print(platform.architecture()[0])" 2>&1) -match "64bit" }
        "PostgreSQL" = { Test-Port -Port $Config.PostgreSQL.Port }
        "Git" = { Test-CommandExists "git" }
        "Repository" = { Test-Path "$($Config.InstallDir)\.git" }
    }

    $allPassed = $true

    foreach ($test in $tests.GetEnumerator()) {
        $result = & $test.Value
        if ($result) {
            Write-Success "$($test.Key): PASS"
        } else {
            Write-Error "$($test.Key): FAIL"
            $allPassed = $false
        }
    }

    # Test Python packages
    Write-Info "Testing Python packages..."
    $packages = @("fastapi", "sqlalchemy", "asyncpg", "pytest")

    foreach ($package in $packages) {
        $installed = & py -c "import $package; print($package.__version__)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  $package: $installed"
        } else {
            Write-Info "  $package: Not installed"
        }
    }

    return $allPassed
}

function Show-NextSteps {
    Write-Host "`n" -NoNewline
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Installation Complete!" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Review and update configuration:" -ForegroundColor White
    Write-Host "   - Edit $($Config.InstallDir)\.env" -ForegroundColor Gray
    Write-Host "   - Update database passwords" -ForegroundColor Gray
    Write-Host "   - Configure ISPB codes" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Initialize databases:" -ForegroundColor White
    Write-Host "   cd $($Config.InstallDir)\spb-shared" -ForegroundColor Gray
    Write-Host "   py -c `"from spb_shared.models import create_tables; import asyncio; asyncio.run(create_tables())`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Load initial data (optional):" -ForegroundColor White
    Write-Host "   cd $($Config.InstallDir)\Carga_Mensageria" -ForegroundColor Gray
    Write-Host "   py carga_mensageria.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Run tests:" -ForegroundColor White
    Write-Host "   cd $($Config.InstallDir)\spbsite" -ForegroundColor Gray
    Write-Host "   py -m pytest -v" -ForegroundColor Gray
    Write-Host ""
    Write-Host "5. Start the application:" -ForegroundColor White
    Write-Host "   cd $($Config.InstallDir)\spbsite" -ForegroundColor Gray
    Write-Host "   py -m uvicorn app.main:app --reload --port 8000" -ForegroundColor Gray
    Write-Host ""
    Write-Host "6. Start the backend service:" -ForegroundColor White
    Write-Host "   cd $($Config.InstallDir)\BCSrvSqlMq" -ForegroundColor Gray
    Write-Host "   py main.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Documentation:" -ForegroundColor Yellow
    Write-Host "  - Project Overview: $($Config.InstallDir)\PROJECTS_OVERVIEW.md" -ForegroundColor Gray
    Write-Host "  - PostgreSQL Setup: $($Config.InstallDir)\POSTGRESQL_SETUP.md" -ForegroundColor Gray
    Write-Host "  - IBM MQ Setup: $($Config.InstallDir)\IBM_MQ_SETUP.md" -ForegroundColor Gray
    Write-Host "  - Architecture: $($Config.InstallDir)\ARCHITECTURE_VERIFICATION.md" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Access the application at: http://localhost:8000" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
}

# ==============================================================================
# Main Installation Process
# ==============================================================================

function Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "SPB System Installation Script" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Installation Directory: $($Config.InstallDir)" -ForegroundColor Yellow
    Write-Host "Python Version: $($Config.Python.Version)" -ForegroundColor Yellow
    Write-Host "PostgreSQL Version: $($Config.PostgreSQL.Version)" -ForegroundColor Yellow
    Write-Host ""

    try {
        # Core prerequisites
        Install-Chocolatey
        Install-Git
        Install-Python

        # Database
        if (-not $SkipPostgreSQL) {
            Install-PostgreSQL
            Setup-PostgreSQLDatabases
        }

        # IBM MQ
        if (-not $SkipIBMMQ) {
            Install-IBMMQ
            Setup-IBMMQQueues
        }

        # Application
        Clone-Repository
        Install-PythonDependencies
        Create-EnvironmentFile

        # Verification
        $testsPassed = Test-Installation

        if ($testsPassed) {
            Show-NextSteps
        } else {
            Write-Error "Installation completed with errors. Please review the output above."
        }

    } catch {
        Write-Error "Installation failed: $_"
        Write-Host $_.ScriptStackTrace -ForegroundColor Red
        exit 1
    }
}

# Run main installation
Main
