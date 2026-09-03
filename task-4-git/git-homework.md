# Git Homework

Name: T. Abdul Kalam Azad

Roll number: 24BCS10053

Everything below was run in a throwaway repo created with git init, so the output is
real and the commit hashes match across the sections.

## Task 1: git commit -a -m vs git commit -m

### The difference in one line

git commit -m only commits what is already staged with git add. git commit -a -m stages
all modified and deleted tracked files first, then commits them, so it saves you the
git add step. Neither one picks up brand new untracked files.

### Setup

    git init -b main
    echo "# Git Practice" > notes.txt
    git add notes.txt
    git commit -m "First commit: add notes.txt"

### Test 1: change a tracked file, then use plain commit -m

    $ echo "line two" >> notes.txt
    $ git status --short
     M notes.txt

    $ git commit -m "try without -a"
    On branch main
    Changes not staged for commit:
      (use "git add <file>..." to update what will be committed)
      (use "git restore <file>..." to discard changes in working directory)
    	modified:   notes.txt

    no changes added to commit (use "git add" and/or "git commit -a")

Nothing was committed. The exit code was 1, which means the command failed. The change
exists in the working directory but was never staged, and commit -m only looks at the
staging area.

### Test 2: the same change with commit -a -m

    $ git commit -a -m "Add line two using commit -a"
    [main 916677e] Add line two using commit -a
     1 file changed, 1 insertion(+)

    $ git status --short
    (nothing, the working tree is clean)

This time it worked. The -a flag staged the modified file and committed it in one step.

### Test 3: does -a pick up a new file?

    $ echo "new file" > extra.txt
    $ git status --short
    ?? extra.txt

    $ git commit -a -m "try to commit untracked file with -a"
    On branch main
    Untracked files:
      (use "git add <file>..." to include in what will be committed)
    	extra.txt

    nothing added to commit but untracked files present (use "git add" to track)

It did not. The ?? in git status means the file is untracked, and git has never seen it
before, so -a ignores it. For a new file you have to use git add first:

    $ git add extra.txt
    $ git commit -m "Add extra.txt the two step way"
    [main b486dd7] Add extra.txt the two step way
     1 file changed, 1 insertion(+)
     create mode 100644 extra.txt

### The log after task 1

    $ git log --oneline
    b486dd7 Add extra.txt the two step way
    916677e Add line two using commit -a
    3ed3634 First commit: add notes.txt

### What I understood

-a is a shortcut, not a different kind of commit. It is convenient when you are editing
files that git already tracks, but it is also a bit risky because it sweeps in every
modified tracked file, including ones you did not mean to include in this commit. When I
want to commit only some of my changes, I use git add on those files and plain commit
-m. Also worth remembering that -a stages deletions too, so removing a file and running
commit -a records the deletion.

## Task 2: git cherry-pick

Cherry-pick copies one specific commit from one branch onto another, without bringing
along the other commits on that branch.

### Starting point: three commits on main

    $ git log --oneline
    b486dd7 Add extra.txt the two step way
    916677e Add line two using commit -a
    3ed3634 First commit: add notes.txt

### Create a branch and make three commits on it

    git checkout -b feature

    echo "work in progress feature A" > feature-a.txt
    git add . && git commit -m "Feature: add feature-a.txt"

    echo "fix: correct the typo in the config" > bugfix.txt
    git add . && git commit -m "Bugfix: correct typo in config"

    echo "work in progress feature C" > feature-c.txt
    git add . && git commit -m "Feature: add feature-c.txt"

### The log on the feature branch

    $ git log --oneline
    13c423c Feature: add feature-c.txt
    cfec984 Bugfix: correct typo in config
    3d85321 Feature: add feature-a.txt
    b486dd7 Add extra.txt the two step way
    916677e Add line two using commit -a
    3ed3634 First commit: add notes.txt

### Identify the commit I want

The situation is that the bugfix is urgent and should go to main now, but the two feature
commits are not finished and should stay on the branch.

    $ git log --oneline --grep="Bugfix"
    cfec984 Bugfix: correct typo in config

    $ git show cfec984 --stat
    commit cfec984f468e0e8be2b72b9d0936ca89606e119d
    Author: Abdul Kalam Azad <abdulkalam.azad@scalerailabs.com>
    Date:   Tue Sep 1 17:47:11 2026 +0530

        Bugfix: correct typo in config

     bugfix.txt | 1 +
     1 file changed, 1 insertion(+)

So cfec984 is the commit hash I need.

### Cherry-pick it into main

    $ git checkout main
    Switched to branch 'main'

    $ ls
    extra.txt   notes.txt

    $ git cherry-pick cfec984
    [main 20f474f] Bugfix: correct typo in config
     Date: Tue Sep 1 17:47:11 2026 +0530
     1 file changed, 1 insertion(+)
     create mode 100644 bugfix.txt

### Verify the change is in main

    $ git log --oneline
    20f474f Bugfix: correct typo in config
    b486dd7 Add extra.txt the two step way
    916677e Add line two using commit -a
    3ed3634 First commit: add notes.txt

    $ ls
    bugfix.txt  extra.txt   notes.txt

    $ cat bugfix.txt
    fix: correct the typo in the config

The bugfix commit and its file are now on main, and feature-a.txt and feature-c.txt are
not, which is exactly what I wanted.

### The branch picture

    $ git log --oneline --graph --all
    * 20f474f Bugfix: correct typo in config
    | * 13c423c Feature: add feature-c.txt
    | * cfec984 Bugfix: correct typo in config
    | * 3d85321 Feature: add feature-a.txt
    |/
    * b486dd7 Add extra.txt the two step way
    * 916677e Add line two using commit -a
    * 3ed3634 First commit: add notes.txt

### What I understood

The important detail is in the graph. The commit on main is 20f474f but the original on
feature is still cfec984. Cherry-pick does not move a commit, it applies the same change
as a brand new commit with a new hash. The message, the author and the date are copied,
which is why the output shows the original date.

Because the change now exists twice, merging feature into main later can be confusing.
Git usually handles it, since the content is identical, but if the same lines were also
edited afterwards you can get a conflict. So cherry-pick is for the case where you need
one specific fix somewhere else now, not as a general way to move work between branches.
For that, merge or rebase is the right tool.

Useful extras I noted:

    git cherry-pick <hash>          copy one commit
    git cherry-pick <h1> <h2>       copy several
    git cherry-pick <h1>..<h2>      copy a range
    git cherry-pick -n <hash>       apply the change but do not commit yet
    git cherry-pick --abort         back out if there is a conflict
    git cherry-pick --continue      carry on after fixing a conflict
