#!/usr/bin/env python3
"""
Verify IBM MQ configuration from BCSrvSqlMq.ini
"""
import configparser
import pymqi

def verify_mq_config():
    # Read configuration
    config = configparser.ConfigParser()
    config.read('/home/ubuntu/SPB_FINAL/BCSrvSqlMq/BCSrvSqlMq.ini')

    # Get MQ settings
    qmgr_name = config['MQSeries']['QueueManager']
    channel = 'FINVEST.SVRCONN'
    conn_info = 'localhost(1414)'

    # Queue names from config
    queues = [
        config['MQSeries']['QLBacenCidadeReq'],
        config['MQSeries']['QLBacenCidadeRsp'],
        config['MQSeries']['QLBacenCidadeRep'],
        config['MQSeries']['QLBacenCidadeSup'],
        config['MQSeries']['QRCidadeBacenReq'],
        config['MQSeries']['QRCidadeBacenRsp'],
        config['MQSeries']['QRCidadeBacenRep'],
        config['MQSeries']['QRCidadeBacenSup'],
    ]

    print("=" * 70)
    print("IBM MQ Configuration Verification")
    print("=" * 70)
    print(f"Queue Manager: {qmgr_name}")
    print(f"Channel: {channel}")
    print(f"Connection: {conn_info}")
    print("=" * 70)

    try:
        # Connect to queue manager
        qmgr = pymqi.connect(qmgr_name, channel, conn_info)
        print(f"✅ Connected to queue manager: {qmgr_name}\n")

        # Verify each queue
        print("Verifying queues:")
        print("-" * 70)
        for queue_name in queues:
            try:
                queue = pymqi.Queue(qmgr, queue_name, pymqi.CMQC.MQOO_INQUIRE)
                print(f"✅ {queue_name}")
                queue.close()
            except pymqi.MQMIError as e:
                print(f"❌ {queue_name} - Error: {e}")

        print("-" * 70)
        qmgr.disconnect()
        print("\n✅ All MQ configuration verified successfully!")
        print("=" * 70)

    except pymqi.MQMIError as e:
        print(f"❌ MQ Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True

if __name__ == '__main__':
    verify_mq_config()
