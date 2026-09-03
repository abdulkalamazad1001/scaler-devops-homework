# System Information Script

A shell script that prints basic system details, asks the user where to save a report,
and writes the full list of running processes into a file.

## What it does

1. Prints the current date, the hostname and the username, all stored in variables.
2. Prints disk usage with df -h.
3. Prints the first ten running processes with ps.
4. Uses read -p to ask for a directory name and a file name.
5. Creates the directory with mkdir and the file with touch.
6. Saves the full process list into that file using the > redirection operator.

## Commands used

mkdir, touch, echo, date, hostname, whoami, df, ps, read -p, variables, and >
redirection.

## The script

    #!/bin/bash
    # System Information Script

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

    read -p "Enter a directory name to create: " DIR_NAME
    read -p "Enter a file name for the process list: " FILE_NAME

    mkdir -p "$DIR_NAME"
    touch "$DIR_NAME/$FILE_NAME"

    ps aux > "$DIR_NAME/$FILE_NAME"

    echo ""
    echo "Directory created : $DIR_NAME"
    echo "File created      : $DIR_NAME/$FILE_NAME"
    echo "Lines saved       : $(wc -l < "$DIR_NAME/$FILE_NAME")"
    echo "Done."

## How to run it

    chmod +x sysinfo.sh
    ./sysinfo.sh

It will ask for a directory name and a file name. I used sysreport and processes.txt.

## Output

    ==============================
         SYSTEM INFORMATION
    ==============================
    Date     : Tue Sep  1 12:11:51 IST 2026
    Hostname : Mohammeds-MacBook-Pro.local
    Username : mohammedabdurrahman

    ----- Disk Usage -----
    Filesystem        Size    Used   Avail Capacity  Mounted on
    /dev/disk3s1s1   926Gi    16Gi   571Gi     3%    /
    devfs            206Ki   206Ki     0Bi   100%    /dev
    /dev/disk3s6     926Gi    19Gi   571Gi     4%    /System/Volumes/VM
    /dev/disk3s2     926Gi    17Gi   571Gi     3%    /System/Volumes/Preboot
    /dev/disk3s4     926Gi   868Mi   571Gi     1%    /System/Volumes/Update
    /dev/disk3s5     926Gi   299Gi   571Gi    35%    /System/Volumes/Data

    ----- Running Processes (first 10) -----
      PID USER              %CPU %MEM COMM
        1 root               0.0  0.1 /sbin/launchd
      336 root               0.2  0.1 /usr/libexec/logd
      338 root               0.0  0.0 /usr/libexec/UserEventAgent
      340 root               0.0  0.0 .../FSEvents.framework/Support/fseventsd
      341 root               0.0  0.0 .../MediaRemote.framework/Support/mediaremoted
      344 root               0.0  0.0 /usr/sbin/systemstats
      348 root               0.0  0.0 /usr/libexec/configd
      350 root               0.0  0.0 /System/Library/CoreServices/powerd.bundle/powerd
      351 root               0.0  0.0 /usr/libexec/IOMFB_bics_daemon

    Enter a directory name to create: sysreport
    Enter a file name for the process list: processes.txt

    Directory created : sysreport
    File created      : sysreport/processes.txt
    Lines saved       : 649
    Done.

The disk usage and process lists above are trimmed so they fit here, the script prints
the full output.

## Checking the file that was created

    $ ls -l sysreport/
    -rw-r--r--  1 mohammedabdurrahman  staff  230231  1 Sep 12:11 processes.txt

    $ head -3 sysreport/processes.txt
    USER               PID  %CPU %MEM      VSZ    RSS   TT  STAT STARTED      TIME COMMAND
    _windowserver      409  33.7  0.4 438071280 108368   ??  Rs    1Apr76 1819:40.36 /System/...
    mohammedabdurrahman 35830 24.7  2.6 1957543776 655104  ??  S    Tue03PM  43:24.54 /Applic...

    $ wc -l sysreport/processes.txt
    649 sysreport/processes.txt

## Notes

I ran this on macOS, so the hostname, disk names and process names look Apple specific.
On Linux the same script works unchanged, only the output looks different, for example
df -h shows /dev/sda1 style filesystems.

The ps line uses -eo pid,user,%cpu,%mem,comm because plain ps aux prints very long
command lines that wrap badly. The full ps aux output is still what gets saved to the
file.

mkdir -p is used instead of plain mkdir so that re-running the script does not fail with
a directory already exists error.

The variables are quoted, as in "$DIR_NAME/$FILE_NAME", so that names with spaces still
work.
