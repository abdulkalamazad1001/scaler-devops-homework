#!/usr/bin/env bash
set -euo pipefail

work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
cd "$work"

bash -n /src/task-2-shell-scripting/sysinfo.sh
bash /src/task-2-shell-scripting/sysinfo.sh </dev/null >default.log
test -s sysreport/processes.txt
cat default.log
head -5 sysreport/processes.txt
grep -q 'Done.' default.log
printf 'folder with spaces\nreport.txt\n' | bash /src/task-2-shell-scripting/sysinfo.sh >spaces.log
test -s 'folder with spaces/report.txt'
printf 'not a directory' >blocked
if printf 'blocked\nreport.txt\n' | bash /src/task-2-shell-scripting/sysinfo.sh >failure.log 2>&1; then
    echo 'FAIL: script accepted an unwritable report destination'
    exit 1
fi
if grep -q 'Done.' failure.log; then
    echo 'FAIL: script reported success after a write error'
    exit 1
fi
echo 'PASS: default inputs, paths containing spaces, and failed writes'

printf 'link-test\n' >original.txt
ln original.txt hard.txt
ln -s original.txt soft.txt
test "$(stat -c %i original.txt)" = "$(stat -c %i hard.txt)"
rm original.txt
test -f hard.txt
test ! -e soft.txt
chmod 640 hard.txt
test "$(stat -c %a hard.txt)" = 640
tar -czf archive.tar.gz hard.txt
tar -tzf archive.tar.gz | grep -q hard.txt
echo 'PASS task 1: hard links, broken symlink, permissions and archive'

useradd -m -s /bin/bash homework-lab-user
id homework-lab-user
test -d /home/homework-lab-user
test "$(getent passwd homework-lab-user | cut -d: -f7)" = /bin/bash
userdel -r homework-lab-user
adduser --disabled-password --gecos 'Homework test account' homework-adduser
id homework-adduser
test -d /home/homework-adduser
deluser --remove-home homework-adduser
echo 'PASS task 1: adduser creates an Ubuntu account and home directory'
echo 'PASS task 1: explicit useradd home/shell and account cleanup in disposable container'

ip -brief address
ip route
ping -c 1 127.0.0.1
ss -lnt
echo 'PASS task 3: container interfaces, routes, loopback and socket inspection'

ip link add homework0 type dummy
ip address add 192.0.2.10/24 dev homework0
ip link set homework0 up
ip route add 198.51.100.0/24 via 192.0.2.1 dev homework0
ip route get 198.51.100.5 | grep 'via 192.0.2.1 dev homework0'
ip route del 198.51.100.0/24
ip address del 192.0.2.10/24 dev homework0
ip link delete homework0
echo 'PASS task 3: interface/address/route creation and deletion in isolated container network'

git init -q -b main git-lab
cd git-lab
git config user.name 'Homework review fixture'
git config user.email 'fixture@example.invalid'
printf 'one\n' >tracked.txt
git add tracked.txt
git commit -qm initial
printf 'two\n' >>tracked.txt
if git commit -qm unstaged; then
    echo 'FAIL: plain commit unexpectedly included unstaged changes'
    exit 1
fi
git commit -qam tracked-change
printf 'new\n' >untracked.txt
if git commit -qam untracked; then
    echo 'FAIL: commit -a unexpectedly added an untracked file'
    exit 1
fi
git switch -qc feature
git add untracked.txt
git commit -qm feature
git switch -q main
git merge --ff-only feature
test -f untracked.txt
echo 'PASS task 4: staged vs unstaged commits, untracked files, branch and merge'

git switch -qc fixes
printf 'feature-only\n' >feature-only.txt
git add feature-only.txt
git commit -qm unrelated-feature
printf 'selected-fix\n' >fix.txt
git add fix.txt
git commit -qm selected-fix
original_fix=$(git rev-parse HEAD)
git switch -q main
git cherry-pick "$original_fix"
test -f fix.txt
test ! -f feature-only.txt
test "$(git rev-parse HEAD)" != "$original_fix"
git log --oneline --graph --all
echo 'PASS task 4: cherry-pick copies the selected change with a new parent/hash'

while IFS= read -r -d '' script; do
    bash -n "$script"
    echo "PASS syntax: $script"
done < <(find /src/task-* -name '*.sh' -type f -print0)
