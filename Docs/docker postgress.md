# switch to postgres superuser and open psql
sudo -u postgres psql

# inside psql, run these commands:
# become the postgres superuser
    sudo -u postgres psql <<'SQL'
    -- set a password that matches your .env
    ALTER USER postgres WITH PASSWORD 'postgres';

    -- create the project database if you haven’t yet
    CREATE DATABASE "omnichannel-cms" OWNER postgres;
    \q

    PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d "omnichannel-cms" -c '\l'

Once that’s done, your .env already points at port 5433 – change it to
5432 or leave it and update the port:

    DB_HOST=localhost
    DB_PORT=5432          # or 5433 if you adjust postgres.conf accordingly

    # confirm listening
    grep -E 'listen_addresses|port' /etc/postgresql/16/main/postgresql.conf

    # restart to pick up changes
    sudo service postgresql restart


    To access PostgreSQL on your local machine (WSL/Ubuntu), you need to have PostgreSQL installed and running locally. Here’s how to set it up and connect.

🐘 1. Install PostgreSQL locally (if not already installed)
bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
Start the service:

bash
sudo service postgresql start
Check status:

bash
sudo service postgresql status
🔑 2. Switch to the postgres system user
bash
sudo -u postgres psql
This will open the PostgreSQL command line interface (CLI) as the superuser.

🛠️ 3. Common local psql commands
List all databases: \l

Connect to a database: \c database_name

List tables in current database: \dt

Quit: \q

🔐 4. If you need to connect as your own user (e.g., lareef)
First, create a PostgreSQL user with the same name as your Ubuntu user (if not already present):

bash
sudo -u postgres createuser --createdb --login --superuser lareef
Then set a password (optional):

bash
sudo -u postgres psql -c "ALTER USER lareef WITH PASSWORD 'yourpassword';"
Now you can connect without sudo:

bash
psql -d postgres -U lareef
Or connect directly to the omnichannel database:

bash
psql -d omnichannel -U lareef
🧪 5. Test the connection for your project
Your local Django settings likely have:

python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'omnichannel',
        'USER': 'postgres',   # or 'lareef'
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
To verify you can connect with those credentials:

bash
psql -h localhost -U postgres -d omnichannel
Enter the password (postgres if default). If it connects, you’re good.

🐳 Note about Docker
If you have PostgreSQL running inside Docker, you can still access it from your local machine using localhost as the host (provided the container’s port 5432 is mapped to the host). In that case, the commands above work as well, but you don’t need to install PostgreSQL locally.

📌 For the migration fix earlier, we used the Docker container’s psql. To replicate that locally, you would run:
bash
docker-compose exec db psql -U postgres -d omnichannel
That’s the simplest if you already have Docker running.

Let me know if you need help with any specific local PostgreSQL operation.