# Linux Homework

## Task 1: Soft Link and Hard Link

A hard link is another name for the same file. Both names point to the same inode, the
real data on disk, so neither one is the original. A soft link (symlink) is a small
separate file holding the path to another file, like a shortcut, so if the target is
deleted or moved the link points at nothing.

    ln original.txt hard.txt       hard link
    ln -s original.txt soft.txt    soft link, -s means symbolic
    rm soft.txt                    deletes the link only, not the target

What I practiced. After echo "hello" > original.txt, then ln -s original.txt soft.txt
and ln original.txt hard.txt, ls -li gave:

    23231483 -rw-r--r-- 2 me wheel  6 hard.txt
    23231483 -rw-r--r-- 2 me wheel  6 original.txt
    23231484 lrwxr-xr-x 1 me wheel 12 soft.txt -> original.txt

The original and the hard link share inode 23231483 with a link count of 2, so it is one
file with two names. The soft link has its own inode, starts with l, and shows an arrow
to its target. After rm original.txt, cat hard.txt still prints hello but cat soft.txt
says no such file, because the hard link kept the data alive while the soft link now
points at a path that is gone. Hard links also cannot cross filesystems or point to a
directory, soft links can do both.

Interview answer: a hard link is a second name for the same inode, so the file survives
as long as one link exists. A soft link is a separate file holding a path, so it breaks
if the target is moved or deleted. Created with ln and ln -s.

## Task 2: adduser vs useradd

useradd is the low level command, present on every distribution. It does exactly what
you tell it, so by default no home directory, no password, no questions. adduser on
Ubuntu and Debian is a script that calls useradd underneath, and it is interactive,
creates the home directory, copies files from /etc/skel, sets up the group and prompts
for a password.

On Ubuntu, adduser is preferred for creating a user by hand because it handles the home
directory, shell and password without extra flags, so there is less to forget. useradd
is better in scripts, where you do not want prompts, and on RHEL based systems where
adduser is just a link to useradd anyway.

    sudo adduser testuser     then answer the password and info prompts
    id testuser               check it worked

The same with useradd needs the flags spelled out, and cleanup afterwards:

    sudo useradd -m -s /bin/bash testuser2   -m makes the home dir, -s sets the shell
    sudo passwd testuser2                    password is a separate step
    sudo deluser --remove-home testuser

## Task 3: journalctl

journalctl reads the logs collected by systemd-journald. On modern Linux most logs go
here instead of into separate files under /var/log, so one command gives you kernel
messages, boot messages and every service's output.

    journalctl -f                      follow the log live, like tail -f
    journalctl -n 50                   last 50 lines
    journalctl -u nginx                logs for one service
    journalctl -u nginx --since today
    journalctl -p err -b               errors only, current boot
    journalctl -b -1                   previous boot, useful after a crash
    journalctl -k                      kernel messages only
    sudo journalctl --vacuum-time=7d   delete logs older than 7 days

Checking one service, using ssh as the example. systemctl status ssh shows whether it is
running plus the last few lines, journalctl -u ssh -n 30 shows the last 30 lines,
journalctl -u ssh --since today -p err shows only today's errors, and journalctl -u ssh
-f watches it live while I try to log in. So when a service will not start: status to
see that it failed, -n 50 to read the real error, fix the config, restart, then -f to
watch it come back up.

## Task 4: Command Cheat Sheet

Navigation: pwd, ls -lah, cd /path, cd .., cd -

Files: touch file, mkdir -p a/b/c, cp file copy, cp -r dir dir2, mv a b, rm file, rm -r
dir. rm -rf has no undo, so check the path first.

Reading: cat file, less file, head -20 file, tail -20 file, tail -f file, wc -l file

Searching: grep "text" file, grep -ri "text" dir/, find . -name "*.log", which python3

Permissions: chmod 755 file, chmod +x script.sh, chown user:group file. Read is 4, write
2, execute 1, added up for owner then group then others, so 644 is owner read and write,
everyone else read only.

Users: whoami, id, adduser name, passwd name, usermod -aG sudo name (do not drop the -a
or you replace their groups), su - name, sudo -i

Processes and services: ps aux, ps aux | grep nginx, top, kill PID, kill -9 PID, pkill
name, systemctl status|start|stop|restart|enable name, journalctl -u name -f

System and network: df -h, du -sh *, free -h, uname -a, uptime, lsblk, ip a, ping host,
curl -I url, wget url, ss -tulpn, ssh user@host, scp file user@host:/path

Archives: tar -czvf a.tar.gz dir/ to create, tar -xzvf a.tar.gz to extract. c is create,
x is extract, z is gzip, v is verbose, f is filename.

Pipes and help: | passes output to the next command, > writes to a file, >> appends, 2>
redirects errors, for example cat access.log | grep 500 | wc -l counts the 500 errors.
Then man ls, ls --help, history, and Ctrl+R to search history.
