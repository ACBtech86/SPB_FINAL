#!/bin/bash
# Quick E2E Test Script
# Runs the complete end-to-end test flow

set -e  # Exit on error

echo "================================================================================"
echo "SPB System - End-to-End Test"
echo "================================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Check IBM MQ Status${NC}"
echo "--------------------------------------------------------------------------------"
python test_scripts/check_mq_status.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ MQ check failed. Please start IBM MQ and create queues.${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 2: Submit Test Message${NC}"
echo "--------------------------------------------------------------------------------"
python test_scripts/submit_test_message.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to submit test message${NC}"
    exit 1
fi
echo ""

# Get the operation number
if [ -f "test_scripts/last_operation.txt" ]; then
    NU_OPE=$(cat test_scripts/last_operation.txt)
    echo -e "${GREEN}✅ Operation Number: $NU_OPE${NC}"
else
    echo -e "${RED}❌ Could not read operation number${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 3: Wait for BCSrvSqlMq to process (10 seconds)${NC}"
echo "--------------------------------------------------------------------------------"
echo "Make sure BCSrvSqlMq is running!"
echo "Expected: BCSrvSqlMq picks up message and sends to MQ"
sleep 10
echo ""

echo -e "${YELLOW}Step 4: Browse Outbound Queue${NC}"
echo "--------------------------------------------------------------------------------"
python test_scripts/browse_mq_queue.py QR.REQ.36266751.00038166.01
echo ""

echo -e "${YELLOW}Step 5: Simulate BACEN Response (COA)${NC}"
echo "--------------------------------------------------------------------------------"
python test_scripts/simulate_bacen_response.py --operation-number "$NU_OPE" --response-type COA
echo ""

echo -e "${YELLOW}Step 6: Wait for BCSrvSqlMq to receive response (10 seconds)${NC}"
echo "--------------------------------------------------------------------------------"
echo "Expected: BCSrvSqlMq picks up response and updates database"
sleep 10
echo ""

echo -e "${YELLOW}Step 7: Browse Response Queue${NC}"
echo "--------------------------------------------------------------------------------"
python test_scripts/browse_mq_queue.py QL.RSP.00038166.36266751.01
echo ""

echo "================================================================================"
echo -e "${GREEN}✅ E2E Test Complete!${NC}"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "1. Check SPBSite: http://localhost:8000"
echo "2. View message status for operation: $NU_OPE"
echo "3. Check database:"
echo "   SELECT * FROM spb_local_to_bacen WHERE nu_ope = '$NU_OPE';"
echo "   SELECT * FROM spb_bacen_to_local WHERE nu_ope LIKE '%$NU_OPE%';"
echo ""
echo "To test full cycle (COA → COD):"
echo "  python test_scripts/simulate_bacen_response.py --operation-number $NU_OPE --response-type COD"
echo ""
