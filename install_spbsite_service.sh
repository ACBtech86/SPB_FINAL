#!/bin/bash
# Install SPBSite as a systemd service for permanent remote access

echo "📦 Installing SPBSite as systemd service"
echo "========================================"
echo ""

# Create systemd service file
echo "Creating systemd service file..."
sudo tee /etc/systemd/system/spbsite.service > /dev/null << 'EOF'
[Unit]
Description=SPBSite Web Interface for SPB Message Monitoring
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/SPB_FINAL/spbsite
Environment="PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service to start on boot
echo "Enabling SPBSite service..."
sudo systemctl enable spbsite

# Start service
echo "Starting SPBSite service..."
sudo systemctl start spbsite

# Wait a moment for startup
sleep 2

# Check status
echo ""
echo "========================================"
echo "✅ SPBSite Service Installed!"
echo "========================================"
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

# Show status
sudo systemctl status spbsite --no-pager

echo ""
echo "📊 Service Information:"
echo "  Status: sudo systemctl status spbsite"
echo "  Start:  sudo systemctl start spbsite"
echo "  Stop:   sudo systemctl stop spbsite"
echo "  Logs:   sudo journalctl -u spbsite -f"
echo ""
echo "🌐 Access URLs:"
echo "  Local network: http://$SERVER_IP:8000"
echo "  Localhost: http://localhost:8000"
echo ""
echo "⚠️  For internet access (AWS):"
echo "  1. Get your public IP from AWS EC2 Console"
echo "  2. Configure Security Group to allow port 8000"
echo "  3. Access: http://YOUR_PUBLIC_IP:8000"
echo ""
