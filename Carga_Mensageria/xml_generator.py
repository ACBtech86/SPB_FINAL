"""
XML and XSL schema generation for SPB messages.
Replaces GeraschemaXml(), GeraschemaXsl(), AddXmlNode(), AddXmlNodeEx()
from the VB6 Etapas_Carga.frm.
"""

import os
from xml.dom import minidom


BANCO_CIDADE_ISPB = "61377677"


def encode_html_entities(text: str) -> str:
    """Encode characters with ordinal > 127 as HTML hex entities.

    Replaces the VB6 character-by-character loop (Etapas_Carga.frm lines 660-668).
    """
    result = []
    for ch in text:
        if ord(ch) > 127:
            result.append(f"&#x{ord(ch):X};")
        else:
            result.append(ch)
    return "".join(result)


def _add_xml_node(doc, parent, name, value="", namespace=""):
    """Create and append an XML element node.

    Replaces AddXmlNode / AddXmlNodeEx from VB6.
    """
    if namespace:
        node = doc.createElementNS(namespace, name)
    else:
        node = doc.createElement(name)
    if value:
        node.appendChild(doc.createTextNode(value.strip()))
    parent.appendChild(node)
    return node


class XmlSchemaGenerator:
    """Generates XML form schemas from SPB_MSGFIELD records.

    Replaces GeraschemaXml() and the DocArray/NivelArray state machine.
    """

    def __init__(self):
        self.doc = None
        self.level_stack = []  # replaces DocArray() + NivelArray
        self.current_msg_id = ""
        self.is_initialized = False

    def start_new_message(self, msg_id, msg_tag, msg_descr):
        """Called when MSG_SEQ == '01'. Creates a new XML document with FORM root."""
        self.is_initialized = True
        self.level_stack = []
        self.doc = minidom.Document()

        form_node = _add_xml_node(self.doc, self.doc, "FORM")
        form_node.setAttribute("name", msg_id)
        form_node.setAttribute("status", "input")
        form_node.setAttribute("title", msg_descr)

        fieldset = _add_xml_node(self.doc, form_node, "FIELDSET")
        fieldset.setAttribute("spbtag", msg_tag)
        fieldset.setAttribute("codgrade", "")
        fieldset.setAttribute("destino", "")
        self.level_stack.append(fieldset)
        self.current_msg_id = msg_id

    def process_field(self, msg_id, msg_seq, msg_cpotag, msg_cponome,
                      msg_cpoobrig, msg_cpoformato, msg_cpotipo, msg_cpotam,
                      db_manager):
        """Process one record from SPB_MSGFIELD LEFT JOIN SPB_DICIONARIO.

        Handles:
        - Repet_ prefix -> FIELDREPET (push level)
        - Grupo_ prefix -> FIELDGRUPO (push level)
        - / prefix -> pop level
        - Otherwise -> FIELD node with type/size/attribute logic
        """
        # --- Repet_ prefix ---
        if msg_cpotag[:6] == "Repet_":
            parent = self.level_stack[-1]
            node = _add_xml_node(self.doc, parent, "FIELDREPET")
            node.setAttribute("name", msg_cpotag)
            node.setAttribute("spbtag", msg_cpotag)
            node.setAttribute("occurs", "1")
            node.setAttribute("label", msg_cponome)
            if msg_cpoobrig == "X":
                node.setAttribute("req", "yes")
            else:
                node.setAttribute("req", "no")
            self.level_stack.append(node)
            return

        # --- Grupo_ prefix ---
        if msg_cpotag[:6] == "Grupo_":
            parent = self.level_stack[-1]
            node = _add_xml_node(self.doc, parent, "FIELDGRUPO")
            node.setAttribute("name", msg_cpotag)
            node.setAttribute("spbtag", msg_cpotag)
            node.setAttribute("label", msg_cponome)
            if msg_cpoobrig == "X":
                node.setAttribute("req", "yes")
            else:
                node.setAttribute("req", "no")
                node.setAttribute("checked", "N")
            self.level_stack.append(node)
            return

        # --- Closing tag (/) ---
        if msg_cpotag[:1] == "/":
            if len(self.level_stack) > 1:
                self.level_stack.pop()
            return

        # --- Regular FIELD ---
        parent = self.level_stack[-1]
        field_node = _add_xml_node(self.doc, parent, "FIELD")

        # Determine field format type
        formato_lower = msg_cpoformato.lower()
        if "alfanum" in formato_lower:  # alfanumérico
            field_format = "text"
        elif "num" in formato_lower:  # numérico
            field_format = "number"
        else:
            field_format = "hidden"

        # Override by data type
        tipo_lower = msg_cpotipo.lower()
        if tipo_lower == "data":
            field_format = "date"
            msg_cpotam = "10"
        elif tipo_lower == "data hora":
            field_format = "datetime"
            msg_cpotam = "19"
        elif tipo_lower == "hora":
            field_format = "time"
            msg_cpotam = "8"

        # Calculate size (handle comma-separated integer,decimal)
        if "," in msg_cpotam:
            parts = msg_cpotam.split(",", 1)
            try:
                int_part = int(parts[0])
                dec_part = int(parts[1])
                if dec_part > 0:
                    msg_cpotam = str(int_part + dec_part + 1)
                else:
                    msg_cpotam = str(int_part)
            except ValueError:
                pass
        else:
            try:
                msg_cpotam = str(int(msg_cpotam)) if msg_cpotam else ""
            except ValueError:
                pass

        # Set basic attributes
        field_node.setAttribute("type", field_format)
        field_node.setAttribute("name", msg_cpotag)
        field_node.setAttribute("spbtag", msg_cpotag)
        field_node.setAttribute("size", msg_cpotam)

        # Special readonly fields
        if msg_cpotag == "CodMsg":
            field_node.setAttribute("readonly", "yes")
            field_node.setAttribute("initial", msg_id)
        elif msg_cpotag == "ISPBIF":
            field_node.setAttribute("readonly", "yes")
            field_node.setAttribute("initial", BANCO_CIDADE_ISPB)
        elif msg_cpotag == "ISPBIFDebtd":
            field_node.setAttribute("readonly", "yes")
            field_node.setAttribute("initial", BANCO_CIDADE_ISPB)
        elif msg_cpoobrig == "X":
            field_node.setAttribute("req", "yes")

        # Date/time initial values
        if tipo_lower == "data":
            field_node.setAttribute("initial", "today")
        elif tipo_lower == "hora":
            field_node.setAttribute("initial", "time")
        elif tipo_lower == "data hora":
            field_node.setAttribute("initial", "now")

        field_node.setAttribute("label", msg_cponome)
        field_node.setAttribute("dominio", msg_cpotipo)

        # Check if domain has help entries in SPB_DOMINIOS
        if db_manager and msg_cpotipo:
            sql = (
                "SELECT DISTINCT TipoDado FROM SPB_DOMINIOS "
                f"WHERE TipoDado = '{msg_cpotipo}'"
            )
            rows = db_manager.execute_query(sql)
            if rows:
                field_node.setAttribute("help", msg_cpotipo)
            else:
                if msg_cpotipo == "ISPB":
                    if msg_cpotag not in ("ISPBIF", "ISPBIFDebtd"):
                        field_node.setAttribute("help", msg_cpotipo)

        # NumCtrlIF gets gerar attribute
        if msg_cpotag == "NumCtrlIF":
            field_node.setAttribute("gerar", msg_cpotag)

    def get_xml_string(self) -> str:
        """Return current document as XML string."""
        if self.doc is None:
            return ""
        return self.doc.toxml()


class XslSchemaGenerator:
    """Loads the spbmodelo.xsl template for each message.

    Replaces GeraschemaXsl(). The VB6 active code simply loads the XSL
    template per message (most of the original logic was commented out).
    """

    def __init__(self, xsl_template_path: str):
        self.template_path = xsl_template_path
        self.doc = None
        self.is_initialized = False

    def start_new_message(self):
        """Load the spbmodelo.xsl template for a new message."""
        self.doc = minidom.parse(self.template_path)
        self.is_initialized = True

    def get_xsl_string(self) -> str:
        """Return the XSL document as XML string."""
        if self.doc is None:
            return ""
        return self.doc.toxml()
