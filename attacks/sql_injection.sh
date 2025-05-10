#!/bin/bash

TARGET_HOST="webserver" # Docker service name
TARGET_PATH="/index.html"

echo "--------------------------------------------------"
echo "Attempting simulated SQL Injection attacks against $TARGET_HOST$TARGET_PATH..."
echo "--------------------------------------------------"

# Basic SQLi patterns
echo "[ATTACK 1] Attempting basic SQLi: id=1' OR '1'='1"
curl -s "http://$TARGET_HOST$TARGET_PATH?id=1'%20OR%20'1'='1" -o /dev/null
echo "Sent. Check IDS logs."
sleep 1

echo "[ATTACK 2] Attempting UNION SELECT: id=1' UNION SELECT username, password FROM users --"
# URL encode ' ' as %20, "'" as %27
PAYLOAD_UNION="id=1'%20UNION%20SELECT%20username,%20password%20FROM%20users%20--"
curl -s "http://$TARGET_HOST$TARGET_PATH?$PAYLOAD_UNION" -o /dev/null
echo "Sent. Check IDS logs."
sleep 1

echo "[ATTACK 3] Attempting SQLi with comment: item=hammer'--"
curl -s "http://$TARGET_HOST$TARGET_PATH?item=hammer'--" -o /dev/null
echo "Sent. Check IDS logs."
sleep 1

# Using sqlmap (if installed and configured)
# This is a more advanced tool.
if command -v sqlmap &> /dev/null
then
    echo ""
    echo "[INFO] sqlmap found. Attempting a basic sqlmap scan (non-interactive)..."
    echo "Note: This might take a few minutes and generate more complex traffic."
    sqlmap -u "http://$TARGET_HOST$TARGET_PATH?id=1" --batch --level=1 --risk=1 --disable-coloring
    echo "sqlmap scan initiated. Check IDS logs."
else
    echo ""
    echo "[INFO] sqlmap not found or not in PATH. Skipping sqlmap attack."
fi


echo "--------------------------------------------------"
echo "SQL Injection attempts finished."
echo "Check Suricata logs (./logs/eve.json on host) for alerts."
echo "Remember, the webserver is static; these attacks won't actually 'work' "
echo "on the webserver itself, but the IDS should detect the malicious patterns."
echo "--------------------------------------------------"