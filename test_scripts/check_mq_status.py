"""
Check IBM MQ Status
Verifies MQ Queue Manager and queues are ready for testing.
"""

import pymqi
import sys

# Configuration
QUEUE_MANAGER = 'QM.36266751.01'
CHANNEL = 'FINVEST.SVRCONN'
CONN_INFO = 'localhost(1414)'

# Queues to check
QUEUES = [
    'QL.REQ.00038166.36266751.01',
    'QL.RSP.00038166.36266751.01',
    'QL.REP.00038166.36266751.01',
    'QL.SUP.00038166.36266751.01',
    'QR.REQ.36266751.00038166.01',
    'QR.RSP.36266751.00038166.01',
    'QR.REP.36266751.00038166.01',
    'QR.SUP.36266751.00038166.01',
]


def check_queue_manager():
    """Check if Queue Manager is running."""
    try:
        cd = pymqi.CD()
        cd.ChannelName = CHANNEL.encode()
        cd.ConnectionName = CONN_INFO.encode()
        cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
        cd.TransportType = pymqi.CMQC.MQXPT_TCP

        qmgr = pymqi.connect(QUEUE_MANAGER, cd=cd)
        print(f"✅ Connected to Queue Manager: {QUEUE_MANAGER}")

        return qmgr
    except pymqi.MQMIError as e:
        print(f"❌ Failed to connect to Queue Manager: {e}")
        return None


def check_queue(qmgr, queue_name):
    """Check queue status and depth."""
    try:
        pcf = pymqi.PCFExecute(qmgr)

        attrs = [
            pymqi.CMQC.MQCA_Q_NAME,
            pymqi.CMQC.MQIA_CURRENT_Q_DEPTH,
            pymqi.CMQC.MQIA_MAX_Q_DEPTH,
            pymqi.CMQC.MQIA_Q_TYPE
        ]

        response = pcf.MQCMD_INQUIRE_Q(
            {pymqi.CMQC.MQCA_Q_NAME: queue_name.encode()},
            attrs
        )

        if response:
            r = response[0]
            name = r[pymqi.CMQC.MQCA_Q_NAME].decode().strip()
            current_depth = r[pymqi.CMQC.MQIA_CURRENT_Q_DEPTH]
            max_depth = r[pymqi.CMQC.MQIA_MAX_Q_DEPTH]
            q_type = r[pymqi.CMQC.MQIA_Q_TYPE]

            type_str = "Local" if q_type == pymqi.CMQC.MQQT_LOCAL else "Remote"

            print(f"  ✅ {name:<40} Type: {type_str:<8} Depth: {current_depth:>4}/{max_depth}")
            return True
    except pymqi.MQMIError as e:
        print(f"  ❌ {queue_name:<40} ERROR: {e}")
        return False


def main():
    """Main function."""
    print("=" * 80)
    print("IBM MQ Status Check")
    print("=" * 80)
    print()

    # Check Queue Manager
    qmgr = check_queue_manager()
    if not qmgr:
        print("\n❌ Cannot proceed without Queue Manager connection")
        sys.exit(1)

    print()
    print("Checking Queues:")
    print("-" * 80)

    # Check all queues
    all_ok = True
    for queue_name in QUEUES:
        if not check_queue(qmgr, queue_name):
            all_ok = False

    print("-" * 80)
    print()

    # Disconnect
    qmgr.disconnect()

    # Summary
    if all_ok:
        print("✅ All queues are ready!")
        print()
        print("Next steps:")
        print("1. Start SPBSite: cd spbsite && uvicorn app.main:app --reload")
        print("2. Start BCSrvSqlMq: cd BCSrvSqlMq/python && python -m bcsrvsqlmq.main_srv")
        print("3. Run test: python test_scripts/submit_test_message.py")
        sys.exit(0)
    else:
        print("❌ Some queues have issues. Please check the errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
