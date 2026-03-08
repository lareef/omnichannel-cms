# Docker Service Startup Guide

## Problem
When Docker Desktop is quit on Windows, the WSL2 Docker integration stops, and containers go down.

## Solution: Restart Docker Desktop

### Step 1: Start Docker Desktop
1. Open **Docker Desktop** application on Windows
2. Wait for it to fully start (may take 1-2 minutes)
3. You'll see "Docker Desktop is starting..." → "Docker Desktop is running"

### Step 2: Restart Your Containers
Once Docker Desktop is running, restart your containers:

```bash
# Start all containers in the background
docker-compose up -d

# Verify they're running
docker-compose ps
```

### Step 3: Access Your Application
- **Web Application**: http://localhost:8000
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6379

## Auto-Restart Configuration

Your `docker-compose.yml` already includes:
```yaml
restart: unless-stopped
```

This means:
- ✅ Containers restart automatically if they crash
- ✅ Containers restart when Docker daemon restarts
- ✅ Only stops if you explicitly run `docker-compose down`

## Daily Workflow

### Morning (after system restart):
```bash
# 1. Open Docker Desktop on Windows (one-time per boot)
# 2. Once it starts, containers will begin restarting automatically
# 3. Verify they're ready:
docker-compose ps

# 4. If needed manually start:
docker-compose up -d
```

### View Logs:
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web
docker-compose logs celery_worker

# Follow logs in real-time
docker-compose logs -f web
```

### Stop Services:
```bash
# Stop all containers
docker-compose down

# Note: With restart: unless-stopped, this is the only way
# to permanently stop containers
```

## Troubleshooting

### Docker not found error:
```bash
# This means Docker Desktop is not running on Windows
# Solution: Open Docker Desktop application
```

### Containers not starting:
```bash
# Check if Docker is running
docker version

# Check container status
docker-compose ps

# View error logs
docker-compose logs --tail=50
```

### Need to rebuild (after code changes):
```bash
docker-compose down
docker-compose up --build -d
```

## Key Commands Reference

| Command | Result |
|---------|--------|
| `docker-compose up -d` | Start all containers in background |
| `docker-compose down` | Stop all containers |
| `docker-compose ps` | Show container status |
| `docker-compose logs` | View all logs |
| `docker-compose logs web` | View specific service logs |
| `docker-compose restart web` | Restart single service |
| `docker-compose up --build -d` | Rebuild and start |

## Windows Startup Automation (Optional)

To make Docker Desktop start automatically when Windows boots:

1. **Create a Windows Task Scheduler task**:
   - Windows Key + `taskschd.msc`
   - Create Basic Task
   - Set trigger: "At startup"
   - Set action: Start `C:\Program Files\Docker\Docker\Docker Desktop.exe`

2. **Or use Windows Startup folder**:
   - Press `Windows Key + R`
   - Type: `shell:startup`
   - Create shortcut to Docker Desktop.exe

This way Docker starts automatically, and your containers will boot with it!

## Final Note

Your omnichannel CMS is fully configured for automatic recovery:
- ✅ Containers have `restart: unless-stopped`
- ✅ Health checks are in place
- ✅ Proper dependency ordering
- ✅ Environment configuration is separate

Just ensure Docker Desktop is running on Windows, and your system will be ready! 🚀
