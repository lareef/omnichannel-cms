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