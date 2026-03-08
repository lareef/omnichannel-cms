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