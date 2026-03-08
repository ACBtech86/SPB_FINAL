#!/bin/bash
# SPB System Installation Script for Linux
# ==============================================================================
# Installs complete SPB system on a clean Linux machine
# Requirements: Ubuntu 20.04+ / Debian 11+ / RHEL 8+ (64-bit), sudo privileges
# ==============================================================================

set -e  # Exit on error

# ==============================================================================
# Configuration
# ==============================================================================

INSTALL_DIR="${INSTALL_DIR:-/opt/spb}"
POSTGRESQL_VERSION="${POSTGRESQL_VERSION:-16}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
IBMMQ_VERSION="${IBMMQ_VERSION:-9.3.0.0}"

POSTGRESQL_PORT="5432"
POSTGRESQL_USER="postgres"
POSTGRESQL_PASSWORD="postgres"  # Change this!
POSTGRESQL_DATABASES=("BCSPB" "BCSPBSTR" "BCSPB_TEST")

IBM_MQ_QUEUE_MANAGER="QM.36266751.01"
IBM_MQ_QUEUES=(
    "QL.REQ.00038166.36266751.01"
    "QL.RES.00038166.36266751.01"
    "QL.REQ.00000000.36266751.01"
    "QL.RES.00000000.36266751.01"
    "QL.REQ.00038166.36266751.02"
    "QL.RES.00038166.36266751.02"
    "QL.REQ.SELIC.36266751.01"
    "QL.RES.SELIC.36266751.01"
)

GIT_REPOSITORY="https://github.com/yourusername/novo_spb.git"  # Update this!

SKIP_IBMMQ=false
SKIP_POSTGRESQL=false
SKIP_PYTHON=false

# ==============================================================================
# Utility Functions
# ==============================================================================

print_step() {
    echo ""
    echo -e "\e[36m[STEP] $1\e[0m"
}

print_success() {
    echo -e "\e[32m[OK] $1\e[0m"
}

print_error() {
    echo -e "\e[31m[ERROR] $1\e[0m"
}

print_info() {
    echo -e "\e[33m[INFO] $1\e[0m"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        OS="unknown"
    fi
    echo "$OS"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# ==============================================================================
# Installation Functions
# ==============================================================================

install_system_packages() {
    print_step "Installing system packages"

    OS=$(detect_os)

    case "$OS" in
        ubuntu|debian)
            apt-get update
            apt-get install -y \
                build-essential \
                libssl-dev \
                libffi-dev \
                python3-dev \
                git \
                curl \
                wget \
                gnupg2 \
                lsb-release \
                software-properties-common
            print_success "System packages installed (Debian/Ubuntu)"
            ;;
        rhel|centos|fedora)
            yum update -y
            yum install -y \
                gcc \
                gcc-c++ \
                make \
                openssl-devel \
                libffi-devel \
                python3-devel \
                git \
                curl \
                wget
            print_success "System packages installed (RHEL/CentOS)"
            ;;
        *)
            print_error "Unsupported OS: $OS"
            exit 1
            ;;
    esac
}

install_python() {
    print_step "Installing Python $PYTHON_VERSION (64-bit)"

    if $SKIP_PYTHON; then
        print_info "Skipping Python installation"
        return
    fi

    if command_exists python3; then
        PY_VERSION=$(python3 --version 2>&1)
        PY_ARCH=$(python3 -c "import platform; print(platform.architecture()[0])" 2>&1)

        if [[ $PY_VERSION == *"3.12"* ]] && [[ $PY_ARCH == "64bit" ]]; then
            print_success "Python 3.12 (64-bit) already installed: $PY_VERSION"
            return
        fi
    fi

    OS=$(detect_os)

    case "$OS" in
        ubuntu|debian)
            add-apt-repository -y ppa:deadsnakes/ppa
            apt-get update
            apt-get install -y python3.12 python3.12-venv python3.12-dev python3-pip
            update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
            ;;
        rhel|centos|fedora)
            yum install -y python3.12 python3.12-devel python3-pip
            ;;
        *)
            print_error "Unsupported OS for Python installation: $OS"
            exit 1
            ;;
    esac

    # Verify installation
    PY_VERSION=$(python3 --version 2>&1)
    PY_ARCH=$(python3 -c "import platform; print(platform.architecture()[0])" 2>&1)

    if [[ $PY_ARCH == "64bit" ]]; then
        print_success "Python installed: $PY_VERSION ($PY_ARCH)"
    else
        print_error "Python installation failed: Architecture is $PY_ARCH (expected 64bit)"
        exit 1
    fi

    # Upgrade pip
    python3 -m pip install --upgrade pip
}

install_postgresql() {
    print_step "Installing PostgreSQL $POSTGRESQL_VERSION"

    if $SKIP_POSTGRESQL; then
        print_info "Skipping PostgreSQL installation"
        return
    fi

    if command_exists psql; then
        print_success "PostgreSQL already installed"
        return
    fi

    OS=$(detect_os)

    case "$OS" in
        ubuntu|debian)
            # Add PostgreSQL APT repository
            sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
            wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
            apt-get update
            apt-get install -y postgresql-$POSTGRESQL_VERSION postgresql-contrib-$POSTGRESQL_VERSION
            ;;
        rhel|centos|fedora)
            dnf install -y postgresql$POSTGRESQL_VERSION-server postgresql$POSTGRESQL_VERSION-contrib
            postgresql-setup --initdb
            ;;
        *)
            print_error "Unsupported OS for PostgreSQL installation: $OS"
            exit 1
            ;;
    esac

    # Start and enable PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql

    print_success "PostgreSQL installed and running"
}

setup_postgresql_databases() {
    print_step "Setting up PostgreSQL databases"

    # Set postgres user password
    sudo -u postgres psql -c "ALTER USER postgres PASSWORD '$POSTGRESQL_PASSWORD';"

    # Create databases
    for db in "${POSTGRESQL_DATABASES[@]}"; do
        print_info "Creating database: $db"

        # Check if database exists
        DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$db'")

        if [ "$DB_EXISTS" = "1" ]; then
            print_success "Database $db already exists"
        else
            sudo -u postgres psql -c "CREATE DATABASE \"$db\";"
            print_success "Database $db created"
        fi
    done

    # Configure PostgreSQL for remote connections (optional)
    PG_HBA="/etc/postgresql/$POSTGRESQL_VERSION/main/pg_hba.conf"
    if [ -f "$PG_HBA" ]; then
        # Backup original
        cp "$PG_HBA" "$PG_HBA.backup"

        # Allow local connections with password
        echo "host    all             all             127.0.0.1/32            md5" >> "$PG_HBA"
        echo "host    all             all             ::1/128                 md5" >> "$PG_HBA"

        systemctl restart postgresql
        print_success "PostgreSQL configured for local connections"
    fi
}

install_ibmmq() {
    print_step "Installing IBM MQ"

    if $SKIP_IBMMQ; then
        print_info "Skipping IBM MQ installation"
        return
    fi

    print_info "IBM MQ requires manual installation:"
    print_info "1. Download IBM MQ $IBMMQ_VERSION from IBM website"
    print_info "2. Extract the archive"
    print_info "3. Run ./mqlicense.sh to accept license"
    print_info "4. Run rpm -ivh MQSeries*.rpm (RHEL) or dpkg -i MQSeries*.deb (Ubuntu)"
    print_info "5. After installation, run this script again to configure queues"
    print_info ""
    print_info "IBM MQ Download: https://www.ibm.com/products/mq/advanced"

    if command_exists dspmq; then
        print_success "IBM MQ is already installed"
        return
    fi

    print_error "IBM MQ not found. Please install manually and run this script again."
    exit 1
}

setup_ibmmq_queues() {
    print_step "Setting up IBM MQ queues"

    if ! command_exists dspmq; then
        print_info "IBM MQ not installed, skipping queue setup"
        return
    fi

    # Check if queue manager exists
    if dspmq | grep -q "$IBM_MQ_QUEUE_MANAGER"; then
        print_info "Queue manager $IBM_MQ_QUEUE_MANAGER already exists"
    else
        print_info "Creating queue manager: $IBM_MQ_QUEUE_MANAGER"
        crtmqm "$IBM_MQ_QUEUE_MANAGER"
    fi

    # Start queue manager
    print_info "Starting queue manager..."
    strmqm "$IBM_MQ_QUEUE_MANAGER"
    sleep 5

    # Create MQSC commands file
    MQSC_FILE="/tmp/spb_queues.mqsc"
    cat > "$MQSC_FILE" <<EOF
* Define local queues for SPB system
$(for queue in "${IBM_MQ_QUEUES[@]}"; do echo "DEFINE QLOCAL('$queue') REPLACE"; done)

* Set queue manager properties
ALTER QMGR CHLAUTH(DISABLED)
REFRESH SECURITY TYPE(CONNAUTH)

* End
END
EOF

    print_info "Creating queues..."
    runmqsc "$IBM_MQ_QUEUE_MANAGER" < "$MQSC_FILE"

    rm -f "$MQSC_FILE"
    print_success "IBM MQ queues configured"
}

clone_repository() {
    print_step "Cloning SPB repository"

    if [ -d "$INSTALL_DIR/.git" ]; then
        print_success "Repository already cloned"
        return
    fi

    mkdir -p "$INSTALL_DIR"

    print_info "Cloning from $GIT_REPOSITORY"
    print_info "Note: Update the repository URL in the script configuration!"

    git clone "$GIT_REPOSITORY" "$INSTALL_DIR"

    print_success "Repository cloned to $INSTALL_DIR"
}

install_python_dependencies() {
    print_step "Installing Python dependencies"

    PROJECTS=(
        "spbsite:requirements.txt"
        "spb-shared:requirements.txt"
        "BCSrvSqlMq:requirements.txt"
    )

    for project_info in "${PROJECTS[@]}"; do
        IFS=':' read -r project_name req_file <<< "$project_info"
        project_path="$INSTALL_DIR/$project_name"
        req_path="$project_path/$req_file"

        if [ ! -f "$req_path" ]; then
            print_info "Requirements file not found for $project_name, skipping"
            continue
        fi

        print_info "Installing dependencies for $project_name..."
        cd "$project_path"
        python3 -m pip install -r "$req_file"
        print_success "$project_name dependencies installed"
    done

    # Install spb-shared as editable package
    print_info "Installing spb-shared as editable package..."
    cd "$INSTALL_DIR/spb-shared"
    python3 -m pip install -e .
    print_success "spb-shared installed as editable package"
}

create_environment_file() {
    print_step "Creating environment configuration"

    ENV_FILE="$INSTALL_DIR/.env"

    cat > "$ENV_FILE" <<EOF
# SPB System Environment Configuration
# Generated: $(date '+%Y-%m-%d %H:%M:%S')

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:$POSTGRESQL_PASSWORD@localhost:$POSTGRESQL_PORT/BCSPB
DATABASE_URL_STR=postgresql+asyncpg://postgres:$POSTGRESQL_PASSWORD@localhost:$POSTGRESQL_PORT/BCSPBSTR
DATABASE_URL_TEST=postgresql+asyncpg://postgres:$POSTGRESQL_PASSWORD@localhost:$POSTGRESQL_PORT/BCSPB_TEST

# IBM MQ Configuration
MQ_QUEUE_MANAGER=$IBM_MQ_QUEUE_MANAGER
MQ_CHANNEL=SYSTEM.DEF.SVRCONN
MQ_HOST=localhost
MQ_PORT=1414

# Application Configuration
SECRET_KEY=$(uuidgen)
DEBUG=false
LOG_LEVEL=INFO

# ISPB Configuration
ISPB_FINVEST=36266751
ISPB_BACEN=00038166
EOF

    chmod 600 "$ENV_FILE"
    print_success "Environment file created: $ENV_FILE"
    print_info "Please review and update the .env file with your specific configuration"
}

create_systemd_services() {
    print_step "Creating systemd services"

    # SPBSite service
    cat > /etc/systemd/system/spbsite.service <<EOF
[Unit]
Description=SPB Site Web Application
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/spbsite
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # BCSrvSqlMq service
    cat > /etc/systemd/system/bcsrvsqlmq.service <<EOF
[Unit]
Description=BC SQL MQ Backend Service
After=network.target postgresql.service ibmmq.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/BCSrvSqlMq
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    print_success "Systemd services created"
    print_info "Enable with: systemctl enable spbsite bcsrvsqlmq"
    print_info "Start with: systemctl start spbsite bcsrvsqlmq"
}

test_installation() {
    print_step "Testing installation"

    ALL_PASSED=true

    # Test Python
    if python3 -c "import platform; assert platform.architecture()[0] == '64bit'" 2>/dev/null; then
        print_success "Python 64-bit: PASS"
    else
        print_error "Python 64-bit: FAIL"
        ALL_PASSED=false
    fi

    # Test PostgreSQL
    if systemctl is-active --quiet postgresql; then
        print_success "PostgreSQL: PASS"
    else
        print_error "PostgreSQL: FAIL"
        ALL_PASSED=false
    fi

    # Test Git
    if command_exists git; then
        print_success "Git: PASS"
    else
        print_error "Git: FAIL"
        ALL_PASSED=false
    fi

    # Test Repository
    if [ -d "$INSTALL_DIR/.git" ]; then
        print_success "Repository: PASS"
    else
        print_error "Repository: FAIL"
        ALL_PASSED=false
    fi

    # Test Python packages
    print_info "Testing Python packages..."
    PACKAGES=("fastapi" "sqlalchemy" "asyncpg" "pytest")

    for package in "${PACKAGES[@]}"; do
        if python3 -c "import $package; print(f'  $package: {$package.__version__}')" 2>/dev/null; then
            print_success "  $package: installed"
        else
            print_info "  $package: Not installed"
        fi
    done

    return $ALL_PASSED
}

show_next_steps() {
    echo ""
    echo "================================================================================"
    echo -e "\e[32mInstallation Complete!\e[0m"
    echo "================================================================================"
    echo ""
    echo -e "\e[33mNext Steps:\e[0m"
    echo ""
    echo -e "\e[37m1. Review and update configuration:\e[0m"
    echo -e "   \e[90m- Edit $INSTALL_DIR/.env\e[0m"
    echo -e "   \e[90m- Update database passwords\e[0m"
    echo -e "   \e[90m- Configure ISPB codes\e[0m"
    echo ""
    echo -e "\e[37m2. Initialize databases:\e[0m"
    echo -e "   \e[90mcd $INSTALL_DIR/spb-shared\e[0m"
    echo -e "   \e[90mpython3 -c \"from spb_shared.models import create_tables; import asyncio; asyncio.run(create_tables())\"\e[0m"
    echo ""
    echo -e "\e[37m3. Load initial data (optional):\e[0m"
    echo -e "   \e[90mcd $INSTALL_DIR/Carga_Mensageria\e[0m"
    echo -e "   \e[90mpython3 carga_mensageria.py\e[0m"
    echo ""
    echo -e "\e[37m4. Run tests:\e[0m"
    echo -e "   \e[90mcd $INSTALL_DIR/spbsite\e[0m"
    echo -e "   \e[90mpython3 -m pytest -v\e[0m"
    echo ""
    echo -e "\e[37m5. Start services:\e[0m"
    echo -e "   \e[90msudo systemctl enable spbsite bcsrvsqlmq\e[0m"
    echo -e "   \e[90msudo systemctl start spbsite bcsrvsqlmq\e[0m"
    echo ""
    echo -e "\e[33mDocumentation:\e[0m"
    echo -e "  \e[90m- Project Overview: $INSTALL_DIR/PROJECTS_OVERVIEW.md\e[0m"
    echo -e "  \e[90m- PostgreSQL Setup: $INSTALL_DIR/POSTGRESQL_SETUP.md\e[0m"
    echo -e "  \e[90m- IBM MQ Setup: $INSTALL_DIR/IBM_MQ_SETUP.md\e[0m"
    echo -e "  \e[90m- Architecture: $INSTALL_DIR/ARCHITECTURE_VERIFICATION.md\e[0m"
    echo ""
    echo -e "\e[32mAccess the application at: http://localhost:8000\e[0m"
    echo "================================================================================"
    echo ""
}

# ==============================================================================
# Main Installation Process
# ==============================================================================

main() {
    echo ""
    echo "================================================================================"
    echo -e "\e[32mSPB System Installation Script\e[0m"
    echo "================================================================================"
    echo ""
    echo -e "\e[33mInstallation Directory: $INSTALL_DIR\e[0m"
    echo -e "\e[33mPython Version: $PYTHON_VERSION\e[0m"
    echo -e "\e[33mPostgreSQL Version: $POSTGRESQL_VERSION\e[0m"
    echo ""

    # Check root privileges
    check_root

    # Install components
    install_system_packages
    install_python

    if ! $SKIP_POSTGRESQL; then
        install_postgresql
        setup_postgresql_databases
    fi

    if ! $SKIP_IBMMQ; then
        install_ibmmq
        setup_ibmmq_queues
    fi

    clone_repository
    install_python_dependencies
    create_environment_file
    create_systemd_services

    # Test installation
    if test_installation; then
        show_next_steps
    else
        print_error "Installation completed with errors. Please review the output above."
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --skip-ibmmq)
            SKIP_IBMMQ=true
            shift
            ;;
        --skip-postgresql)
            SKIP_POSTGRESQL=true
            shift
            ;;
        --skip-python)
            SKIP_PYTHON=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --install-dir DIR      Installation directory (default: /opt/spb)"
            echo "  --skip-ibmmq           Skip IBM MQ installation"
            echo "  --skip-postgresql      Skip PostgreSQL installation"
            echo "  --skip-python          Skip Python installation"
            echo "  --help                 Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main installation
main
