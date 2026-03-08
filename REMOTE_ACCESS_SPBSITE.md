# Remote Access to SPBSite Web Interface

**Server IP:** 172.31.15.80
**SPBSite Port:** 8000
**Status:** Ready for remote access

---

## 🌐 Quick Access Guide

### Your Server Information
- **Private IP:** 172.31.15.80
- **SPBSite Port:** 8000
- **Firewall (UFW):** Inactive (no blocking)

---

## Step 1: Start SPBSite Server

### Option A: Start for Testing (Foreground)
```bash
cd /home/ubuntu/SPB_FINAL/spbsite
~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```
**Note:** `--host 0.0.0.0` allows connections from any network interface

### Option B: Start in Background
```bash
cd /home/ubuntu/SPB_FINAL/spbsite
nohup ~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > spbsite.log 2>&1 &
```

### Option C: Start with Systemd (Permanent Service)
Create a systemd service file:

```bash
sudo tee /etc/systemd/system/spbsite.service > /dev/null << 'EOF'
[Unit]
Description=SPBSite Web Interface
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

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable spbsite
sudo systemctl start spbsite

# Check status
sudo systemctl status spbsite
```

---

## Step 2: Configure Network Access

### If on AWS/Cloud (Most Likely Your Case)

Your server IP (172.31.x.x) indicates you're on AWS. You need to configure the **Security Group**:

1. **Go to AWS Console:**
   - Navigate to EC2 Dashboard
   - Select your instance
   - Click on the Security Group (in the Security tab)

2. **Add Inbound Rule:**
   - Click "Edit inbound rules"
   - Click "Add rule"
   - **Type:** Custom TCP
   - **Port range:** 8000
   - **Source:** Choose one:
     - `0.0.0.0/0` - Allow from anywhere (not secure, for testing)
     - `My IP` - Allow only from your current IP (recommended)
     - `Custom` - Specify your office/home network CIDR

3. **Save the rule**

### If on Local Network

If this is a local server (not cloud):

**Enable UFW and open port 8000:**
```bash
# Enable firewall
sudo ufw enable

# Allow SSH first (important!)
sudo ufw allow 22/tcp

# Allow SPBSite
sudo ufw allow 8000/tcp

# Check status
sudo ufw status
```

---

## Step 3: Access SPBSite

### From Same Network
```
http://172.31.15.80:8000
```

### From Internet (AWS Only)
You need the **public IP** of your AWS instance:

1. **Find Public IP:**
   - Go to AWS EC2 Console
   - Select your instance
   - Look for "Public IPv4 address" or "Public IPv4 DNS"
   - Example: `52.12.34.56` or `ec2-52-12-34-56.compute-1.amazonaws.com`

2. **Access URL:**
   ```
   http://YOUR_PUBLIC_IP:8000
   ```
   or
   ```
   http://YOUR_PUBLIC_DNS:8000
   ```

---

## Step 4: Verify SPBSite is Running

### Check if SPBSite is listening on all interfaces:
```bash
sudo netstat -tlnp | grep 8000
```

**Expected output:**
```
tcp        0      0 0.0.0.0:8000            0.0.0.0:*               LISTEN      12345/python
```

**Note:** `0.0.0.0:8000` means it's listening on ALL network interfaces (correct for remote access)

### Check SPBSite logs:
```bash
# If running with systemd
sudo journalctl -u spbsite -f

# If running with nohup
tail -f /home/ubuntu/SPB_FINAL/spbsite/spbsite.log
```

---

## Step 5: Test Access

### From the Server (Local Test)
```bash
curl http://localhost:8000/
curl http://172.31.15.80:8000/
```

### From Another Machine
Open a web browser and go to:
```
http://172.31.15.80:8000        (if on same network)
http://YOUR_PUBLIC_IP:8000       (if on internet/AWS)
```

**Expected:** You should see the SPBSite interface redirecting to the monitoring page

---

## 🔒 Security Considerations

### For Production Use:

1. **Use HTTPS (SSL/TLS)**
   - Get SSL certificate (Let's Encrypt)
   - Use nginx as reverse proxy
   - Configure SSL termination

2. **Restrict Access**
   - Use VPN for remote access
   - Whitelist specific IP addresses
   - Enable authentication (SPBSite has built-in auth)

3. **Use Reverse Proxy**
   ```bash
   # Install nginx
   sudo apt update
   sudo apt install -y nginx

   # Configure nginx
   sudo tee /etc/nginx/sites-available/spbsite > /dev/null << 'EOF'
   server {
       listen 80;
       server_name YOUR_DOMAIN_OR_IP;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   EOF

   # Enable site
   sudo ln -s /etc/nginx/sites-available/spbsite /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx

   # Open port 80 instead of 8000
   sudo ufw allow 80/tcp
   ```

---

## 📱 Access URLs

### SPBSite Pages

| Page | URL |
|------|-----|
| **Home** | http://SERVER_IP:8000/ |
| **API Docs** | http://SERVER_IP:8000/docs |
| **Login** | http://SERVER_IP:8000/login |
| **Monitoring** | http://SERVER_IP:8000/monitoring/control/local |
| **Inbound Messages** | http://SERVER_IP:8000/monitoring/messages/inbound/bacen |
| **Outbound Messages** | http://SERVER_IP:8000/monitoring/messages/outbound/bacen |
| **Message Viewer** | http://SERVER_IP:8000/viewer/spb_bacen_to_local/MESSAGE_ID |

Replace `SERVER_IP` with:
- `172.31.15.80` (same network)
- Your AWS public IP (from internet)

---

## 🔧 Troubleshooting

### Problem: "Connection refused"

**Check if SPBSite is running:**
```bash
ps aux | grep uvicorn
sudo netstat -tlnp | grep 8000
```

**Solution:**
```bash
cd /home/ubuntu/SPB_FINAL/spbsite
~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Problem: "Connection timeout"

**Check firewall:**
```bash
sudo ufw status
```

**Check AWS Security Group:**
- Ensure port 8000 is open in inbound rules

**Check SPBSite is listening on 0.0.0.0:**
```bash
sudo netstat -tlnp | grep 8000
# Should show: 0.0.0.0:8000 (NOT 127.0.0.1:8000)
```

### Problem: "Database connection error"

**Check PostgreSQL is running:**
```bash
sudo systemctl status postgresql
```

**Check .env file:**
```bash
cat /home/ubuntu/SPB_FINAL/spbsite/.env
# Verify DATABASE_URL is correct
```

### Problem: "404 Not Found"

**Check SPBSite logs:**
```bash
# If systemd
sudo journalctl -u spbsite -n 50

# If manual
# Check terminal output or spbsite.log
```

---

## 📊 Quick Start Commands

### Start SPBSite for Remote Access
```bash
cd /home/ubuntu/SPB_FINAL/spbsite
~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Check if Accessible
```bash
# From server
curl http://172.31.15.80:8000/docs

# Check what's listening
sudo netstat -tlnp | grep 8000
```

### Stop SPBSite
```bash
# If running in foreground: Ctrl+C

# If running in background
pkill -f "uvicorn app.main:app"

# If systemd service
sudo systemctl stop spbsite
```

---

## 🌟 Recommended Setup for Production

```bash
# 1. Create systemd service
sudo tee /etc/systemd/system/spbsite.service > /dev/null << 'EOF'
[Unit]
Description=SPBSite Web Interface
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/SPB_FINAL/spbsite
Environment="PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 2. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable spbsite
sudo systemctl start spbsite

# 3. Configure AWS Security Group (in AWS Console)
# - Allow port 8000 from your IP

# 4. Access from browser
# http://YOUR_AWS_PUBLIC_IP:8000
```

---

## 📝 Summary

**To access SPBSite from another machine:**

1. ✅ **Start SPBSite** with `--host 0.0.0.0`
2. ✅ **Configure AWS Security Group** to allow port 8000
3. ✅ **Get your public IP** from AWS Console
4. ✅ **Access:** `http://PUBLIC_IP:8000`

**Your Server:**
- Private IP: 172.31.15.80
- Port: 8000
- Firewall: Inactive (no local blocking)

**Need:** AWS Security Group configuration to allow port 8000

---

**Created:** 2026-03-08
**Status:** Ready for remote access
