#!/bin/bash
# Start SPBSite for remote access

echo "🌐 Starting SPBSite Web Interface for Remote Access"
echo "=================================================="
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "Server IP: $SERVER_IP"
echo "Port: 8000"
echo ""

# Check if already running
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "⚠️  SPBSite is already running!"
    echo ""
    echo "To stop it: pkill -f 'uvicorn app.main:app'"
    echo ""
    exit 1
fi

# Change to SPBSite directory
cd /home/ubuntu/SPB_FINAL/spbsite

# Start SPBSite
echo "Starting SPBSite..."
echo "Access URLs:"
echo "  - Local network: http://$SERVER_IP:8000"
echo "  - Localhost: http://localhost:8000"
echo ""
echo "⚠️  IMPORTANT: If accessing from internet (AWS), you need to:"
echo "  1. Find your AWS public IP in EC2 Console"
echo "  2. Configure Security Group to allow port 8000"
echo "  3. Access: http://YOUR_PUBLIC_IP:8000"
echo ""
echo "Press Ctrl+C to stop SPBSite"
echo "=================================================="
echo ""

# Start uvicorn with 0.0.0.0 to allow remote access
~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
