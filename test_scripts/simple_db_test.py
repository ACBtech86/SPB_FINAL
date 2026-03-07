"""
Simple Database Test - PostgreSQL
Tests SPBSite -> Database flow by directly inserting and monitoring.
"""

import psycopg2
import time
from datetime import datetime

# PostgreSQL connection parameters
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'BCSPB',
    'user': 'postgres',
    'password': ''
}

def create_test_message():
    """Insert test message directly into PostgreSQL."""
    now = datetime.now()
    nu_ope = now.strftime('%Y%m%d%H%M%S')

    print("=" * 80)
    print("Creating Test Message")
    print("=" * 80)
    print(f"Operation Number: {nu_ope}")
    print(f"Timestamp: {now}")
    print()

    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    # Insert message
    cursor.execute('''
        INSERT INTO spb_local_to_bacen
        (db_datetime, cod_msg, mq_qn_destino, status_msg, flag_proc, nu_ope, msg)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (
        now,
        'SPB0001',
        'QR.REQ.36266751.00038166.01',
        'P',  # Pending
        'N',  # Not processed
        nu_ope,
        f'''<?xml version="1.0" encoding="UTF-8"?>
<DOC>
    <BCMSG>
        <IdentdPartDestinat>00038166</IdentdPartDestinat>
        <IdentdPartRemt>36266751</IdentdPartRemt>
        <IdentdOperad>
            <NumCtrl>{nu_ope}</NumCtrl>
            <DtHrOp>{now.strftime('%Y-%m-%dT%H:%M:%S')}</DtHrOp>
        </IdentdOperad>
    </BCMSG>
    <SISMSG>
        <CodMsg>SPB0001</CodMsg>
        <TestMessage>
            <Description>Simple DB Test</Description>
        </TestMessage>
    </SISMSG>
</DOC>'''
    ))

    conn.commit()
    conn.close()

    print("[OK] Message inserted into database")
    print(f"   - Operation: {nu_ope}")
    print(f"   - Status: P (Pending)")
    print(f"   - Destination: QR.REQ.36266751.00038166.01")
    print()

    return nu_ope


def check_message(nu_ope):
    """Check message status."""
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT nu_ope, status_msg, flag_proc, mq_msg_id, cod_msg
        FROM spb_local_to_bacen
        WHERE nu_ope = %s
    ''', (nu_ope,))

    row = cursor.fetchone()

    if row:
        nu_ope_db, status, flag, mq_id, cod = row

        status_map = {
            'P': 'Pending',
            'E': 'Sent to MQ',
            'C': 'Confirmed',
            'R': 'Rejected'
        }

        print(f"[OK] Message Found:")
        print(f"   - Operation: {nu_ope_db}")
        print(f"   - Status: {status} ({status_map.get(status, 'Unknown')})")
        print(f"   - Processed: {flag} ({'Yes' if flag == 'S' else 'No'})")

        if mq_id:
            print(f"   - MQ Message ID: Set")

        # Check for responses
        cursor.execute('''
            SELECT nu_ope, cod_msg, status_msg, db_datetime
            FROM spb_bacen_to_local
            WHERE nu_ope LIKE %s
            ORDER BY db_datetime DESC
        ''', (f'%{nu_ope}%',))

        responses = cursor.fetchall()
        if responses:
            print(f"\n[OK] {len(responses)} Response(s) Received:")
            for idx, resp in enumerate(responses, 1):
                print(f"   Response {idx}: {resp[1]} - {resp[2]}")

        conn.close()
        return status, flag
    else:
        print(f"[ERROR] Message not found")
        conn.close()
        return None, None


def main():
    """Main test."""
    print("\n")
    print("=" * 80)
    print("SPB Simple Database Test")
    print("=" * 80)
    print()
    print("This test will:")
    print("1. Insert a test message into the database")
    print("2. Monitor it for 30 seconds")
    print("3. Check if BCSrvSqlMq processes it")
    print()
    print("Make sure:")
    print("- PostgreSQL is running (BCSPB database)")
    print("- BCSrvSqlMq is running")
    print("- IBM MQ is running")
    print()

    # Create message
    nu_ope = create_test_message()

    # Save for later
    with open('test_scripts/last_operation.txt', 'w') as f:
        f.write(nu_ope)

    # Monitor
    print("=" * 80)
    print("Monitoring (30 seconds, checking every 5 seconds)")
    print("=" * 80)
    print()

    for i in range(6):
        print(f"Check #{i+1}:")
        print("-" * 80)
        status, flag = check_message(nu_ope)
        print()

        if flag == 'S':
            print("[OK] SUCCESS! Message processed by BCSrvSqlMq")
            if status == 'E':
                print("[OK] Message sent to IBM MQ")
            break

        if i < 5:
            print("Waiting 5 seconds...")
            print()
            time.sleep(5)

    # Final summary
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)
    print(f"Operation Number: {nu_ope}")
    print()
    print("Check SPBSite: http://localhost:8000")
    print("  Login: admin / admin")
    print("  Messages -> Sent Messages")
    print()
    print("Check database:")
    print(f"  SELECT * FROM spb_local_to_bacen WHERE nu_ope = '{nu_ope}';")
    print()


if __name__ == '__main__':
    main()
