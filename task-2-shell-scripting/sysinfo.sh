#!/bin/bash
# System Information Script
# Prints basic system details, then saves the running processes to a file.
#
# Author : T. Abdul Kalam Azad
# Roll no: 24BCS10053

# Stop before reporting success if collecting or writing the report fails.
set -euo pipefail

# Variables holding the system details
CURRENT_DATE=$(date)
HOST_NAME=$(hostname)
USER_NAME=$(whoami)
KERNEL=$(uname -sr)
UP_TIME=$(uptime | sed 's/^ *//')

echo "=============================="
echo "     SYSTEM INFORMATION"
echo "=============================="
echo "Date     : $CURRENT_DATE"
echo "Hostname : $HOST_NAME"
echo "Username : $USER_NAME"
echo "Kernel   : $KERNEL"
echo "Uptime   : $UP_TIME"
echo ""

echo "----- Disk Usage -----"
df -h
echo ""

echo "----- Running Processes (first 10) -----"
ps -eo pid,user,%cpu,%mem,comm | sed -n '1,10p'
echo ""

# Ask the user where to save the report.
# Initialised first so that `set -u` is safe if read hits end of input.
DIR_NAME=""
FILE_NAME=""
read -r -p "Enter a directory name to create [sysreport]: " DIR_NAME || true
read -r -p "Enter a file name for the process list [processes.txt]: " FILE_NAME || true

# Fall back to sensible defaults if the answer was left blank
DIR_NAME=${DIR_NAME:-sysreport}
FILE_NAME=${FILE_NAME:-processes.txt}

REPORT="$DIR_NAME/$FILE_NAME"

mkdir -p "$DIR_NAME"
touch "$REPORT"

# Save the full process list into the file
ps aux > "$REPORT"

echo ""
echo "Directory created : $DIR_NAME"
echo "File created      : $REPORT"
echo "Full path         : $(cd "$DIR_NAME" && pwd)/$FILE_NAME"
echo "Lines saved       : $(wc -l < "$REPORT" | tr -d " ")"
echo "Size on disk      : $(du -h "$REPORT" | cut -f1)"
echo "Done."
