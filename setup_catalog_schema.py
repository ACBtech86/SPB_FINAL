"""Create catalog tables and views in PostgreSQL BCSPBSTR database."""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='Rama1248',
    database='BCSPBSTR'
)
conn.autocommit = True
cur = conn.cursor()

print('Setting up catalog schema...\n')

# Create SPB_MENSAGEM table
print('[1/6] Creating SPB_MENSAGEM table...')
cur.execute('''
CREATE TABLE IF NOT EXISTS SPB_MENSAGEM (
    MSG_ID VARCHAR(50) PRIMARY KEY,
    MSG_DESCR VARCHAR(500)
)
''')

# Create SPB_DICIONARIO table
print('[2/6] Creating SPB_DICIONARIO table...')
cur.execute('''
CREATE TABLE IF NOT EXISTS SPB_DICIONARIO (
    MSG_CPOTAG VARCHAR(100) PRIMARY KEY,
    MSG_CPOTIPO VARCHAR(50),
    MSG_CPOTAM VARCHAR(20),
    MSG_CPOFORM VARCHAR(50)
)
''')

# Create SPB_MSGFIELD table
print('[3/6] Creating SPB_MSGFIELD table...')
cur.execute('''
CREATE TABLE IF NOT EXISTS SPB_MSGFIELD (
    COD_GRADE VARCHAR(50),
    MSG_ID VARCHAR(50),
    MSG_TAG VARCHAR(100),
    MSG_DESCR VARCHAR(500),
    MSG_EMISSOR VARCHAR(100),
    MSG_DESTINATARIO VARCHAR(100),
    MSG_SEQ INTEGER,
    MSG_CPOTAG VARCHAR(100),
    MSG_CPONOME VARCHAR(200),
    MSG_CPOOBRIG VARCHAR(10),
    PRIMARY KEY (COD_GRADE, MSG_ID, MSG_SEQ)
)
''')

# Drop old tables/views created by seed.py
print('[4/6] Dropping old views/tables...')
cur.execute('DROP TABLE IF EXISTS spb_mensagem_view CASCADE')
cur.execute('DROP TABLE IF EXISTS spb_dicionario_view CASCADE')
cur.execute('DROP TABLE IF EXISTS spb_msgfield_view CASCADE')

# Create views for SPBSite compatibility
print('[5/6] Creating spb_mensagem_view...')
cur.execute('''
CREATE VIEW spb_mensagem_view AS
SELECT MSG_ID as msg_id, MSG_DESCR as msg_descr
FROM SPB_MENSAGEM
''')

print('[6/6] Creating spb_dicionario_view...')
cur.execute('''
CREATE VIEW spb_dicionario_view AS
SELECT MSG_CPOTAG as msg_cpotag, MSG_CPOTIPO as msg_cpotipo,
       MSG_CPOTAM as msg_cpotam, MSG_CPOFORM as msg_cpoform
FROM SPB_DICIONARIO
''')

print('[7/6] Creating spb_msgfield_view...')
cur.execute('''
CREATE VIEW spb_msgfield_view AS
SELECT
    ROW_NUMBER() OVER (ORDER BY COD_GRADE, MSG_ID, MSG_SEQ) as id,
    COD_GRADE as cod_grade,
    MSG_ID as msg_id,
    MSG_TAG as msg_tag,
    MSG_DESCR as msg_descr,
    MSG_EMISSOR as msg_emissor,
    MSG_DESTINATARIO as msg_destinatario,
    MSG_SEQ as msg_seq,
    MSG_CPOTAG as msg_cpotag,
    MSG_CPONOME as msg_cponome,
    MSG_CPOOBRIG as msg_cpoobrig
FROM SPB_MSGFIELD
''')

conn.close()
print('\n[OK] Catalog schema created successfully!')
