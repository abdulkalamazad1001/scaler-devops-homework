#!/bin/bash
# System Information Script
# Prints basic system details, then saves the running processes to a file.

# Variables holding the system details
CURRENT_DATE=$(date)
HOST_NAME=$(hostname)
USER_NAME=$(whoami)

echo "=============================="
echo "     SYSTEM INFORMATION"
echo "=============================="
echo "Date     : $CURRENT_DATE"
echo "Hostname : $HOST_NAME"
echo "Username : $USER_NAME"
echo ""

echo "----- Disk Usage -----"
df -h
echo ""

echo "----- Running Processes (first 10) -----"
ps -eo pid,user,%cpu,%mem,comm | head -10
echo ""

# Ask the user where to save the report
read -p "Enter a directory name to create: " DIR_NAME
read -p "Enter a file name for the process list: " FILE_NAME

mkdir -p "$DIR_NAME"
touch "$DIR_NAME/$FILE_NAME"

# Save the full process list into the file
ps aux > "$DIR_NAME/$FILE_NAME"

echo ""
echo "Directory created : $DIR_NAME"
echo "File created      : $DIR_NAME/$FILE_NAME"
echo "Lines saved       : $(wc -l < "$DIR_NAME/$FILE_NAME")"
echo "Done."
