"""Migrate message catalog from SQLite to PostgreSQL."""
import sqlite3
import psycopg2

# Connect to SQLite source
sqlite_conn = sqlite3.connect(r'Carga_Mensageria\BCSPBSTR.db')
sqlite_cur = sqlite_conn.cursor()

# Connect to PostgreSQL target
pg_conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='Rama1248',
    database='BCSPBSTR'
)
pg_conn.autocommit = False
pg_cur = pg_conn.cursor()

print('Migrating catalog data from SQLite to PostgreSQL...\n')

# Clear existing data in PostgreSQL (in reverse FK order)
print('[1/3] Clearing existing data...')
pg_cur.execute('DELETE FROM SPB_MSGFIELD')
pg_cur.execute('DELETE FROM SPB_DICIONARIO')
pg_cur.execute('DELETE FROM SPB_MENSAGEM')
pg_conn.commit()

# Migrate SPB_MENSAGEM
print('[2/4] Migrating SPB_MENSAGEM...')
sqlite_cur.execute('SELECT MSG_ID, MSG_DESCR FROM SPB_MENSAGEM')
count = 0
for row in sqlite_cur.fetchall():
    pg_cur.execute(
        'INSERT INTO SPB_MENSAGEM (MSG_ID, MSG_DESCR) VALUES (%s, %s) '
        'ON CONFLICT (MSG_ID) DO NOTHING',
        row
    )
    count += 1
pg_conn.commit()
print(f'   Migrated {count} messages')

# Migrate SPB_DICIONARIO
print('[3/4] Migrating SPB_DICIONARIO...')
sqlite_cur.execute('''
    SELECT MSG_CPOTAG, MSG_CPOTIPO, MSG_CPOTAM, COALESCE(MSG_CPOFORMATO, '')
    FROM SPB_DICIONARIO
''')
count = 0
for row in sqlite_cur.fetchall():
    pg_cur.execute(
        'INSERT INTO SPB_DICIONARIO (MSG_CPOTAG, MSG_CPOTIPO, MSG_CPOTAM, MSG_CPOFORM) '
        'VALUES (%s, %s, %s, %s) ON CONFLICT (MSG_CPOTAG) DO NOTHING',
        row
    )
    count += 1
pg_conn.commit()
print(f'   Migrated {count} dictionary entries')

# Migrate SPB_MSGFIELD (assign grade based on message ID)
print('[4/4] Migrating SPB_MSGFIELD...')
sqlite_cur.execute('''
    SELECT MSG_ID, MSG_TAG, MSG_DESCR, MSG_EMISSOR, MSG_DESTINATARIO,
           MSG_SEQ, MSG_CPOTAG, MSG_CPONOME, MSG_CPOOBRIG
    FROM SPB_MSGFIELD
''')
count = 0
for row in sqlite_cur.fetchall():
    # Determine grade based on message ID prefix
    msg_id = row[0]
    if msg_id and msg_id.startswith('SEL'):
        cod_grade = 'SEL01'
    else:
        cod_grade = 'BCN01'

    pg_cur.execute(
        '''INSERT INTO SPB_MSGFIELD
           (COD_GRADE, MSG_ID, MSG_TAG, MSG_DESCR, MSG_EMISSOR, MSG_DESTINATARIO,
            MSG_SEQ, MSG_CPOTAG, MSG_CPONOME, MSG_CPOOBRIG)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (COD_GRADE, MSG_ID, MSG_SEQ) DO NOTHING''',
        (cod_grade, *row)
    )
    count += 1
pg_conn.commit()
print(f'   Migrated {count} field definitions')

# Close connections
sqlite_conn.close()
pg_conn.close()

print('\n[OK] Migration completed successfully!')
