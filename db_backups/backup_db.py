#backup_db.py
import gzip
import psycopg2

# Database connection parameters (adjust as needed)
host = 'localhost'
database = 'ng_news'
username = 'postgres'
password = 'naija1'
port = 5432

conn = psycopg2.connect(
    host=host,
    port=port,
    database=database,
    user=username,
    password=password
)

# Create a cursor object
cur = conn.cursor()

# Dump the database data to a compressed file
with gzip.open('backup.sql.gz', 'wt') as f:
    cur.execute("SELECT * FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';")
    tables = cur.fetchall()
    for table in tables:
        table_name = table[1]
        cur.execute(f'SELECT * FROM {table_name};')
        rows = cur.fetchall()
        for row in rows:
            f.write(f'INSERT INTO {table_name} VALUES (')
            f.write(', '.join(f"'{value}'" for value in row))
            f.write(');\n')

# Close the cursor and connection
cur.close()
conn.close()