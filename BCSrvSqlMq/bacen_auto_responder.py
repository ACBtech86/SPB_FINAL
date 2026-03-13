#!/usr/bin/env python3
"""
Automated BACEN Response Service for Testing

This is an automated version of the bacen_simulator.py that:
- Listens to Finvest outbound queues (IF staging)
- Automatically generates and sends responses
- Can be used in automated tests

Based on: BCSrvSqlMq/python/scripts/bacen_simulator.py
"""

import os
import sys
import threading
import time
from datetime import datetime
from typing import Optional, Dict

# Add python/ to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_DIR = os.path.join(SCRIPT_DIR, 'python')
sys.path.insert(0, PYTHON_DIR)

import pymqi
import pymqi.CMQC

from bcsrvsqlmq.msg_sgr import SECHDR_SIZE

# MQ Configuration
QM_NAME = 'QM.36266751.01'
CHANNEL = 'FINVEST.SVRCONN'
CONN_INFO = 'localhost(1414)'

# Queues where Finvest PUTS outbound messages (Bacen reads these)
FINVEST_OUTBOUND_QUEUES = {
    'REQ': 'QL.36266751.01.ENTRADA.IF',
    'RSP': 'QL.36266751.01.SAIDA.IF',
    'REP': 'QL.36266751.01.REPORT.IF',
    'SUP': 'QL.36266751.01.SUPORTE.IF',
}

# Queues where Bacen PUTS inbound messages (Finvest reads these)
# When BACEN responds to Finvest's REQ (GEN0001/GEN0002/GEN0003), the response
# goes to the RSP queue (CBacenRsp handles GEN0001R1/GEN0002R1/GEN0003R1).
# The REQ queue is for BACEN-initiated requests TO Finvest (different flow).
FINVEST_INBOUND_QUEUES = {
    'REQ': 'QL.RSP.00038166.36266751.01',  # Responses to Finvest's requests → RSP queue
    'RSP': 'QL.RSP.00038166.36266751.01',
    'REP': 'QL.REP.00038166.36266751.01',
    'SUP': 'QL.SUP.00038166.36266751.01',
}

ISPB_BACEN = '00038166'
ISPB_FINVEST = '36266751'


class BacenAutoResponder:
    """Automated BACEN response service for testing."""

    def __init__(self):
        self.qmgr = None
        self.running = False
        self.messages_processed = 0
        self.responses_sent = 0
        self.errors = []

    def connect_mq(self):
        """Connect to queue manager."""
        try:
            self.qmgr = pymqi.connect(QM_NAME, CHANNEL, CONN_INFO)
            return True
        except pymqi.MQMIError as e:
            self.errors.append(f"MQ connection error: {e}")
            return False

    def disconnect_mq(self):
        """Disconnect from queue manager."""
        if self.qmgr:
            try:
                self.qmgr.disconnect()
            except:
                pass
            self.qmgr = None

    def decode_payload(self, payload: bytes) -> str:
        """Decode message payload to string."""
        # Try different encodings
        for encoding in ['utf-8', 'utf-16-be', 'utf-16-le', 'latin-1']:
            try:
                # For UTF-16BE (SPB standard), byte-swap first
                if encoding == 'utf-16-be' and len(payload) % 2 == 0:
                    swapped = bytearray(len(payload))
                    for i in range(0, len(payload) - 1, 2):
                        swapped[i] = payload[i + 1]
                        swapped[i + 1] = payload[i]
                    text = bytes(swapped).decode('utf-16-le').rstrip('\x00')
                    if '<' in text and '>' in text:  # Looks like XML
                        return text
                else:
                    text = payload.decode(encoding).rstrip('\x00')
                    if '<' in text and '>' in text:
                        return text
            except:
                continue

        # Fallback to UTF-8 with errors ignored
        return payload.decode('utf-8', errors='ignore').rstrip('\x00')

    def encode_payload(self, xml_text: str) -> bytes:
        """Encode XML string to payload (UTF-16BE)."""
        utf16le = xml_text.encode('utf-16-le')
        # Byte-swap to UTF-16BE
        be = bytearray(len(utf16le))
        for i in range(0, len(utf16le) - 1, 2):
            be[i] = utf16le[i + 1]
            be[i + 1] = utf16le[i]
        return bytes(be)

    def extract_message_info(self, xml_text: str) -> Dict[str, str]:
        """Extract key information from request XML."""
        import xml.etree.ElementTree as ET

        info = {
            'nu_ope': '',
            'cod_msg': '',
            'emissor': '',
            'destinatario': ''
        }

        try:
            root = ET.fromstring(xml_text)

            # Try to find fields with or without namespace
            for elem in root.iter():
                tag = elem.tag.split('}')[-1]  # Remove namespace

                if tag == 'NUOp' and elem.text:
                    info['nu_ope'] = elem.text.strip()
                elif tag == 'CodMsg' and elem.text:
                    info['cod_msg'] = elem.text.strip()
                elif tag == 'IdentdEmissor' and elem.text:
                    info['emissor'] = elem.text.strip()
                elif tag == 'IdentdDestinatario' and elem.text:
                    info['destinatario'] = elem.text.strip()
                # SPBDOC format: Id_Emissor / Id_Destinatario
                elif tag == 'Id_Emissor' and elem.text:
                    info['emissor'] = elem.text.strip()
                elif tag == 'Id_Destinatario' and elem.text:
                    info['destinatario'] = elem.text.strip()

            # SPBDOC format: message type is the first child tag of SISMSG
            if not info['cod_msg']:
                sismsg = root.find('SISMSG')
                if sismsg is not None:
                    for child in sismsg:
                        tag = child.tag.split('}')[-1]
                        if not tag.startswith('/'):
                            info['cod_msg'] = tag
                            break
        except:
            pass

        return info

    def generate_response(self, request_info: Dict[str, str]) -> str:
        """Generate BACEN response XML.

        Maps SPB request types to their correct response types:
          GEN0001 (Echo request)    → GEN0001R1 with GENReqECORespReq
          GEN0002 (Log request)     → GEN0002R1 with GENReqLOGRespReq
          GEN0003 (UltMsg request)  → GEN0003R1 with GENReqUltMsgRespReq
        """
        cod_msg = request_info['cod_msg']
        nu_ope = request_info['nu_ope']

        # Map request → response code (all requests get R1 suffix)
        response_cod = cod_msg + 'R1'

        # Map request → inner response tag expected by CBacenRsp
        resp_tag_map = {
            'GEN0001R1': 'GENReqECORespReq',
            'GEN0002R1': 'GENReqLOGRespReq',
            'GEN0003R1': 'GENReqUltMsgRespReq',
        }
        inner_tag = resp_tag_map.get(response_cod, 'GENReqECORespReq')

        now = datetime.now()
        response_nu_ope = f"{ISPB_BACEN}{now.strftime('%Y%m%d%H%M%S')}"

        response_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<DOC xmlns="http://www.bcb.gov.br/SPB/{response_cod}.xsd">
  <BCMSG>
    <IdentdEmissor>{ISPB_BACEN}</IdentdEmissor>
    <IdentdDestinatario>{ISPB_FINVEST}</IdentdDestinatario>
    <DomSist>SPB</DomSist>
    <NUOp>{response_nu_ope}</NUOp>
  </BCMSG>
  <SISMSG>
    <{response_cod}>
      <CodMsg>{response_cod}</CodMsg>
      <{inner_tag}>
        <SitRetReqECO>
          <CodSitRetReq>00</CodSitRetReq>
          <DescrSitRetReq>Processado com Sucesso - BACEN Simulator</DescrSitRetReq>
        </SitRetReqECO>
        <NumCtrlIF>BACEN{now.strftime('%H%M%S')}</NumCtrlIF>
        <DtHrBC>{now.strftime('%Y-%m-%dT%H:%M:%S')}</DtHrBC>
      </{inner_tag}>
    </{response_cod}>
  </SISMSG>
</DOC>'''

        return response_xml

    def process_message(self, raw_msg: bytes, msg_id: bytes, correl_id: bytes) -> Optional[str]:
        """Process a single message and return response."""
        try:
            # Skip SECHDR (always prepended, even in clear-text mode)
            payload = raw_msg[SECHDR_SIZE:] if len(raw_msg) > SECHDR_SIZE else raw_msg
            xml_text = self.decode_payload(payload)

            if not xml_text or '<' not in xml_text:
                return None

            # Extract message info
            info = self.extract_message_info(xml_text)

            if not info['nu_ope'] or not info['cod_msg']:
                return None

            # Generate response
            response_xml = self.generate_response(info)

            return response_xml

        except Exception as e:
            self.errors.append(f"Error processing message: {e}")
            return None

    def poll_queue_once(self, queue_type: str, queue_name: str):
        """Poll a queue once for messages."""
        try:
            queue = pymqi.Queue(self.qmgr, queue_name,
                               pymqi.CMQC.MQOO_INPUT_SHARED)

            while True:
                try:
                    md = pymqi.MD()
                    gmo = pymqi.GMO()
                    gmo.Options = (pymqi.CMQC.MQGMO_NO_WAIT |
                                  pymqi.CMQC.MQGMO_FAIL_IF_QUIESCING)

                    raw_msg = queue.get(None, md, gmo)
                    self.messages_processed += 1

                    # Process and generate response
                    response_xml = self.process_message(raw_msg, md.MsgId, md.CorrelId)

                    if response_xml:
                        # Send response to corresponding inbound queue
                        response_queue_name = FINVEST_INBOUND_QUEUES.get(queue_type)
                        if response_queue_name:
                            self.send_response(response_queue_name, response_xml, md.MsgId)

                except pymqi.MQMIError as e:
                    if e.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
                        break
                    raise

            queue.close()

        except pymqi.MQMIError as e:
            if e.reason != pymqi.CMQC.MQRC_Q_MGR_NOT_AVAILABLE:
                self.errors.append(f"Error polling {queue_name}: {e}")

    def send_response(self, queue_name: str, response_xml: str, correl_id: bytes):
        """Send response message to queue."""
        try:
            queue = pymqi.Queue(self.qmgr, queue_name, pymqi.CMQC.MQOO_OUTPUT)

            # Prepend clear-text SECHDR
            from bcsrvsqlmq.msg_sgr import SECHDR, SECHDR_VERSION_CLEAR
            sec_hdr = SECHDR()
            sec_hdr.Versao = SECHDR_VERSION_CLEAR
            sechdr_bytes = sec_hdr.pack()

            # Encode response XML as UTF-8 (clear-text mode, matching BCSrvSqlMq expectation)
            payload = sechdr_bytes + response_xml.encode('utf-8')

            # Create message descriptor
            md = pymqi.MD()
            md.Format = pymqi.CMQC.MQFMT_STRING
            md.Persistence = pymqi.CMQC.MQPER_PERSISTENT
            md.CorrelId = correl_id  # Match correlation ID

            # Put message
            queue.put(payload, md)
            queue.close()

            self.responses_sent += 1

        except pymqi.MQMIError as e:
            self.errors.append(f"Error sending response to {queue_name}: {e}")

    def poll_all_queues_once(self):
        """Poll all outbound queues once."""
        if not self.qmgr:
            if not self.connect_mq():
                return

        for queue_type, queue_name in FINVEST_OUTBOUND_QUEUES.items():
            self.poll_queue_once(queue_type, queue_name)

    def run_continuous(self, duration_seconds: int = 30, poll_interval: float = 1.0):
        """Run continuous polling for specified duration."""
        if not self.connect_mq():
            return False

        self.running = True
        start_time = time.time()

        print(f"BACEN Auto Responder started (duration: {duration_seconds}s)")
        print(f"Polling interval: {poll_interval}s")
        print()

        try:
            while self.running and (time.time() - start_time) < duration_seconds:
                self.poll_all_queues_once()
                time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\nStopped by user")
        finally:
            self.running = False
            self.disconnect_mq()

        return True

    def get_stats(self) -> Dict:
        """Get processing statistics."""
        return {
            'messages_processed': self.messages_processed,
            'responses_sent': self.responses_sent,
            'errors': len(self.errors),
            'error_messages': self.errors
        }


def run_in_background(duration_seconds: int = 30, poll_interval: float = 1.0) -> BacenAutoResponder:
    """Run BACEN responder in background thread."""
    responder = BacenAutoResponder()

    def worker():
        responder.run_continuous(duration_seconds, poll_interval)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    # Give it a moment to start
    time.sleep(0.5)

    return responder


if __name__ == '__main__':
    # Test mode: run for 30 seconds
    responder = BacenAutoResponder()
    responder.run_continuous(duration_seconds=30, poll_interval=1.0)

    # Show stats
    stats = responder.get_stats()
    print("\n" + "=" * 60)
    print("BACEN Auto Responder Statistics")
    print("=" * 60)
    print(f"Messages Processed: {stats['messages_processed']}")
    print(f"Responses Sent:     {stats['responses_sent']}")
    print(f"Errors:             {stats['errors']}")

    if stats['error_messages']:
        print("\nErrors:")
        for err in stats['error_messages']:
            print(f"  - {err}")

    print("=" * 60)
