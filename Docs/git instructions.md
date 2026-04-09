# Git Version Control for Django Project

This guide provides the essential Git commands and configuration steps to manage your Django (and Docker) project effectively.

## 1. Install Git (if not already installed)

Check if Git is installed:

bash
git --version
If not, install it:

Ubuntu/WSL:

bash
sudo apt update
sudo apt install git
macOS:

bash
brew install git
Windows: Download from git-scm.com.

Configure your identity (used for commits):

bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

## 2. Initialize a Git Repository

Navigate to your project root (the directory containing docker-compose.yml, backend/, etc.) and run:

bash
git init

## 3. Create a .gitignore File

Create a file named .gitignore in the project root with the following content (tailored for Django + Docker + environment files):

gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Django stuff
*.log
local_settings.py
db.sqlite3
media/
staticfiles/
static/

# Environment variables
.env
.env.local
.env.*

# Virtual environment
venv/
env/
ENV/
env.bak/
venv.bak/

# Docker
*.pid
docker-compose.override.yml

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Celery
celerybeat-schedule
celerybeat.pid

# Database migrations (optional – keep if you want to track them)
# !migrations/*.py
# Uncomment the line below if you do NOT want to track migrations
# */migrations/*.py
# */migrations/*.pyc
Note: The .env file is excluded because it contains secrets. Media and collected static files are also excluded.

## 4. Add and Commit Your Initial Code

Add all files (respecting .gitignore) to the staging area:

bash
git add .
Commit them with a descriptive message:

bash
git commit -m "Initial commit: Omnichannel Complaint Management System"

## 5. Create a Remote Repository (Optional but Recommended)

On GitHub (example):
Log in to GitHub.

Click the + icon → New repository.

Give it a name (e.g., omnichannel-cms). Do not initialise with README, .gitignore, or license (we already have them).

Copy the remote URL (e.g., https://github.com/yourusername/omnichannel-cms.git).

Link your local repo to the remote:
bash
git remote add origin https://github.com/yourusername/omnichannel-cms.git
git branch -M main
git push -u origin main

## 6. Create a .gitattributes File (Optional)

This file ensures consistent line endings and binary file handling. Create .gitattributes in the project root:

text
# Auto detect text files and perform LF normalization
* text=auto

# Python files
*.py text diff=python

# Dockerfiles
Dockerfile text

# Binary files (images, archives)
*.png binary
*.jpg binary
*.pdf binary
*.zip binary

## 7. Useful Git Workflow for Your Project

Regular Development Cycle
Pull latest changes (if collaborating):

bash
git pull origin main
Create a feature branch (optional but good practice):

bash
git checkout -b feature/add-sla-dashboard
Make changes and commit:

bash
git add .
git commit -m "Add SLA dashboard with charts"
Push the branch:

bash
git push -u origin feature/add-sla-dashboard
Open a Pull/Merge Request on GitHub/GitLab for review.

Ignoring Local Changes Temporarily
If you have local changes you don’t want to commit (e.g., debugging prints), you can stash them:

bash
git stash
# ... do something else ...
git stash pop

## 8. Important Considerations for Django Projects

Never commit .env or any file containing secrets. Use .env.example as a template.

Do not commit the database file (db.sqlite3) if you use SQLite – it’s excluded above.

Migrations can be committed – this helps other developers replicate your database schema.

Media files (user uploads) should never be committed. They are excluded.

Static files collected by collectstatic are excluded; only source CSS/JS should be tracked.

## 9. Verify Your Repository

Check the commit history:

bash
git log --oneline

## 10. Next Steps (Optional)

Set up branch protection rules on GitHub if collaborating (require pull requests before merging to main).

Consider using Git hooks (e.g., pre‑commit) to run linting or tests automatically.

Use Git tags to mark releases (e.g., v1.0.0):

bash
git tag -a v1.0.0 -m "First stable release"
git push origin v1.0.0

📦 1. Commit
A commit is a snapshot of your project’s files at a specific point in time.

It saves your changes permanently in the local Git history.

Each commit has a unique ID (hash) and a message describing what changed.

You commit after staging files (git add).

Example:

bash
git add backend/core/settings.py
git commit -m "Fix logging permission issue"
When to commit:

You have finished a logical piece of work.

You want to share your changes with others (via git push).

🗃️ 2. Stash
A stash temporarily saves your uncommitted changes (both staged and unstaged) and reverts your working directory to the last commit.

It’s like a “shelf” where you put aside modifications without committing them.

Useful when you need to switch branches or pull updates but are not ready to commit.

Example:

bash
git stash               # saves changes and cleans working directory
git pull origin main    # now works without conflicts
git stash pop           # reapplies your stashed changes
When to stash:

You have local modifications that you don’t want to commit yet, but you need to update your branch (e.g., git pull).

You want to test something on a clean state without losing your work.

🔀 3. Merge
A merge combines changes from two different branches into one.

When you git pull, it fetches remote changes and merges them into your current branch.

If there are conflicting changes (both branches modified the same lines), Git will mark conflicts for you to resolve manually.

Example:

bash
git checkout main
git merge feature-branch    # merges feature-branch into main
When to merge:

You want to integrate work from another branch (e.g., after a pull request).

You update your local branch with remote changes (via git pull which does fetch + merge).

🔄 How they work together (common scenario)
You have uncommitted changes on your VPS (e.g., you edited settings.py). You want to pull the latest code from GitHub without losing your modifications.

Step‑by‑step:
Stash your local changes (temporarily remove them):

bash
git stash
Pull remote changes (fetch and merge):

bash
git pull origin main
This will update your branch with the latest commits from GitHub.

Re‑apply your stashed changes (restore your local modifications):

bash
git stash pop
If there are conflicts (e.g., the same file was changed both locally and remotely), Git will pause and ask you to resolve them. You edit the conflicting file, then git add it and continue.

If you are satisfied with the result, you can commit your merged work (including your local changes) or keep them unstaged for further editing.

If you don't need your local changes anymore, you can discard the stash instead of popping it:

bash
git stash drop
⚠️ Important notes
Commit is permanent; stash is temporary.

Merge can create a new commit (merge commit) if the branches diverged.

To avoid conflicts, always stash or commit your local changes before pulling.

If you have committed changes locally and then pull, Git will attempt to merge automatically. If there are conflicts, you resolve them and then commit the merge.

🎯 Your situation on the VPS
You have a local modification (commented logging handler).

You want to pull new code from GitHub without losing that change.

Solution:

bash
git stash
git pull origin main
git stash pop
If a conflict arises (unlikely for just a comment change), resolve it, then git add and git stash drop (or continue working).

If you never want to lose that logging change, consider making it permanent by committing it (after fixing the log path to a writable location) – then you won't need to stash it every time.

Let me know if you'd like a visual diagram or more examples!

yes, give me a visual diagram as I need a clear understanding of git commands
We need to produce a visual diagram explaining Git commands: commit, stash, merge, and how they interact. The user requested a "visual diagram" – likely a text-based diagram (ASCII art) or a description of a diagram. Since this is a text interface, we can create an ASCII flowchart or a step-by-step visual representation. We'll also include the scenario of pulling remote changes while having local uncommitted changes, using stash.

We'll produce a clear ASCII diagram showing the flow of working directory, staging area, local repo, remote repo, and the operations. Also show stash as a temporary storage.

Let's create a diagram and explanation.

I'll provide a text-based diagram (ASCII art) to help you visualize how commit, stash, and merge work together, especially when you have local changes and need to pull updates from a remote repository.

🖼️ Visual Diagram: Git Workflow with Stash & Merge
text
          ┌─────────────────────────────────────────────────────────────┐
          │                       REMOTE REPOSITORY                     │
          │                      (e.g., GitHub, origin)                 │
          │                                                             │
          │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐    │
          │   │ Commit A│──▶│ Commit B│──▶│ Commit C│──▶│ Commit D│    │
          │   └─────────┘   └─────────┘   └─────────┘   └─────────┘    │
          │        ▲                           ▲                        │
          └────────┼───────────────────────────┼────────────────────────┘
                   │                           │
                   │ git fetch / pull          │ git push
                   │ (merge remote changes)    │ (send local commits)
                   │                           │
          ┌────────┼───────────────────────────┼────────────────────────┐
          │        │                           │                        │
          │   ┌────▼────┐                 ┌─────▼─────┐                  │
          │   │  Local  │                 │  Local    │                  │
          │   │  Commits│                 │  Commits  │                  │
          │   │ (main)  │                 │  (main)   │                  │
          │   └────┬────┘                 └─────┬─────┘                  │
          │        │                            │                        │
          │        │ git merge                  │ git commit             │
          │        │ (merge branches)           │ (save staged changes)  │
          │        ▼                            ▼                        │
          │   ┌─────────────────────────────────────┐                    │
          │   │           LOCAL REPOSITORY           │                    │
          │   │         (stored in .git folder)      │                    │
          │   └─────────────────────────────────────┘                    │
          │                    ▲                                          │
          │                    │ git add                                 │
          │                    │ (stage changes)                         │
          │                    │                                          │
          │   ┌────────────────┴────────────────┐                       │
          │   │          STAGING AREA            │                       │
          │   │    (changes ready to commit)     │                       │
          │   └────────────────┬────────────────┘                       │
          │                    │                                          │
          │                    │ git stash                               │
          │                    │ (temporarily save uncommitted changes)  │
          │                    ▼                                          │
          │   ┌─────────────────────────────────────┐                    │
          │   │               STASH                 │                    │
          │   │   (temporary storage – stack)       │                    │
          │   │    stash@{0}: changes on main       │                    │
          │   │    stash@{1}: earlier changes       │                    │
          │   └────────────────┬────────────────────┘                    │
          │                    │                                          │
          │                    │ git stash pop / apply                   │
          │                    │ (restore changes to working dir)        │
          │                    ▼                                          │
          │   ┌─────────────────────────────────────┐                    │
          │   │          WORKING DIRECTORY          │                    │
          │   │      (your actual files on disk)    │                    │
          │   └─────────────────────────────────────┘                    │
          │                                                             │
          └─────────────────────────────────────────────────────────────┘
🔄 Step‑by‑step flow with stash + merge (common scenario)
You have uncommitted changes in your working directory (e.g., edited settings.py).

You need to pull the latest updates from the remote branch (e.g., git pull origin main).

Without stash: Git refuses because it would overwrite your local changes.

You run git stash – this moves your uncommitted changes to the stash stack, cleaning your working directory.

Now git pull origin main works – it fetches remote commits and merges them into your local branch (fast‑forward or creates a merge commit).

You run git stash pop – this applies the stashed changes back to your working directory.

If there are no conflicts, the changes are restored and the stash is removed.

If there are conflicts (both remote and your stash changed the same lines), Git pauses; you resolve conflicts manually, then git add and git stash drop (or git stash pop again).

You can now commit your merged work (including the restored changes) or continue editing.

📦 Commit – Stash – Merge: Quick Definitions
Command	Purpose	Effect on history	When to use
git commit	Save staged changes permanently	Creates a new commit (snapshot)	After finishing a logical unit of work
git stash	Temporarily shelve uncommitted changes	No commit; changes go to a stack	Before pulling/switching branches when you're not ready to commit
git merge	Combine two branches	Creates a merge commit (unless fast‑forward)	After fetching remote changes, or when integrating a feature branch
🧪 Practical example with commands
bash
# 1. You have uncommitted changes
echo "debug = True" >> settings.py
git status          # shows modified: settings.py

# 2. Stash them
git stash           # saves changes, working directory clean

# 3. Pull remote updates
git pull origin main   # fetches and merges remote commits

# 4. Apply stash back
git stash pop        # restores changes, may conflict

# 5. If conflict occurs, resolve, then:
git add settings.py
git stash drop       # remove the stash after successful pop

# 6. Commit the merged result (including your changes)
git commit -m "Merge remote changes and keep my settings"
🧠 Key points to remember
Stash is a temporary shelf – it's not a commit. Don't rely on it for long‑term storage.

Merge creates a commit that ties together two lines of development.

Always stash or commit before pulling to avoid merge conflicts caused by uncommitted changes.

If you have committed changes locally and then pull, Git will attempt to merge automatically; you may still need to resolve conflicts, but you won't need stash.

I hope this visual + explanation clears up how these Git operations work together! Let me know if you'd like a more detailed diagram or specific examples.

