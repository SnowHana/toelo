Get a datafile...

---

This is a new repo. My old repo (footy) was abandoned cuz data file was too big, and it often lead to a lot of unexpected errors.

---

# Data and DB

## Data set

Download and place the data files from
google drive link
https://drive.google.com/drive/folders/1x_R1GlTMJKeo9CTACmffRorAjfjSmxy8?usp=drive_link

and place it to
~/data/

## DB

### Creating a dump / sql file

there is a postgre database file in ~/football.dump (or footall.sql)

```bash
pg_dump -U your_username -h localhost your_db_name > your_dump_file.sql

OR

pg_dump -U your_username -h localhost -F c -f your_dump_file.dump your_db_name
```

Replace your_db_name to football

### Create a database based on above file

1. Create a database

```bash
createdb -U your_username new_db_name

OR

CREATE DATABASE new_db_name;
```

2. Restore the dump file

```bash
psql -U your_username -d new_db_name -f your_dump_file.sql

OR

pg_restore -U your_username -d new_db_name your_dump_file.dump

```

If this doesnt work do

```bash
sudo -u postgres pg_dump -d football -f /tmp/football.sql

AND

sudo mv /tmp/football.sql .

```

And zip it

```bash
gzip > football.sql.gz
```

Unzip

```bash
gunzip -c football.sql.gz | psql -U postgres -d football
```

Make sure to
🔒 Don’t Forget:

You may need to allow trust or password login in pg_hba.conf or use --password if needed.

Use the same PostgreSQL version or a compatible one on both machines to avoid restore errors.

### Setting up postgresql

```python
DATABASE_CONFIG = {
"dbname": "football",
"user": "postgres",
"password": "1234",
"host": "localhost",
"port": "5432",
}
```

You have to create a user and database accordingly...
