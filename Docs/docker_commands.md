# Start containers
docker-compose up -d

# Check status  
docker-compose ps

# View logs
docker-compose logs

# Stop containers
docker-compose down

📋 Summary: Docker Service Startup
Why Containers Went Down:
When you quit Docker Desktop, the WSL2 Docker integration stops immediately. Since Docker doesn't run natively in WSL2 (it relies on Docker Desktop's Windows daemon), all containers go offline.

How to Fix (Right Now):
Step 1: Open Docker Desktop on Windows

Look for Docker icon in taskbar
Or search Windows for "Docker Desktop"
Wait for it to reach "Docker Desktop is running" status
Step 2: Once Docker Desktop is running, restart containers:

✅ Good News - Already Configured:
Your docker-compose.yml has restart: unless-stopped on all services, which means:

Containers auto-restart if they crash
Containers auto-restart when Docker restarts
No manual restart needed after reboots (once Docker is running)
Permanent Solution for System Boot:
I've created a detailed guide at DOCKER_STARTUP_GUIDE.md that includes instructions to make Docker Desktop launch automatically when Windows boots.

Daily Workflow:
After system restart: Open Docker Desktop (one-time manual action)
Containers start automatically via restart policies
Your app is ready at http://localhost:8000
The key takeaway: Just keep Docker Desktop running - your containers handle the rest! 🚀

# project_startup_ins.md

docker compose up web-dev
docker compose --profile dev up web-dev
docker compose --profile dev up
docker compose down
docker compose up
docker compose restart
docker compose restart web # individual service
docker compose ps

docker compose build --no-cache

-- create the superuser (inside container)
docker compose --profile dev down createsuperuser

--  list web log
docker exec -it omnichannel_web sh


docker-compose logs -f celery_beat

docker compose exec db psql -U omniuser -d omnichannel

$ docker exec -it omnichannel_web bash

listing files
$ ls -l

changing ownership
$ sudo chown -R $USER:$USER . #  current user
$ sudo chown -R lareef:laraef . #  similar
$ sudo chown -R $(whoami):$(whoami) . # more safer
$ sudo chown -R $(whoami):$(whoami) public static templates # with directory
$ chmod -R 775 .

Get shell
docker exec -it omnichannel_cms_web python manage.py shell

from ticket.models import Ticket
from django.forms.models import model_to_dict

listing all objects
>>> for ticket in Ticket.objects.all(): print('\n'.join(f"{key}: {value}" for key, value in model_to_dict(ticket).items())); print('---')

list the first() object
>>> print('\n'.join(f"{k}: {v}" for k, v in Ticket.objects.first().__dict__.items() if not k.startswith('_')))


