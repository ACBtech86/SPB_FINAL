#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for SPB System

Tests the complete message flow:
1. SPBSite (Web Interface) -> Submit message via API
2. BCSrvSqlMq -> Process and send to IBM MQ
3. IBM MQ -> Queue management
4. BACEN Simulator -> Auto-response
5. Reverse flow -> Response back to database
6. SPBSite -> Display response

This script:
- Checks service status
- Starts services if needed
- Submits test message
- Monitors complete flow
- Generates comprehensive report
"""

import sys
import os
import time
import json
import subprocess
import psycopg2
import requests
from datetime import datetime
from pathlib import Path

# ===========================================================================
# Configuration
# ===========================================================================

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'banuxSPB',
    'user': 'postgres',
    'password': 'Rama1248',
}

# Service ports
SPBSITE_PORT = 8000
SPBSITE_URL = f'http://localhost:{SPBSITE_PORT}'
BCSRVSQLMQ_MONITOR_PORT = 14499

# Test message details
TEST_ISPB_LOCAL = '36266751'  # Finvest
TEST_ISPB_BACEN = '00038166'  # BACEN
TEST_MESSAGE_TYPE = 'GEN0001'  # Echo request

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
BCSRVSQLMQ_PATH = PROJECT_ROOT / 'BCSrvSqlMq' / 'python'
SPBSITE_PATH = PROJECT_ROOT / 'spbsite'
BACEN_SIMULATOR_PATH = BCSRVSQLMQ_PATH / 'scripts' / 'bacen_simulator.py'

# ===========================================================================
# Helper Functions
# ===========================================================================

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


def check_port(port):
    """Check if a port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def get_db_connection():
    """Get database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print_status(f"Database connection failed: {e}", 'error')
        return None


def check_service_status():
    """Check status of all required services."""
    print_header("Step 1: Service Status Check")

    services = {
        'PostgreSQL': ('Database', DB_CONFIG['port']),
        'IBM MQ': ('Message Queue', 1414),
        'SPBSite': ('Web Interface', SPBSITE_PORT),
        'BCSrvSqlMq': ('Backend Service', BCSRVSQLMQ_MONITOR_PORT),
    }

    status = {}
    for name, (desc, port) in services.items():
        running = check_port(port)
        status[name] = running
        icon = '[OK]' if running else '[FAIL]'
        state = 'Running' if running else 'Stopped'
        print(f"{icon} {name} ({desc}): {state} [Port {port}]")

    return status


def start_spbsite():
    """Start SPBSite service in background."""
    print_status("Starting SPBSite web server...", 'progress')

    # Check if already running
    if check_port(SPBSITE_PORT):
        print_status("SPBSite already running", 'success')
        return None

    # Start SPBSite
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', str(SPBSITE_PORT)
    ]

    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(SPBSITE_PATH),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )

        # Wait for startup
        print_status("Waiting for SPBSite to start...", 'progress')
        for i in range(10):
            time.sleep(1)
            if check_port(SPBSITE_PORT):
                print_status(f"SPBSite started successfully: {SPBSITE_URL}", 'success')
                return process

        print_status("SPBSite failed to start", 'error')
        return None

    except Exception as e:
        print_status(f"Failed to start SPBSite: {e}", 'error')
        return None


def start_bacen_simulator():
    """Start BACEN simulator in background."""
    print_status("Starting BACEN Simulator...", 'progress')

    if not BACEN_SIMULATOR_PATH.exists():
        print_status(f"BACEN simulator not found: {BACEN_SIMULATOR_PATH}", 'error')
        return None

    try:
        process = subprocess.Popen(
            [sys.executable, str(BACEN_SIMULATOR_PATH)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )

        print_status("BACEN Simulator started", 'success')
        time.sleep(2)  # Give it time to initialize
        return process

    except Exception as e:
        print_status(f"Failed to start BACEN simulator: {e}", 'error')
        return None


def create_test_message():
    """Create a test SPB message."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    return {
        'cod_msg': TEST_MESSAGE_TYPE,
        'ispb_emissor': TEST_ISPB_LOCAL,
        'ispb_destinatario': TEST_ISPB_BACEN,
        'nu_op': f'TEST{timestamp}',
        'dt_movto': datetime.now().strftime('%Y-%m-%d'),
        'fields': {
            'InfConsMsg': {
                'NumCtrlIF': f'TEST{timestamp}',
                'TpConsMsg': 'ECHO'
            }
        }
    }


def submit_message_via_api(message_data):
    """Submit message via SPBSite API."""
    print_header("Step 2: Submit Test Message via SPBSite")

    # First, login to get token
    print_status("Authenticating with SPBSite...", 'progress')

    try:
        login_response = requests.post(
            f'{SPBSITE_URL}/api/auth/login',
            data={'username': 'admin', 'password': 'admin'},
            timeout=10
        )

        if login_response.status_code != 200:
            print_status(f"Login failed: {login_response.status_code}", 'error')
            return None

        print_status("Authentication successful", 'success')

        # Submit message
        print_status(f"Submitting {TEST_MESSAGE_TYPE} message...", 'progress')

        submit_response = requests.post(
            f'{SPBSITE_URL}/api/messages/submit',
            json=message_data,
            cookies=login_response.cookies,
            timeout=10
        )

        if submit_response.status_code == 200:
            result = submit_response.json()
            print_status(f"Message submitted successfully", 'success')
            print(f"   Message ID: {result.get('message_id', 'N/A')}")
            print(f"   NU_OP: {result.get('nu_op', 'N/A')}")
            return result
        else:
            print_status(f"Message submission failed: {submit_response.status_code}", 'error')
            print(f"   Response: {submit_response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to SPBSite - service not running?", 'error')
        return None
    except Exception as e:
        print_status(f"Error submitting message: {e}", 'error')
        return None


def monitor_database_for_message(nu_op, timeout=30):
    """Monitor database for message creation."""
    print_header("Step 3: Monitor Database for Message")

    conn = get_db_connection()
    if not conn:
        return None

    print_status(f"Monitoring for NU_OP: {nu_op}", 'progress')

    start_time = time.time()
    while (time.time() - start_time) < timeout:
        try:
            cur = conn.cursor()

            # Check spb_local_to_bacen table
            cur.execute("""
                SELECT nu_op, cod_msg, ispb_emissor, ispb_destinatario,
                       status, dt_hr_criacao
                FROM spb_local_to_bacen
                WHERE nu_op = %s
                ORDER BY dt_hr_criacao DESC
                LIMIT 1
            """, (nu_op,))

            row = cur.fetchone()
            if row:
                print_status("Message found in database!", 'success')
                print(f"   NU_OP: {row[0]}")
                print(f"   Message Type: {row[1]}")
                print(f"   From: {row[2]} -> To: {row[3]}")
                print(f"   Status: {row[4]}")
                print(f"   Created: {row[5]}")
                cur.close()
                conn.close()
                return row

            cur.close()
            time.sleep(1)

        except Exception as e:
            print_status(f"Database query error: {e}", 'error')
            conn.close()
            return None

    print_status(f"Message not found after {timeout}s", 'warning')
    conn.close()
    return None


def check_mq_queues():
    """Check IBM MQ queue depths."""
    print_header("Step 4: Check IBM MQ Queues")

    # This would require pymqi which may not be available
    # For now, just report that this step should be done
    print_status("Manual check recommended:", 'info')
    print("   Run: runmqsc QM.36266751.01")
    print("   Commands:")
    print("     DISPLAY QLOCAL(QL.36266751.01.ENTRADA.IF) CURDEPTH")
    print("     DISPLAY QLOCAL(QL.REQ.00038166.36266751.01) CURDEPTH")


def monitor_response(nu_op, timeout=60):
    """Monitor for response message."""
    print_header("Step 5: Monitor for Response")

    conn = get_db_connection()
    if not conn:
        return None

    print_status(f"Waiting for response to NU_OP: {nu_op}", 'progress')
    print_status(f"Timeout: {timeout}s", 'info')

    start_time = time.time()
    while (time.time() - start_time) < timeout:
        try:
            cur = conn.cursor()

            # Check spb_bacen_to_local for response
            cur.execute("""
                SELECT nu_op, cod_msg, ispb_emissor, ispb_destinatario,
                       status, dt_hr_criacao
                FROM spb_bacen_to_local
                WHERE nu_op = %s
                ORDER BY dt_hr_criacao DESC
                LIMIT 1
            """, (nu_op,))

            row = cur.fetchone()
            if row:
                elapsed = time.time() - start_time
                print_status(f"Response received! (after {elapsed:.1f}s)", 'success')
                print(f"   NU_OP: {row[0]}")
                print(f"   Response Type: {row[1]}")
                print(f"   From: {row[2]} -> To: {row[3]}")
                print(f"   Status: {row[4]}")
                print(f"   Received: {row[5]}")
                cur.close()
                conn.close()
                return row

            cur.close()
            time.sleep(2)

        except Exception as e:
            print_status(f"Database query error: {e}", 'error')
            conn.close()
            return None

    print_status(f"No response received after {timeout}s", 'warning')
    conn.close()
    return None


def verify_via_spbsite(nu_op):
    """Verify message is visible via SPBSite API."""
    print_header("Step 6: Verify via SPBSite API")

    try:
        # Login
        login_response = requests.post(
            f'{SPBSITE_URL}/api/auth/login',
            data={'username': 'admin', 'password': 'admin'},
            timeout=10
        )

        if login_response.status_code != 200:
            print_status("Authentication failed", 'error')
            return False

        # Get messages
        messages_response = requests.get(
            f'{SPBSITE_URL}/api/messages',
            cookies=login_response.cookies,
            timeout=10
        )

        if messages_response.status_code == 200:
            messages = messages_response.json()

            # Find our test message
            test_msg = None
            for msg in messages:
                if msg.get('nu_op') == nu_op:
                    test_msg = msg
                    break

            if test_msg:
                print_status("Message found in SPBSite!", 'success')
                print(f"   NU_OP: {test_msg.get('nu_op')}")
                print(f"   Status: {test_msg.get('status')}")
                return True
            else:
                print_status("Message not found in SPBSite", 'warning')
                return False
        else:
            print_status(f"Failed to get messages: {messages_response.status_code}", 'error')
            return False

    except Exception as e:
        print_status(f"Error verifying via SPBSite: {e}", 'error')
        return False


def generate_report(results):
    """Generate comprehensive test report."""
    print_header("End-to-End Test Report")

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"Test Execution Time: {timestamp}")
    print(f"Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}")
    print(f"SPBSite URL: {SPBSITE_URL}")
    print()

    print("Test Results:")
    print("-" * 80)

    for step, result in results.items():
        status = '[OK] PASS' if result['success'] else '[FAIL] FAIL'
        print(f"{status} - {step}")
        if result.get('details'):
            print(f"         {result['details']}")

    print("-" * 80)

    # Overall result
    all_passed = all(r['success'] for r in results.values())
    if all_passed:
        print_status("\nAll tests PASSED! [OK]", 'success')
    else:
        print_status("\nSome tests FAILED [FAIL]", 'error')

    return all_passed


# ===========================================================================
# Main Test Execution
# ===========================================================================

def main():
    """Main test execution."""
    print_header("SPB System - Comprehensive End-to-End Test")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}
    processes = []

    try:
        # Step 1: Check services
        service_status = check_service_status()
        results['Service Check'] = {
            'success': service_status.get('PostgreSQL', False) and service_status.get('IBM MQ', False),
            'details': f"PostgreSQL: {service_status.get('PostgreSQL')}, IBM MQ: {service_status.get('IBM MQ')}"
        }

        if not results['Service Check']['success']:
            print_status("\nRequired services not running. Please start:", 'error')
            print("  - PostgreSQL")
            print("  - IBM MQ")
            return 1

        # Step 2: Start SPBSite if not running
        if not service_status.get('SPBSite'):
            spbsite_process = start_spbsite()
            if spbsite_process:
                processes.append(spbsite_process)

        # Step 3: Start BACEN simulator
        bacen_process = start_bacen_simulator()
        if bacen_process:
            processes.append(bacen_process)

        # Step 4: Create and submit test message
        message_data = create_test_message()
        submission_result = submit_message_via_api(message_data)

        results['Message Submission'] = {
            'success': submission_result is not None,
            'details': f"NU_OP: {message_data['nu_op']}" if submission_result else "Failed"
        }

        if not submission_result:
            print_status("\nCannot proceed without successful message submission", 'error')
            return 1

        nu_op = message_data['nu_op']

        # Step 5: Monitor database for message
        db_message = monitor_database_for_message(nu_op)
        results['Database Storage'] = {
            'success': db_message is not None,
            'details': f"Message stored with status: {db_message[4]}" if db_message else "Not found"
        }

        # Step 6: Check MQ queues
        check_mq_queues()

        # Step 7: Monitor for response
        response = monitor_response(nu_op, timeout=60)
        results['Response Received'] = {
            'success': response is not None,
            'details': f"Response type: {response[1]}" if response else "No response"
        }

        # Step 8: Verify via SPBSite
        spbsite_verified = verify_via_spbsite(nu_op)
        results['SPBSite Visibility'] = {
            'success': spbsite_verified,
            'details': "Message visible in web interface" if spbsite_verified else "Not visible"
        }

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

    finally:
        # Cleanup: terminate background processes
        print_status("\nCleaning up background processes...", 'info')
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()


if __name__ == '__main__':
    sys.exit(main())
