#!/usr/bin/env python3
"""
Simplified End-to-End Database Test for SPB System

Tests the database flow without requiring web API:
1. Direct database insert of test message
2. Monitor for message processing
3. Verify database states

This test focuses on the core data flow through the banuxSPB database.
"""

import sys
import psycopg2
import time
from datetime import datetime, timezone

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'BanuxSPB',  # Note: case-sensitive
    'user': 'postgres',
    'password': 'Rama1248',
}

# Test configuration
TEST_ISPB_LOCAL = '36266751'  # Finvest
TEST_ISPB_BACEN = '00038166'  # BACEN
TEST_MESSAGE_TYPE = 'GEN0001'  # Echo request


def print_header(title):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_status(message, status='info'):
    """Print formatted status message."""
    icons = {'info': '[INFO]', 'success': '[OK]', 'error': '[ERR]', 'warning': '[WARN]', 'progress': '[...]'}
    icon = icons.get(status, '[*]')
    print(f"{icon} {message}")


def get_db_connection():
    """Get database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print_status(f"Database connection failed: {e}", 'error')
        return None


def check_database_tables():
    """Check if required tables exist."""
    print_header("Step 1: Database Table Check")

    conn = get_db_connection()
    if not conn:
        return False

    tables_to_check = [
        'spb_local_to_bacen',
        'spb_bacen_to_local',
        'spb_log_bacen',
        'spb_controle',
        '"SPB_MENSAGEM"',  # Catalog table (quoted uppercase)
        '"SPB_DICIONARIO"',
        '"SPB_MSGFIELD"',
    ]

    all_exist = True
    try:
        cur = conn.cursor()

        for table in tables_to_check:
            # Handle quoted tables differently
            if table.startswith('"'):
                table_name = table.strip('"')
                query = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)"
                cur.execute(query, (table_name,))
            else:
                query = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)"
                cur.execute(query, (table,))

            exists = cur.fetchone()[0]

            if exists:
                print_status(f"Table {table}: Found", 'success')
            else:
                print_status(f"Table {table}: Missing", 'error')
                all_exist = False

        cur.close()
        conn.close()

        return all_exist

    except Exception as e:
        print_status(f"Error checking tables: {e}", 'error')
        conn.close()
        return False


def check_catalog_data():
    """Check if catalog tables have data."""
    print_header("Step 2: Catalog Data Check")

    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()

        # Check SPB_MENSAGEM for GEN0001
        cur.execute('SELECT COUNT(*) FROM "SPB_MENSAGEM"')
        msg_count = cur.fetchone()[0]
        print_status(f"SPB_MENSAGEM: {msg_count} messages", 'success' if msg_count > 0 else 'warning')

        cur.execute('SELECT COUNT(*) FROM "SPB_DICIONARIO"')
        dict_count = cur.fetchone()[0]
        print_status(f"SPB_DICIONARIO: {dict_count} fields", 'success' if dict_count > 0 else 'warning')

        cur.execute('SELECT COUNT(*) FROM "SPB_MSGFIELD"')
        field_count = cur.fetchone()[0]
        print_status(f"SPB_MSGFIELD: {field_count} mappings", 'success' if field_count > 0 else 'warning')

        cur.close()
        conn.close()

        return msg_count > 0 and dict_count > 0 and field_count > 0

    except Exception as e:
        print_status(f"Error checking catalog: {e}", 'error')
        conn.close()
        return False


def create_test_message_in_db():
    """Create a test message directly in the database."""
    print_header("Step 3: Create Test Message in Database")

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    nu_ope = f'E2ETEST{timestamp}'

    conn = get_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()

        # Insert into spb_local_to_bacen (outbound message table)
        # Schema: mq_msg_id, mq_correl_id, db_datetime, status_msg, flag_proc,
        #         mq_qn_origem, mq_datetime, mq_header, security_header,
        #         nu_ope, cod_msg, msg
        insert_query = """
        INSERT INTO spb_local_to_bacen (
            mq_msg_id, mq_correl_id, db_datetime, status_msg, flag_proc,
            nu_ope, cod_msg, msg
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s
        )
        RETURNING nu_ope
        """

        xml_msg = f"""<?xml version="1.0" encoding="UTF-8"?>
<DOC>
    <BCMSG>
        <IdentdEmissor>{TEST_ISPB_LOCAL}</IdentdEmissor>
        <IdentdDestinatario>{TEST_ISPB_BACEN}</IdentdDestinatario>
        <CodMsg>{TEST_MESSAGE_TYPE}</CodMsg>
        <NumCtrlIF>{nu_ope}</NumCtrlIF>
    </BCMSG>
    <SISMSG>
        <GEN0001>
            <InfConsMsg>
                <NumCtrlIF>{nu_ope}</NumCtrlIF>
                <TpConsMsg>ECHO</TpConsMsg>
            </InfConsMsg>
        </GEN0001>
    </SISMSG>
</DOC>"""

        # Generate fake MQ message IDs for testing
        import os
        fake_msg_id = os.urandom(24)  # 24-byte message ID
        fake_correl_id = os.urandom(24)  # 24-byte correlation ID

        values = (
            fake_msg_id,  # mq_msg_id (bytea)
            fake_correl_id,  # mq_correl_id (bytea)
            datetime.now(),  # db_datetime
            'P',  # status_msg: Pending
            'N',  # flag_proc: Not processed
            nu_ope,  # nu_ope
            TEST_MESSAGE_TYPE,  # cod_msg
            xml_msg  # msg
        )

        cur.execute(insert_query, values)
        conn.commit()

        print_status(f"Test message created: {nu_ope}", 'success')
        print(f"   Message Type: {TEST_MESSAGE_TYPE}")
        print(f"   From: {TEST_ISPB_LOCAL} -> To: {TEST_ISPB_BACEN}")
        print(f"   Status: Pending")

        cur.close()
        conn.close()

        return nu_ope

    except Exception as e:
        print_status(f"Error creating test message: {e}", 'error')
        conn.rollback()
        conn.close()
        return None


def verify_message_in_db(nu_ope):
    """Verify message exists in database."""
    print_header("Step 4: Verify Message in Database")

    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT nu_ope, cod_msg, status, dt_hr_criacao
            FROM spb_local_to_bacen
            WHERE nu_ope = %s
        """, (nu_ope,))

        row = cur.fetchone()

        if row:
            print_status(f"Message found in spb_local_to_bacen", 'success')
            print(f"   NU_OP: {row[0]}")
            print(f"   Message Type: {row[1]}")
            print(f"   Status: {row[2]}")
            print(f"   Created: {row[3]}")

            cur.close()
            conn.close()
            return True
        else:
            print_status(f"Message not found", 'error')
            cur.close()
            conn.close()
            return False

    except Exception as e:
        print_status(f"Error verifying message: {e}", 'error')
        conn.close()
        return False


def check_for_response(nu_ope, timeout=10):
    """Check if a response was generated (simulated or real)."""
    print_header("Step 5: Check for Response")

    print_status(f"Checking for response to {nu_ope} (timeout: {timeout}s)", 'progress')
    print_status("Note: This requires BCSrvSqlMq + BACEN Simulator to be running", 'info')

    conn = get_db_connection()
    if not conn:
        return False

    start_time = time.time()
    while (time.time() - start_time) < timeout:
        try:
            cur = conn.cursor()

            # Check spb_bacen_to_local for response
            cur.execute("""
                SELECT nu_ope, cod_msg, status, dt_hr_criacao
                FROM spb_bacen_to_local
                WHERE nu_ope = %s
                ORDER BY dt_hr_criacao DESC
                LIMIT 1
            """, (nu_ope,))

            row = cur.fetchone()

            if row:
                elapsed = time.time() - start_time
                print_status(f"Response received after {elapsed:.1f}s!", 'success')
                print(f"   NU_OP: {row[0]}")
                print(f"   Response Type: {row[1]}")
                print(f"   Status: {row[2]}")
                print(f"   Received: {row[3]}")

                cur.close()
                conn.close()
                return True

            cur.close()
            time.sleep(1)

        except Exception as e:
            print_status(f"Error checking response: {e}", 'error')
            conn.close()
            return False

    print_status(f"No response after {timeout}s", 'warning')
    print_status("BCSrvSqlMq or BACEN Simulator may not be running", 'info')
    conn.close()
    return False


def check_log_table(nu_ope):
    """Check if message was logged."""
    print_header("Step 6: Check Log Table")

    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT COUNT(*) FROM spb_log_bacen
            WHERE xml_msg LIKE %s
        """, (f'%{nu_ope}%',))

        count = cur.fetchone()[0]

        if count > 0:
            print_status(f"Found {count} log entries for message", 'success')
            cur.close()
            conn.close()
            return True
        else:
            print_status("No log entries found", 'warning')
            print_status("This is expected if BCSrvSqlMq hasn't processed the message yet", 'info')
            cur.close()
            conn.close()
            return False

    except Exception as e:
        print_status(f"Error checking logs: {e}", 'error')
        conn.close()
        return False


def cleanup_test_data(nu_ope):
    """Clean up test message from database."""
    print_header("Step 7: Cleanup Test Data")

    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()

        # Delete from spb_local_to_bacen
        cur.execute("DELETE FROM spb_local_to_bacen WHERE nu_ope = %s", (nu_ope,))
        deleted_out = cur.rowcount

        # Delete from spb_bacen_to_local
        cur.execute("DELETE FROM spb_bacen_to_local WHERE nu_ope = %s", (nu_ope,))
        deleted_in = cur.rowcount

        # Delete from spb_log_bacen
        cur.execute("DELETE FROM spb_log_bacen WHERE xml_msg LIKE %s", (f'%{nu_ope}%',))
        deleted_log = cur.rowcount

        conn.commit()

        print_status(f"Cleaned up test data", 'success')
        print(f"   Deleted from spb_local_to_bacen: {deleted_out} rows")
        print(f"   Deleted from spb_bacen_to_local: {deleted_in} rows")
        print(f"   Deleted from spb_log_bacen: {deleted_log} rows")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print_status(f"Error cleaning up: {e}", 'error')
        conn.rollback()
        conn.close()
        return False


def generate_report(results):
    """Generate test report."""
    print_header("End-to-End Database Test Report")

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Test Execution Time: {timestamp}")
    print(f"Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}")
    print()

    print("Test Results:")
    print("-" * 80)

    for step, result in results.items():
        status = '[OK] PASS' if result else '[FAIL] FAIL'
        print(f"{status} - {step}")

    print("-" * 80)

    # Overall result
    all_passed = all(results.values())
    if all_passed:
        print_status("\nAll tests PASSED!", 'success')
    else:
        print_status("\nSome tests FAILED", 'warning')

    return all_passed


def main():
    """Main test execution."""
    print_header("SPB System - Simplified Database E2E Test")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    try:
        # Step 1: Check tables
        tables_ok = check_database_tables()
        results['Database Tables'] = tables_ok

        if not tables_ok:
            print_status("\nRequired tables missing. Run setup_database.py first", 'error')
            return 1

        # Step 2: Check catalog
        catalog_ok = check_catalog_data()
        results['Catalog Data'] = catalog_ok

        # Step 3: Create test message
        nu_ope = create_test_message_in_db()
        results['Message Creation'] = nu_ope is not None

        if not nu_ope:
            print_status("\nCannot proceed without test message", 'error')
            return 1

        # Step 4: Verify message
        verify_ok = verify_message_in_db(nu_ope)
        results['Message Verification'] = verify_ok

        # Step 5: Check for response (may timeout if services not running)
        response_ok = check_for_response(nu_ope, timeout=10)
        results['Response Received'] = response_ok

        # Step 6: Check logs
        log_ok = check_log_table(nu_ope)
        results['Message Logged'] = log_ok

        # Step 7: Cleanup
        cleanup_ok = cleanup_test_data(nu_ope)
        results['Cleanup'] = cleanup_ok

        # Generate report
        success = generate_report(results)

        return 0 if success else 1

    except KeyboardInterrupt:
        print_status("\nTest interrupted by user", 'warning')
        return 1

    except Exception as e:
        print_status(f"\nTest failed with error: {e}", 'error')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
