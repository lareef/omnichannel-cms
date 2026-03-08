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
docker exec -it omnichannel_web_dev python manage.py shell

from ticket.models import Ticket
from django.forms.models import model_to_dict

listing all objects
>>> for ticket in Ticket.objects.all(): print('\n'.join(f"{key}: {value}" for key, value in model_to_dict(ticket).items())); print('---')

list the first() object
>>> print('\n'.join(f"{k}: {v}" for k, v in Ticket.objects.first().__dict__.items() if not k.startswith('_')))


Below is a step‑by‑step guide to set up a local development environment for your Omnichannel Complaint Management System on Windows WSL (Ubuntu 24.04) using Docker, Django 5.2, PostgreSQL, Redis, Celery, Tailwind CSS, and HTMX. This setup follows the model architecture we designed and includes placeholders for RBAC, SLA engine, and escalation logic that you can implement later.

1. Prerequisites
Ensure you have the following installed on your Windows machine:

Windows Subsystem for Linux (WSL2) with Ubuntu 24.04
Installation guide

Docker Desktop (with WSL2 backend enabled)
Download Docker Desktop

Git (optional, but recommended)

VS Code (or your preferred editor) with the Remote – WSL extension

Inside your WSL Ubuntu terminal, verify Docker is available:

bash
docker --version
docker-compose --version
2. Project Directory & Initial Files
Create a project folder and navigate into it:

bash
mkdir omnichannel-cms
cd omnichannel-cms
We’ll create the following structure (explained step by step):

text
omnichannel-cms/
├── docker-compose.yml
├── .env
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── core/               # Django project folder
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── celery.py
│   └── apps/                # All Django apps
│       ├── accounts/
│       ├── customers/
│       ├── products/
│       ├── tickets/
│       ├── public/
│       ├── integration/
│       ├── notifications/
│       └── analytics/
├── frontend/                 # For Tailwind (if using standalone)
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/input.css
└── scripts/                  # Helper scripts
3. Docker Compose Configuration
Create a docker-compose.yml file in the project root:

yaml
version: '3.8'

services:
  db:
    image: postgres:15
    container_name: omnichannel_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: omnichannel_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: omnichannel_web
    restart: unless-stopped
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: omnichannel_celery_worker
    restart: unless-stopped
    command: celery -A core worker --loglevel=info
    volumes:
      - ./backend:/app
    env_file:
      - .env
    depends_on:
      - redis
      - web

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: omnichannel_celery_beat
    restart: unless-stopped
    command: celery -A core beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - ./backend:/app
    env_file:
      - .env
    depends_on:
      - redis
      - web

volumes:
  postgres_data:
  redis_data:
4. Environment Variables
Create a .env.example file (copy to .env for actual values):

bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=omnichannel
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Email (for notifications – optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
Copy .env.example to .env and adjust as needed.

5. Backend Dockerfile
Create backend/Dockerfile:

dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1 \
    # If using pip requirements instead of poetry
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies (for psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user (optional)
RUN adduser --disabled-password --gecos '' appuser
USER appuser
6. Python Dependencies
Create backend/requirements.txt with all necessary packages:

text
Django==5.2
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.6
django-celery-beat==2.6.0
django-celery-results==2.5.1
django-environ==0.11.2
django-extensions==3.2.3
django-allauth==0.61.1          # For social auth if needed
django-auditlog==3.0.0           # Audit trail
django-htmx==1.17.0              # HTMX helpers
django-tailwind-cli==1.3.0       # Tailwind integration (alternative: django-tailwind)
django-debug-toolbar==4.3.0      # Development only
django-storages==1.14.2           # For file storage (if using S3 etc.)
gunicorn==21.2.0                  # Production WSGI
Note: We’ll use django-tailwind-cli for easy Tailwind integration. It runs the Tailwind CLI without Node.js. Alternatively, you can use the traditional django-tailwind which requires Node. We'll show the simpler django-tailwind-cli approach.

7. Django Project & Apps
Now let’s create the Django project and the required apps.

Inside the backend directory, run:

bash
cd backend
django-admin startproject core .
Then create the apps (we’ll use the models we designed earlier):

bash
python manage.py startapp accounts
python manage.py startapp customers
python manage.py startapp products
python manage.py startapp tickets
python manage.py startapp public
python manage.py startapp integration
python manage.py startapp notifications
python manage.py startapp analytics
Now copy the model code from the previous answer into the respective models.py files. (You can do this manually or create the files now and paste later.)

Make sure to adjust imports across apps – e.g., in tickets/models.py you’ll need to import from accounts, customers, etc. Use string references for ForeignKeys to avoid circular imports.

8. Django Settings (core/settings.py)
We’ll configure the settings to use environment variables, connect to PostgreSQL, set up Celery, and include all apps.

Key parts of settings.py:

python
import os
from pathlib import Path
import environ

env = environ.Env()
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent, '.env'))

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'django_extensions',
    'django_htmx',
    'tailwind_cli',                     # django-tailwind-cli
    'debug_toolbar',                     # local development only
    'auditlog',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_celery_beat',
    'django_celery_results',
    # Local apps
    'accounts',
    'customers',
    'products',
    'tickets',
    'public',
    'integration',
    'notifications',
    'analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # local
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',            # HTMX
    'auditlog.middleware.AuditlogMiddleware',           # Auditlog
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [...]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Tailwind CLI (django-tailwind-cli)
TAILWIND_CLI_PATH = BASE_DIR / 'static' / 'css'   # where output.css will be placed
TAILWIND_CLI_CONFIG_FILE = BASE_DIR.parent / 'frontend' / 'tailwind.config.js'
TAILWIND_CLI_SRC_CSS = BASE_DIR.parent / 'frontend' / 'src' / 'input.css'

# Celery
CELERY_BROKER_URL = env('REDIS_URL')
CELERY_RESULT_BACKEND = 'django-db'  # use django-celery-results
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Django Debug Toolbar (local only)
INTERNAL_IPS = ['127.0.0.1']

# django-allauth configuration (if used)
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Any other settings...
9. Celery Configuration
Create core/celery.py:

python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
In core/__init__.py add:

python
from .celery import app as celery_app

__all__ = ('celery_app',)
10. Tailwind CSS Setup
We’ll use the standalone Tailwind CLI via the django-tailwind-cli package, which downloads the binary automatically. Create the required files in the frontend/ folder (outside backend):

bash
mkdir -p frontend/src
Create frontend/tailwind.config.js:

js
module.exports = {
  content: [
    '../backend/**/*.{html,js,py}',   // scan all Django templates and Python files for classes
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
Create frontend/src/input.css with the Tailwind directives:

css
@tailwind base;
@tailwind components;
@tailwind utilities;
Now, when you run python manage.py tailwind build, the CLI will generate static/css/output.css. Include this in your base template:

html
<link href="{% static 'css/output.css' %}" rel="stylesheet">
11. HTMX Integration
Add the HTMX script to your base template. You can either download it or use a CDN:

html
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
The django-htmx middleware we added provides handy utilities (e.g., request.htmx).

12. Initial Migrations & Superuser
With everything in place, build and start the containers:

bash
docker-compose up --build
In another terminal, run migrations (they run automatically on start, but you can also do manually):

bash
docker-compose exec web python manage.py migrate
Create a superuser:

bash
docker-compose exec web python manage.py createsuperuser
If you need to generate the Tailwind CSS:

bash
docker-compose exec web python manage.py tailwind build
You may want to run the Tailwind build process in watch mode during development. You can add a separate service in docker-compose for that, or run it locally if you have Node installed. For simplicity, we’ll just build it once and re‑build when needed.

13. Implementing RBAC, SLA Engine & Escalation (Outline)
Your models already support RBAC via Role, Department, and Django’s built‑in permissions. You can:

Assign permissions to groups or roles.

Use @permission_required decorators or mixins in views.

Restrict access at the queryset level using the department and assigned_to fields.

For SLA engine:

Write a Celery periodic task (using django-celery-beat) that runs every minute and checks tickets where response_due_at or resolution_due_at is in the past but not yet met, updating the is_response_breached / is_resolution_breached flags.

Another task can evaluate escalation policies: if a ticket is breached and escalation rules apply, create a TicketEscalation record and optionally notify supervisors.

Example task skeleton:

python
# tickets/tasks.py
from celery import shared_task
from .models import Ticket

@shared_task
def check_sla_breaches():
    # Logic to find tickets with passed due dates
    ...
Schedule it via the Django admin (django_celery_beat).

14. Access the Application
Django app: http://localhost:8000

Admin interface: http://localhost:8000/admin

PostgreSQL: localhost:5432

Redis: localhost:6379

15. Useful Development Commands
Rebuild containers after dependency changes: docker-compose up --build

View logs: docker-compose logs -f [service]

Enter the web container: docker-compose exec web bash

Run Django management commands: docker-compose exec web python manage.py <command>

Stop all containers: docker-compose down

Stop and remove volumes (reset DB): docker-compose down -v

Next Steps
Implement the actual views, templates, and business logic for complaint submission, agent dashboard, etc.

Configure authentication with django-allauth (social logins for customers) if needed.

Set up notifications using Celery to send emails/WhatsApp messages.

Integrate with ERP using the Outbox model and a periodic task that processes pending outbox records.

Develop the AI pipeline: start collecting labelled data and later train models.

Final Notes
This setup is fully containerised, making it easy to share and deploy.

The use of environment variables keeps secrets out of the code.

Tailwind and HTMX give you a modern frontend without a separate Node.js build step (thanks to django-tailwind-cli).

Celery Beat is configured with the database scheduler so you can manage periodic tasks through the Django admin.

Your enterprise‑grade Omnichannel Complaint Management System is now ready for development! If you encounter any issues during setup, feel free to ask for clarification.