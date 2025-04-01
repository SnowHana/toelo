Get a datafile...

---

This is a new repo. My old repo (footy) was abandoned cuz data file was too big, and it often lead to a lot of unexpected errors.

---

## Data set

Download and place the data files from
google drive link
https://drive.google.com/drive/folders/1x_R1GlTMJKeo9CTACmffRorAjfjSmxy8?usp=drive_link

and place it to
~/toelo/footy/src/data

## Setting up postgresql

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
