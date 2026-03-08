#!/usr/bin/env python3
"""
Integration test for IBM MQ and PostgreSQL database
Tests the complete BCSrvSqlMq environment
"""
import configparser
import psycopg2
import pymqi
from datetime import datetime

def load_config():
    """Load configuration from BCSrvSqlMq.ini"""
    config = configparser.ConfigParser()
    config.read('/home/ubuntu/SPB_FINAL/BCSrvSqlMq/BCSrvSqlMq.ini')
    return config

def test_mq_connection(config):
    """Test IBM MQ connection and queues"""
    print("=" * 70)
    print("Test 1: IBM MQ Connection")
    print("=" * 70)

    qmgr_name = config['MQSeries']['QueueManager']
    channel = 'FINVEST.SVRCONN'
    conn_info = 'localhost(1414)'

    try:
        # Connect to queue manager
        qmgr = pymqi.connect(qmgr_name, channel, conn_info)
        print(f"✅ Connected to queue manager: {qmgr_name}")

        # Test queue access
        test_queue = config['MQSeries']['QLBacenCidadeReq']
        queue = pymqi.Queue(qmgr, test_queue, pymqi.CMQC.MQOO_INQUIRE)
        print(f"✅ Successfully opened queue: {test_queue}")
        queue.close()

        qmgr.disconnect()
        print("✅ MQ connection test passed\n")
        return True

    except pymqi.MQMIError as e:
        print(f"❌ MQ Error: {e}\n")
        return False
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False

def test_database_connection(config):
    """Test PostgreSQL database connection"""
    print("=" * 70)
    print("Test 2: Database Connection")
    print("=" * 70)

    db_config = {
        'host': config['DataBase']['DBServer'],
        'port': 5432,
        'dbname': config['DataBase']['DBName'].lower(),
        'user': 'postgres',
        'password': 'Rama1248',
    }

    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        print(f"✅ Connected to database: {db_config['dbname']}")

        cur = conn.cursor()

        # Verify control table
        cur.execute("SELECT ispb, nome_ispb, status_geral FROM SPB_CONTROLE")
        row = cur.fetchone()
        if row:
            print(f"✅ Control record found: ISPB={row[0]}, Name={row[1]}, Status={row[2]}")
        else:
            print("⚠️  No control record found")

        cur.close()
        conn.close()
        print("✅ Database connection test passed\n")
        return True

    except psycopg2.Error as e:
        print(f"❌ Database Error: {e}\n")
        return False
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False

def test_mq_to_database(config):
    """Test putting a message to MQ and logging it to database"""
    print("=" * 70)
    print("Test 3: MQ to Database Integration")
    print("=" * 70)

    # MQ configuration
    qmgr_name = config['MQSeries']['QueueManager']
    channel = 'FINVEST.SVRCONN'
    conn_info = 'localhost(1414)'
    test_queue = config['MQSeries']['QLBacenCidadeReq']

    # Database configuration
    db_config = {
        'host': config['DataBase']['DBServer'],
        'port': 5432,
        'dbname': config['DataBase']['DBName'].lower(),
        'user': 'postgres',
        'password': 'Rama1248',
    }

    try:
        # Step 1: Put message to MQ queue
        qmgr = pymqi.connect(qmgr_name, channel, conn_info)
        queue = pymqi.Queue(qmgr, test_queue,
                           pymqi.CMQC.MQOO_OUTPUT | pymqi.CMQC.MQOO_INPUT_AS_Q_DEF)

        test_msg = b'TEST INTEGRATION MESSAGE'
        md = pymqi.MD()
        queue.put(test_msg, md)
        msg_id = md.MsgId
        print(f"✅ Message sent to queue: {test_queue}")
        print(f"   Message ID: {msg_id.hex()}")

        # Step 2: Get message back
        md_get = pymqi.MD()
        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_WAIT | pymqi.CMQC.MQGMO_FAIL_IF_QUIESCING
        gmo.WaitInterval = 5000  # 5 seconds

        msg = queue.get(None, md_get, gmo)
        print(f"✅ Message retrieved from queue")
        print(f"   Message: {msg.decode()}")

        queue.close()
        qmgr.disconnect()

        # Step 3: Log to database
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO SPB_LOG_BACEN
            (mq_msg_id, mq_correl_id, db_datetime, status_msg,
             mq_qn_origem, mq_datetime, mq_header, nu_ope, cod_msg, msg)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            psycopg2.Binary(msg_id),
            psycopg2.Binary(md_get.CorrelId),
            datetime.now(),
            'T',  # Test
            test_queue,
            datetime.now(),
            psycopg2.Binary(b'TEST_HEADER'),
            'TEST_OPE',
            'TEST_CODE',
            msg.decode()
        ))

        conn.commit()
        print(f"✅ Message logged to SPB_LOG_BACEN")

        # Verify database record
        cur.execute("SELECT COUNT(*) FROM SPB_LOG_BACEN")
        count = cur.fetchone()[0]
        print(f"✅ Total records in SPB_LOG_BACEN: {count}")

        cur.close()
        conn.close()

        print("✅ MQ to Database integration test passed\n")
        return True

    except pymqi.MQMIError as e:
        print(f"❌ MQ Error: {e}\n")
        return False
    except psycopg2.Error as e:
        print(f"❌ Database Error: {e}\n")
        return False
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("\n" + "=" * 70)
    print("BCSrvSqlMq Integration Test Suite")
    print("=" * 70)
    print()

    # Load configuration
    config = load_config()

    # Run tests
    results = []
    results.append(("MQ Connection", test_mq_connection(config)))
    results.append(("Database Connection", test_database_connection(config)))
    results.append(("MQ to Database Integration", test_mq_to_database(config)))

    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:30} : {status}")
    print("=" * 70)

    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! BCSrvSqlMq environment is ready!")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    print("=" * 70)

    return all_passed

if __name__ == '__main__':
    import sys
    sys.exit(0 if main() else 1)
