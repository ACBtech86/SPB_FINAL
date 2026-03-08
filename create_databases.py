"""Create PostgreSQL databases for SPB system."""
import psycopg2

# Connect to default 'postgres' database
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='Rama1248',
    database='postgres'
)
conn.autocommit = True
cur = conn.cursor()

# Create databases
try:
    cur.execute('CREATE DATABASE "BCSPB"')
    print('[OK] Database BCSPB created')
except psycopg2.errors.DuplicateDatabase:
    print('[OK] Database BCSPB already exists')

try:
    cur.execute('CREATE DATABASE "BCSPBSTR"')
    print('[OK] Database BCSPBSTR created')
except psycopg2.errors.DuplicateDatabase:
    print('[OK] Database BCSPBSTR already exists')

conn.close()
print('\n[OK] Done! Databases are ready.')
