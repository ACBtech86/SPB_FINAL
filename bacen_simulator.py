"""
BACEN Message Simulator
Simulates Central Bank responses for SPB testing

Usage:
    py bacen_simulator.py
"""

import asyncio
import asyncpg
from datetime import datetime
from typing import Optional
import xml.etree.ElementTree as ET

# Configuration
DB_CONFIG = {
    'user': 'postgres',
    'password': 'Rama1248',
    'host': 'localhost',
    'port': 5432,
    'database': 'BCSPB'
}

ISPB_FINVEST = '36266751'
ISPB_BACEN = '00038166'


async def simulate_bacen_response(nu_ope: str, request_xml: str) -> tuple:
    """
    Generate a SPB-compliant response XML for a given request

    Args:
        nu_ope: Operation number from request
        request_xml: Request XML content

    Returns:
        Tuple of (response_xml, response_code)
    """
    try:
        # Parse request
        root = ET.fromstring(request_xml)

        # Extract message code
        cod_msg_elem = root.find('.//CodMsg')
        cod_msg = cod_msg_elem.text if cod_msg_elem is not None else 'UNKNOWN'

        # Generate response message code (append R1 for response)
        response_code = f"{cod_msg}R1" if cod_msg is None or not cod_msg.endswith('R1') else cod_msg

        # Build response XML
        response_xml = f'''<?xml version="1.0"?>
<!DOCTYPE SPBDOC SYSTEM "SPBDOC.DTD">
<SPBDOC>
  <BCMSG>
    <Grupo_EmissorMsg>
      <TipoId_Emissor>P</TipoId_Emissor>
      <Id_Emissor>{ISPB_BACEN}</Id_Emissor>
    </Grupo_EmissorMsg>
    <DestinatarioMsg>
      <TipoId_Destinatario>P</TipoId_Destinatario>
      <Id_Destinatario>{ISPB_FINVEST}</Id_Destinatario>
    </DestinatarioMsg>
    <NUOp>{nu_ope}</NUOp>
  </BCMSG>
  <SISMSG>
    <CodMsg>{response_code}</CodMsg>
    <DtHrBC>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}-03:00</DtHrBC>
    <DtMovto>{datetime.now().strftime('%Y-%m-%d')}</DtMovto>
    <SitSTR>
      <CodSitSTR>1</CodSitSTR>
      <DescSitSTR>Sistema em Operacao Normal</DescSitSTR>
    </SitSTR>
  </SISMSG>
</SPBDOC>'''

        return response_xml, response_code

    except Exception as e:
        print(f"Error generating response: {e}")
        return None, None


async def process_pending_messages():
    """
    Main loop: Check for pending messages and generate responses
    """
    print("=" * 60)
    print("BACEN Simulator Starting")
    print("=" * 60)
    print(f"ISPB BACEN: {ISPB_BACEN}")
    print(f"ISPB Finvest: {ISPB_FINVEST}")
    print(f"Database: {DB_CONFIG['database']}")
    print()

    try:
        # Connect to database
        conn = await asyncpg.connect(**DB_CONFIG)
        print(f"[OK] Connected to PostgreSQL: {DB_CONFIG['database']}")

        # Check for pending messages in spb_local_to_bacen
        messages = await conn.fetch('''
            SELECT
                nu_ope,
                db_datetime,
                msg,
                encode(mq_msg_id, 'hex') as msg_id_hex
            FROM spb_local_to_bacen
            WHERE nu_ope IS NOT NULL
            ORDER BY db_datetime DESC
            LIMIT 10
        ''')

        print(f"\nFound {len(messages)} message(s) to process\n")

        if not messages:
            print("[INFO] No pending messages. Submit a message via SPBSite first.")
            print()
            print("To submit a test message:")
            print("1. Open http://localhost:8000")
            print("2. Login (admin/admin)")
            print("3. Go to Messages → Select")
            print("4. Choose a message type (e.g., STR0030)")
            print("5. Fill the form and submit")
            print()
            await conn.close()
            return

        # Process each message
        for msg in messages:
            nu_ope = msg['nu_ope']
            request_xml = msg['msg']
            db_datetime = msg['db_datetime']

            print("[PROCESSING] Message:")
            print(f"   Operation: {nu_ope}")
            print(f"   DateTime: {db_datetime}")
            print(f"   XML length: {len(request_xml)} bytes")

            # Generate response
            response_xml, response_code = await simulate_bacen_response(nu_ope, request_xml)

            if response_xml and response_code:
                # Insert response into spb_bacen_to_local
                try:
                    # Generate new operation number for response (max 23 chars)
                    # Format: ISPB(8) + YYYYMMDD(8) + Sequence(7) = 23 chars
                    now = datetime.now()
                    sequence = int(now.strftime('%H%M%S%f')[:7])  # Use time as sequence
                    response_nu_ope = f"{ISPB_BACEN}{now.strftime('%Y%m%d')}{sequence:07d}"
                    response_datetime = now

                    # Create dummy MQ IDs (in real scenario, these come from IBM MQ)
                    mq_msg_id = b'\x00' * 24  # 24-byte MQ message ID
                    mq_correl_id = b'\x00' * 24
                    mq_header = b'MQHRF2  '  # MQ header format
                    security_header = b''

                    await conn.execute('''
                        INSERT INTO spb_bacen_to_local (
                            mq_msg_id, mq_correl_id, db_datetime,
                            mq_header, security_header, nu_ope, msg,
                            cod_msg, status_msg, flag_proc, mq_qn_origem, mq_datetime
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ''', mq_msg_id, mq_correl_id, response_datetime,
                        mq_header, security_header, response_nu_ope, response_xml,
                        response_code, 'S', 'N', 'QL.REQ.00038166.36266751.01', response_datetime)

                    print("[SUCCESS] Response generated:")
                    print(f"   Response Operation: {response_nu_ope}")
                    print("   Stored in: spb_bacen_to_local")
                    print(f"   XML length: {len(response_xml)} bytes")

                except Exception as e:
                    print(f"[ERROR] Error storing response: {e}")
            else:
                print("[ERROR] Failed to generate response")

            print()

        await conn.close()
        print("=" * 60)
        print("Simulation Complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Check SPBSite monitoring page: http://localhost:8000/monitoring/control/local")
        print("2. View response messages in database:")
        print("   SELECT * FROM spb_bacen_to_local ORDER BY db_datetime DESC;")
        print()

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print()
    asyncio.run(process_pending_messages())
