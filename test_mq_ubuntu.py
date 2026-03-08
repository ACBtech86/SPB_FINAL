#!/usr/bin/env python3
import pymqi

qmgr_name = 'QM.36266751.01'
channel = 'FINVEST.SVRCONN'
conn_info = 'localhost(1414)'
queue_name = 'QL.36266751.01.ENTRADA.IF'

try:
    # Connect to queue manager
    qmgr = pymqi.connect(qmgr_name, channel, conn_info)
    print(f'✅ Connected to {qmgr_name}')

    # Open queue for input and output
    queue = pymqi.Queue(qmgr, queue_name, pymqi.CMQC.MQOO_INPUT_AS_Q_DEF + pymqi.CMQC.MQOO_OUTPUT)
    print(f'✅ Opened queue {queue_name}')

    # Put test message
    test_msg = b'TEST MESSAGE FROM UBUNTU'
    queue.put(test_msg)
    print(f'✅ Message sent to queue')

    # Get message back
    msg = queue.get()
    print(f'✅ Message received: {msg.decode()}')

    # Close
    queue.close()
    qmgr.disconnect()
    print('✅ Test completed successfully!')

except pymqi.MQMIError as e:
    print(f'❌ MQ Error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
