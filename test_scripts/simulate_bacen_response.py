"""
Simulate BACEN Response
Creates a simulated response from BACEN for testing.
"""

import pymqi
import sys
import argparse
from datetime import datetime
import uuid


# Configuration
QUEUE_MANAGER = 'QM.36266751.01'
CHANNEL = 'FINVEST.SVRCONN'
CONN_INFO = 'localhost(1414)'

# Response types
RESPONSE_TYPES = {
    'COA': 'Confirmation of Arrival',
    'COD': 'Confirmation of Delivery',
    'REP': 'Report',
    'ERR': 'Error'
}


def create_response_message(nu_ope, response_type='COA', error_code=None):
    """Create a response message XML."""
    now = datetime.now()

    if response_type == 'ERR':
        # Error response
        error_code = error_code or '9999'
        message = f'''<?xml version="1.0" encoding="UTF-8"?>
<DOC>
    <BCMSG>
        <IdentdPartDestinat>36266751</IdentdPartDestinat>
        <IdentdPartRemt>00038166</IdentdPartRemt>
        <IdentdOperad>
            <NumCtrl>{nu_ope}</NumCtrl>
            <DtHrOp>{now.strftime('%Y-%m-%dT%H:%M:%S')}</DtHrOp>
        </IdentdOperad>
        <Grupo_Seq>
            <NumSeq>1</NumSeq>
        </Grupo_Seq>
    </BCMSG>
    <SISMSG>
        <CodMsg>SPB9999</CodMsg>
        <ErrorResponse>
            <ErrorCode>{error_code}</ErrorCode>
            <ErrorDescription>Simulated error for testing</ErrorDescription>
            <OriginalOperation>{nu_ope}</OriginalOperation>
        </ErrorResponse>
    </SISMSG>
</DOC>'''

    elif response_type == 'COA':
        # Confirmation of Arrival
        message = f'''<?xml version="1.0" encoding="UTF-8"?>
<DOC>
    <BCMSG>
        <IdentdPartDestinat>36266751</IdentdPartDestinat>
        <IdentdPartRemt>00038166</IdentdPartRemt>
        <IdentdOperad>
            <NumCtrl>{nu_ope}_COA</NumCtrl>
            <DtHrOp>{now.strftime('%Y-%m-%dT%H:%M:%S')}</DtHrOp>
        </IdentdOperad>
        <Grupo_Seq>
            <NumSeq>1</NumSeq>
        </Grupo_Seq>
    </BCMSG>
    <SISMSG>
        <CodMsg>SPB0002</CodMsg>
        <ConfirmationOfArrival>
            <Status>RECEIVED</Status>
            <OriginalOperation>{nu_ope}</OriginalOperation>
            <ReceivedAt>{now.isoformat()}</ReceivedAt>
        </ConfirmationOfArrival>
    </SISMSG>
</DOC>'''

    elif response_type == 'COD':
        # Confirmation of Delivery
        message = f'''<?xml version="1.0" encoding="UTF-8"?>
<DOC>
    <BCMSG>
        <IdentdPartDestinat>36266751</IdentdPartDestinat>
        <IdentdPartRemt>00038166</IdentdPartRemt>
        <IdentdOperad>
            <NumCtrl>{nu_ope}_COD</NumCtrl>
            <DtHrOp>{now.strftime('%Y-%m-%dT%H:%M:%S')}</DtHrOp>
        </IdentdOperad>
        <Grupo_Seq>
            <NumSeq>1</NumSeq>
        </Grupo_Seq>
    </BCMSG>
    <SISMSG>
        <CodMsg>SPB0003</CodMsg>
        <ConfirmationOfDelivery>
            <Status>PROCESSED</Status>
            <OriginalOperation>{nu_ope}</OriginalOperation>
            <ProcessedAt>{now.isoformat()}</ProcessedAt>
            <Result>SUCCESS</Result>
        </ConfirmationOfDelivery>
    </SISMSG>
</DOC>'''

    else:  # REP
        # Report
        message = f'''<?xml version="1.0" encoding="UTF-8"?>
<DOC>
    <BCMSG>
        <IdentdPartDestinat>36266751</IdentdPartDestinat>
        <IdentdPartRemt>00038166</IdentdPartRemt>
        <IdentdOperad>
            <NumCtrl>{nu_ope}_REP</NumCtrl>
            <DtHrOp>{now.strftime('%Y-%m-%dT%H:%M:%S')}</DtHrOp>
        </IdentdOperad>
        <Grupo_Seq>
            <NumSeq>1</NumSeq>
        </Grupo_Seq>
    </BCMSG>
    <SISMSG>
        <CodMsg>SPB0004</CodMsg>
        <Report>
            <ReportType>STATUS</ReportType>
            <OriginalOperation>{nu_ope}</OriginalOperation>
            <Details>Simulated report for testing</Details>
        </Report>
    </SISMSG>
</DOC>'''

    return message


def send_response(nu_ope, response_type='COA', error_code=None):
    """Send simulated response to MQ queue."""

    print("=" * 80)
    print("Simulate BACEN Response")
    print("=" * 80)
    print()
    print(f"Operation Number: {nu_ope}")
    print(f"Response Type: {response_type} - {RESPONSE_TYPES.get(response_type, 'Unknown')}")
    if error_code:
        print(f"Error Code: {error_code}")
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

        # Determine response queue based on type
        if response_type == 'REP':
            queue_name = 'QL.REP.00038166.36266751.01'
        else:
            queue_name = 'QL.RSP.00038166.36266751.01'

        # Open queue
        queue = pymqi.Queue(qmgr, queue_name, pymqi.CMQC.MQOO_OUTPUT)
        print(f"✅ Opened queue: {queue_name}")
        print()

        # Create response message
        message_text = create_response_message(nu_ope, response_type, error_code)
        message_bytes = message_text.encode('utf-8')

        # Set message descriptor
        md = pymqi.MD()
        md.Format = pymqi.CMQC.MQFMT_STRING
        md.Persistence = pymqi.CMQC.MQPER_PERSISTENT
        md.Priority = 0

        # Set correlation ID (simulate correlation with original message)
        # In real scenario, this would be the original message ID
        correl_id = nu_ope.encode('utf-8').ljust(24, b'\x00')
        md.CorrelId = correl_id[:24]

        # Put message
        queue.put(message_bytes, md)

        print("✅ Response message sent successfully!")
        print()
        print("Message Details:")
        print(f"  - Message ID: {md.MsgId.hex()}")
        print(f"  - Correlation ID: {md.CorrelId.hex()}")
        print(f"  - Queue: {queue_name}")
        print(f"  - Size: {len(message_bytes)} bytes")
        print()
        print("Message Preview:")
        print("-" * 80)
        print(message_text[:500])
        if len(message_text) > 500:
            print("...")
        print("-" * 80)
        print()

        # Close
        queue.close()
        qmgr.disconnect()

        print("Next steps:")
        print("1. BCSrvSqlMq should pick up this response automatically")
        print("2. Check BCSrvSqlMq logs")
        print("3. Verify database update:")
        print(f"   SELECT * FROM spb_bacen_to_local WHERE nu_ope = '{nu_ope}';")
        print()

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
    parser = argparse.ArgumentParser(description='Simulate BACEN response message')
    parser.add_argument('--operation-number', '-o', required=True,
                        help='Operation number (NU_OPE) to respond to')
    parser.add_argument('--response-type', '-t', choices=['COA', 'COD', 'REP', 'ERR'],
                        default='COA', help='Response type (default: COA)')
    parser.add_argument('--error-code', '-e', help='Error code (for ERR type)')

    args = parser.parse_args()

    send_response(args.operation_number, args.response_type, args.error_code)


if __name__ == '__main__':
    main()
