#!/usr/bin/env python3
"""
Insert test messages into the PostgreSQL database.

This simulates the "local institution" (IF) side: inserting records into
spb_local_to_bacen with flag_proc='P' (pending), which the IFReq task
will pick up and send via MQ.

Usage:
    python test_db_insert.py [--count N]

Prerequisites:
    - PostgreSQL running on localhost:5432
    - Database 'banuxSPB' with operational tables created
    - Update DB_CONFIG below with your credentials
"""

import argparse
import sys
from datetime import datetime

try:
    import psycopg2
except ImportError:
    print('ERROR: psycopg2 not installed. Run: pip install psycopg2-binary')
    sys.exit(1)

# Database connection - update these to match your BCSrvSqlMq.ini
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'banuxSPB',
    'user': 'postgres',
    'password': 'Rama1248',
}

# Sample SPB XML message (simplified GEN0014 - test message)
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<DOC>
  <BCMSG>
    <IdentdEmissor>36266751</IdentdEmissor>
    <IdentdDesworknnatario>00038166</IdentdDesworknnatario>
    <IdentdContworknworknudo>GEN</IdentdContworknworknudo>
    <NUOp>{nu_ope}</NUOp>
    <DtHrMsg>{dt_hr}</DtHrMsg>
  </BCMSG>
  <SISMSG>
    <CodMsg>GEN0014</CodMsg>
    <NumCtrlIF>CTRL{seq:06d}</NumCtrlIF>
    <NumCtrlSTR>STR{seq:06d}</NumCtrlSTR>
  </SISMSG>
  <GENMSG>
    <TxtMsg>Test message #{seq} from test_db_insert.py</TxtMsg>
  </GENMSG>
</DOC>"""


def create_tables_if_needed(conn):
    """Create the required tables if they don't exist."""
    cur = conn.cursor()

    # spb_local_to_bacen (outbound: IF -> Bacen)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS spb_local_to_bacen (
            mq_msg_id        VARCHAR(48) DEFAULT '',
            mq_correl_id     VARCHAR(48) DEFAULT '',
            db_datetime      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status_msg       VARCHAR(1) DEFAULT 'N',
            flag_proc        VARCHAR(1) DEFAULT 'P',
            mq_qn_origem     VARCHAR(48) DEFAULT '',
            mq_qn_destino    VARCHAR(48) DEFAULT '',
            mq_datetime      VARCHAR(20) DEFAULT '',
            mq_header        BYTEA DEFAULT '',
            security_header  BYTEA DEFAULT '',
            nu_ope           VARCHAR(20) DEFAULT '',
            cod_msg          VARCHAR(10) DEFAULT '',
            msg              TEXT DEFAULT '',
            msg_len          INTEGER DEFAULT 0,
            mq_msg_id_coa    VARCHAR(48) DEFAULT '',
            mq_datetime_coa  VARCHAR(20) DEFAULT '',
            mq_msg_id_cod    VARCHAR(48) DEFAULT '',
            mq_datetime_cod  VARCHAR(20) DEFAULT '',
            mq_msg_id_rep    VARCHAR(48) DEFAULT ''
        )
    """)

    # spb_bacen_to_local (inbound: Bacen -> IF)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS spb_bacen_to_local (
            mq_msg_id        VARCHAR(48) DEFAULT '',
            mq_correl_id     VARCHAR(48) DEFAULT '',
            db_datetime      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status_msg       VARCHAR(1) DEFAULT 'N',
            flag_proc        VARCHAR(1) DEFAULT 'N',
            mq_qn_origem     VARCHAR(48) DEFAULT '',
            mq_datetime      VARCHAR(20) DEFAULT '',
            mq_header        BYTEA DEFAULT '',
            security_header  BYTEA DEFAULT '',
            nu_ope           VARCHAR(20) DEFAULT '',
            cod_msg          VARCHAR(10) DEFAULT '',
            msg              TEXT DEFAULT ''
        )
    """)

    # spb_log_bacen
    cur.execute("""
        CREATE TABLE IF NOT EXISTS spb_log_bacen (
            mq_msg_id        VARCHAR(48) DEFAULT '',
            mq_correl_id     VARCHAR(48) DEFAULT '',
            db_datetime      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status_msg       VARCHAR(1) DEFAULT 'N',
            flag_proc        VARCHAR(1) DEFAULT 'N',
            mq_qn_origem     VARCHAR(48) DEFAULT '',
            mq_datetime      VARCHAR(20) DEFAULT '',
            mq_header        BYTEA DEFAULT '',
            security_header  BYTEA DEFAULT '',
            nu_ope           VARCHAR(20) DEFAULT '',
            cod_msg          VARCHAR(10) DEFAULT ''
        )
    """)

    # spb_controle
    cur.execute("""
        CREATE TABLE IF NOT EXISTS spb_controle (
            cod_controle     VARCHAR(20) PRIMARY KEY,
            val_controle     VARCHAR(100) DEFAULT '',
            desc_controle    VARCHAR(200) DEFAULT '',
            dt_atualizacao   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usr_atualizacao  VARCHAR(50) DEFAULT '',
            status           VARCHAR(1) DEFAULT 'A',
            obs              TEXT DEFAULT ''
        )
    """)

    conn.commit()
    print('[OK] Tables verified/created.')


def insert_test_messages(conn, count=1):
    """Insert test messages into spb_local_to_bacen."""
    cur = conn.cursor()
    now = datetime.now()

    remote_queue = 'QR.REQ.36266751.00038166.01'

    for i in range(1, count + 1):
        nu_ope = f'{now.strftime("%Y%m%d")}{i:06d}'
        dt_hr = now.strftime('%Y-%m-%dT%H:%M:%S')
        xml_msg = SAMPLE_XML.format(nu_ope=nu_ope, dt_hr=dt_hr, seq=i)

        cur.execute("""
            INSERT INTO spb_local_to_bacen
                (mq_msg_id, mq_correl_id, db_datetime, status_msg, flag_proc,
                 mq_qn_destino, nu_ope, cod_msg, msg, msg_len)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            f'MSG{i:024d}',           # mq_msg_id
            f'COR{i:024d}',           # mq_correl_id
            now,                       # db_datetime
            'N',                       # status_msg
            'P',                       # flag_proc = Pending (IFReq will pick this up)
            remote_queue,              # mq_qn_destino
            nu_ope,                    # nu_ope
            'GEN0014',                 # cod_msg
            xml_msg,                   # msg
            len(xml_msg),              # msg_len
        ))

    conn.commit()
    print(f'[OK] Inserted {count} test message(s) into spb_local_to_bacen (flag_proc=P)')
    print(f'     The IFReq task will pick these up and send via MQ.')


def show_pending(conn):
    """Show pending messages in the outbound table."""
    cur = conn.cursor()
    cur.execute("""
        SELECT nu_ope, cod_msg, flag_proc, status_msg, db_datetime
        FROM spb_local_to_bacen
        WHERE flag_proc = 'P'
        ORDER BY db_datetime DESC
        LIMIT 20
    """)
    rows = cur.fetchall()

    if not rows:
        print('\n[INFO] No pending messages in spb_local_to_bacen.')
        return

    print(f'\nPending messages ({len(rows)}):')
    print(f'{"NuOpe":<20} {"CodMsg":<10} {"Flag":<5} {"Status":<5} {"DateTime"}')
    print('-' * 70)
    for row in rows:
        print(f'{row[0]:<20} {row[1]:<10} {row[2]:<5} {row[3]:<5} {row[4]}')


def main():
    parser = argparse.ArgumentParser(description='Insert test messages for BCSrvSqlMq')
    parser.add_argument('--count', '-n', type=int, default=1,
                        help='Number of test messages to insert (default: 1)')
    parser.add_argument('--create-tables', action='store_true',
                        help='Create tables if they do not exist')
    parser.add_argument('--show-pending', action='store_true',
                        help='Show pending messages only (no insert)')
    args = parser.parse_args()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
    except Exception as e:
        print(f'ERROR: Cannot connect to PostgreSQL: {e}')
        print(f'  Check DB_CONFIG in this script matches your BCSrvSqlMq.ini')
        sys.exit(1)

    try:
        if args.create_tables:
            create_tables_if_needed(conn)

        if args.show_pending:
            show_pending(conn)
        else:
            create_tables_if_needed(conn)
            insert_test_messages(conn, args.count)
            show_pending(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
