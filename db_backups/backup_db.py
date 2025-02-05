#backup_db.py

import psycopg2

# Define the database connection parameters
host = 'localhost'
database = 'ng_news'
username = 'postgres'
password = 'naija1'

# Create a connection to the database
conn = psycopg2.connect(
    host=host,
    database=database,
    user=username,
    password=password
)

# Create a cursor object
cur = conn.cursor()

# Dump the database data to a file
with open('backup.sql', 'w') as f:
    cur.execute('SELECT * FROM pg_catalog.pg_tables WHERE schemaname != \'pg_catalog\' AND schemaname != \'information_schema\';')
    tables = cur.fetchall()
    for table in tables:
        cur.execute(f'SELECT * FROM {table[1]};')
        rows = cur.fetchall()
        for row in rows:
            f.write(f'INSERT INTO {table[1]} VALUES (')
            for value in row:
                f.write(f"'{value}', ")
            f.write(');\n')

# Close the cursor and connection
cur.close()
conn.close()