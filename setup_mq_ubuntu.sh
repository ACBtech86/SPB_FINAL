#!/bin/bash
# =============================================================================
# IBM MQ Setup Script for Ubuntu — FINVEST ISPB 36266751
# Queue Manager: QM.36266751.01
# =============================================================================
set -euo pipefail

MQ_BIN="/opt/mqm/bin"
QM="QM.36266751.01"
MQSC_FILE="/tmp/finvest_queues_$$.mqsc"

# Colours
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }
step() { echo -e "\n${YELLOW}[$1]${NC} $2"; }

echo "========================================================"
echo " IBM MQ Setup for FINVEST (ISPB 36266751) — Ubuntu"
echo "========================================================"

# --- Check IBM MQ is installed ---
step "1/6" "Checking IBM MQ installation"
if [ ! -f "$MQ_BIN/crtmqm" ]; then
    fail "IBM MQ not found at $MQ_BIN. Run the install steps first."
fi
ok "IBM MQ found at $MQ_BIN"

# --- Load MQ environment ---
step "2/6" "Loading MQ environment"
# Note: do not source setmqenv — it calls exit() internally and kills the shell.
# Set the required variables directly instead.
export PATH="/opt/mqm/bin:/opt/mqm/samp/bin:$PATH"
export LD_LIBRARY_PATH="/opt/mqm/lib64:/opt/mqm/lib:${LD_LIBRARY_PATH:-}"
ok "MQ environment set (PATH + LD_LIBRARY_PATH)"

# Check user is in mqm group
if ! id -nG "$USER" | grep -qw mqm; then
    warn "User '$USER' is not in the mqm group."
    warn "Run: sudo usermod -aG mqm \$USER  then log out and back in."
    warn "Continuing as current user — some commands may fail."
fi

# --- Handle existing queue manager ---
step "3/6" "Checking for existing queue manager $QM"
if "$MQ_BIN/dspmq" 2>/dev/null | grep -q "$QM"; then
    warn "Queue manager $QM already exists."
    echo -n "  Delete and recreate it? [y/N]: "
    read -r ANSWER
    if [[ "${ANSWER,,}" == "y" ]]; then
        echo "  Stopping and deleting $QM..."
        "$MQ_BIN/endmqm" -i "$QM" 2>/dev/null || true
        sleep 3
        "$MQ_BIN/dltmqm" "$QM"
        ok "Deleted $QM"
    else
        ok "Keeping existing queue manager — skipping creation."
        SKIP_CREATE=true
    fi
else
    ok "No existing queue manager found"
    SKIP_CREATE=false
fi

# --- Create queue manager ---
step "4/6" "Creating queue manager $QM"
if [ "${SKIP_CREATE:-false}" = "false" ]; then
    "$MQ_BIN/crtmqm" "$QM"
    ok "Queue manager created"
fi

# --- Start queue manager ---
step "5/6" "Starting queue manager $QM"
STATUS=$("$MQ_BIN/dspmq" -m "$QM" 2>/dev/null | grep -oP 'STATUS\(\K[^)]+' || echo "Unknown")
if [[ "$STATUS" == "Running" ]]; then
    ok "Queue manager already running"
else
    "$MQ_BIN/strmqm" "$QM"
    ok "Queue manager started"
fi

# --- Create queues, channels, listener ---
step "6/6" "Creating queues, channels, and listener"

cat > "$MQSC_FILE" << 'MQSC'
* ====================================================================
* FINVEST ISPB: 36266751  |  BACEN ISPB: 00038166
* Queue Manager: QM.36266751.01
* ====================================================================

* Local Queues — Messages FROM Bacen TO Finvest
DEFINE QLOCAL('QL.REQ.00038166.36266751.01') DESCR('Bacen Request to Finvest')   DEFPSIST(YES) MAXDEPTH(5000) REPLACE
DEFINE QLOCAL('QL.RSP.00038166.36266751.01') DESCR('Bacen Response to Finvest')  DEFPSIST(YES) MAXDEPTH(5000) REPLACE
DEFINE QLOCAL('QL.REP.00038166.36266751.01') DESCR('Bacen Report to Finvest')    DEFPSIST(YES) MAXDEPTH(5000) REPLACE
DEFINE QLOCAL('QL.SUP.00038166.36266751.01') DESCR('Bacen Support to Finvest')   DEFPSIST(YES) MAXDEPTH(5000) REPLACE

* Remote Queues — Messages FROM Finvest TO Bacen
DEFINE QREMOTE('QR.REQ.36266751.00038166.01') DESCR('Finvest Request to Bacen')  RNAME('QL.REQ.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE
DEFINE QREMOTE('QR.RSP.36266751.00038166.01') DESCR('Finvest Response to Bacen') RNAME('QL.RSP.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE
DEFINE QREMOTE('QR.REP.36266751.00038166.01') DESCR('Finvest Report to Bacen')   RNAME('QL.REP.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE
DEFINE QREMOTE('QR.SUP.36266751.00038166.01') DESCR('Finvest Support to Bacen')  RNAME('QL.SUP.36266751.00038166.01') RQMNAME('QM.BACEN') XMITQ('QL.RSP.00038166.36266751.01') REPLACE

* Dead Letter Queue
DEFINE QLOCAL('SYSTEM.DEAD.LETTER.QUEUE') REPLACE

* TCP Listener on port 1414
DEFINE LISTENER('FINVEST.LISTENER') TRPTYPE(TCP) PORT(1414) CONTROL(QMGR) REPLACE
START LISTENER('FINVEST.LISTENER')

* Server Connection Channel for pymqi
DEFINE CHANNEL('FINVEST.SVRCONN') CHLTYPE(SVRCONN) TRPTYPE(TCP) REPLACE

* Disable auth for local development
ALTER QMGR CHLAUTH(DISABLED)
ALTER QMGR CONNAUTH('')
REFRESH SECURITY TYPE(CONNAUTH)

END
MQSC

"$MQ_BIN/runmqsc" "$QM" < "$MQSC_FILE"
rm -f "$MQSC_FILE"

# --- Verify ---
echo ""
echo "========================================================"
echo " Verification"
echo "========================================================"

# Queue manager status
QM_STATUS=$("$MQ_BIN/dspmq" -m "$QM" 2>/dev/null | grep -oP 'STATUS\(\K[^)]+' || echo "Unknown")
if [[ "$QM_STATUS" == "Running" ]]; then
    ok "Queue manager $QM is Running"
else
    fail "Queue manager $QM status: $QM_STATUS"
fi

# Count local queues (expect 5: 4 app + dead letter)
LOCAL_COUNT=$(echo "DISPLAY QLOCAL(*)" | "$MQ_BIN/runmqsc" "$QM" 2>/dev/null | grep -c "QUEUE(" || true)
ok "Local queues found: $LOCAL_COUNT (expect 5)"

# Count remote queues (expect 4)
REMOTE_COUNT=$(echo "DISPLAY QREMOTE(*)" | "$MQ_BIN/runmqsc" "$QM" 2>/dev/null | grep -c "QUEUE(" || true)
ok "Remote queues found: $REMOTE_COUNT (expect 4)"

# Listener status
LISTENER_STATUS=$(echo "DISPLAY LSSTATUS('FINVEST.LISTENER') STATUS" | "$MQ_BIN/runmqsc" "$QM" 2>/dev/null | grep -oP 'STATUS\(\K[^)]+' || echo "Unknown")
if [[ "$LISTENER_STATUS" == "RUNNING" ]]; then
    ok "Listener FINVEST.LISTENER is RUNNING on port 1414"
else
    warn "Listener status: $LISTENER_STATUS"
fi

# Port 1414
if ss -tlnp 2>/dev/null | grep -q ':1414'; then
    ok "Port 1414 is open"
else
    warn "Port 1414 not detected (listener may take a moment to start)"
fi

echo ""
echo "========================================================"
echo " Setup Complete!"
echo " Queue Manager : $QM"
echo " Channel       : FINVEST.SVRCONN"
echo " Listener      : localhost(1414)"
echo "========================================================"
echo ""
echo "Next step: install pymqi and run the integration tests."
