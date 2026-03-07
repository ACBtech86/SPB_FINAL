"""
Browse MQ Queue (Non-Destructive)
View messages in an IBM MQ queue without removing them.
"""

import pymqi
import sys


# Configuration
QUEUE_MANAGER = 'QM.36266751.01'
CHANNEL = 'FINVEST.SVRCONN'
CONN_INFO = 'localhost(1414)'


def browse_queue(queue_name, max_messages=10):
    """Browse messages in a queue."""

    print("=" * 80)
    print(f"Browsing Queue: {queue_name}")
    print("=" * 80)
    print()

    try:
        # Connect to Queue Manager
        cd = pymqi.CD()
        cd.ChannelName = CHANNEL.encode()
        cd.ConnectionName = CONN_INFO.encode()
        cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
        cd.TransportType = pymqi.CMQC.MQXPT_TCP

        qmgr = pymqi.connect(QUEUE_MANAGER, cd=cd)
        print(f"✅ Connected to Queue Manager: {QUEUE_MANAGER}")
        print()

        # Open queue for browsing
        queue = pymqi.Queue(qmgr, queue_name, pymqi.CMQC.MQOO_BROWSE)
        print(f"✅ Opened queue for browsing: {queue_name}")
        print()

        # Get queue depth
        pcf = pymqi.PCFExecute(qmgr)
        response = pcf.MQCMD_INQUIRE_Q(
            {pymqi.CMQC.MQCA_Q_NAME: queue_name.encode()},
            [pymqi.CMQC.MQIA_CURRENT_Q_DEPTH]
        )
        depth = response[0][pymqi.CMQC.MQIA_CURRENT_Q_DEPTH]

        print(f"Queue Depth: {depth} messages")
        print("-" * 80)
        print()

        if depth == 0:
            print("Queue is empty.")
            queue.close()
            qmgr.disconnect()
            return

        # Browse messages
        md = pymqi.MD()
        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_BROWSE_FIRST

        message_count = 0

        while message_count < max_messages:
            try:
                # Get message
                message = queue.get(None, md, gmo)
                message_count += 1

                print(f"Message {message_count}:")
                print(f"  Message ID: {md.MsgId.hex()}")
                print(f"  Correlation ID: {md.CorrelId.hex()}")
                print(f"  Format: {md.Format.decode().strip()}")
                print(f"  Priority: {md.Priority}")
                print(f"  Persistence: {md.Persistence}")

                # Try to decode message
                try:
                    msg_text = message.decode('utf-8')
                    print(f"  Message (first 200 chars):")
                    print(f"    {msg_text[:200]}")

                    # Look for NU_OPE
                    if '<NumCtrl>' in msg_text:
                        import re
                        match = re.search(r'<NumCtrl>(.*?)</NumCtrl>', msg_text)
                        if match:
                            print(f"  Operation Number: {match.group(1)}")

                except UnicodeDecodeError:
                    print(f"  Message (hex, first 100 bytes): {message[:100].hex()}")

                print()

                # Next message
                gmo.Options = pymqi.CMQC.MQGMO_BROWSE_NEXT

            except pymqi.MQMIError as e:
                if e.comp == pymqi.CMQC.MQCC_WARNING and e.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
                    # No more messages
                    break
                else:
                    raise

        print("-" * 80)
        print(f"Total messages browsed: {message_count}")
        print()

        # Close
        queue.close()
        qmgr.disconnect()

        print("✅ Browse complete")

    except pymqi.MQMIError as e:
        print(f"❌ MQ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python browse_mq_queue.py <queue_name> [max_messages]")
        print()
        print("Examples:")
        print("  python browse_mq_queue.py QR.REQ.36266751.00038166.01")
        print("  python browse_mq_queue.py QL.RSP.00038166.36266751.01 20")
        print()
        print("Common queues:")
        print("  QR.REQ.36266751.00038166.01  - Outbound requests to BACEN")
        print("  QL.RSP.00038166.36266751.01  - Inbound responses from BACEN")
        sys.exit(1)

    queue_name = sys.argv[1]
    max_messages = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    browse_queue(queue_name, max_messages)


if __name__ == '__main__':
    main()
