#!/bin/bash

TARGET_HOST="webserver" # Docker service name
TARGET_PORT_HTTP="80"

echo "------------------------------------------"
echo "Starting Port Scan against $TARGET_HOST..."
echo "------------------------------------------"

echo "[INFO] Pinging $TARGET_HOST to check reachability..."
ping -c 3 $TARGET_HOST
if [ $? -ne 0 ]; then
    echo "[ERROR] Host $TARGET_HOST is not reachable. Aborting scan."
    exit 1
fi
echo ""

echo "[INFO] Performing TCP connect scan on common ports of $TARGET_HOST..."
# -sT: TCP Connect Scan (easier for Suricata to detect than -sS if not configured for raw sockets)
# -Pn: Skip host discovery (assume host is up if ping worked, or force if ping blocked)
# -p-: Scan all 65535 ports (can be slow, use -p 1-1024 for quicker common ports)
# For demo, let's scan a smaller range
nmap -sT -Pn -p 1-1000 $TARGET_HOST

echo ""
echo "[INFO] Performing version detection on open HTTP port ($TARGET_PORT_HTTP) of $TARGET_HOST..."
nmap -sV -Pn -p $TARGET_PORT_HTTP $TARGET_HOST

echo ""
echo "------------------------------------------"
echo "Port Scan Finished."
echo "Check Suricata logs (./logs/eve.json on host) for alerts."
echo "------------------------------------------"