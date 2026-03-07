"""XML parsing and display utilities.

Replaces the functionality from inc/xmlutilbc.asp (RecordsetToXMLDoc, AddXMLNode, etc.)
and the XML tree viewer from ShwMsg.asp / bwseREM2LOC.xsl.
"""

from lxml import etree


def parse_xml(xml_string: str) -> etree._Element | None:
    """Parse an XML string and return the root element."""
    try:
        if not xml_string or not xml_string.strip():
            return None
        # Remove XML declaration and DOCTYPE if present (for display purposes)
        clean = xml_string.strip()
        return etree.fromstring(clean.encode("utf-8") if isinstance(clean, str) else clean)
    except etree.XMLSyntaxError:
        # Try wrapping in a root element if it fails
        try:
            wrapped = f"<root>{xml_string}</root>"
            return etree.fromstring(wrapped.encode("utf-8"))
        except Exception:
            return None


def xml_to_tree(element: etree._Element, level: int = 0) -> list[dict]:
    """Convert an XML element to a tree structure for template rendering.

    Returns a list of dicts with: tag, text, attributes, level, children.
    """
    node = {
        "tag": element.tag,
        "text": (element.text or "").strip(),
        "attributes": dict(element.attrib),
        "level": level,
        "children": [],
    }

    for child in element:
        node["children"].append(xml_to_tree(child, level + 1))

    return node


def format_datetime_br(dt) -> str:
    """Format a datetime in Brazilian format (dd/mm/yyyy.HH:MM:SS).

    Replaces the FmtDataEuro function from the XSL stylesheets.
    """
    if dt is None:
        return ""
    try:
        if isinstance(dt, str):
            # Handle AAAAMMDDHHMMSS format from old system
            if len(dt) >= 14:
                return f"{dt[6:8]}/{dt[4:6]}/{dt[0:4]}.{dt[8:10]}:{dt[10:12]}:{dt[12:14]}"
            return dt
        return dt.strftime("%d/%m/%Y.%H:%M:%S")
    except (ValueError, AttributeError):
        return str(dt) if dt else ""


def format_currency_br(value) -> str:
    """Format a number as Brazilian currency (R$ X.XXX,XX)."""
    if value is None:
        return "0,00"
    try:
        formatted = f"{float(value):,.2f}"
        # Swap . and , for Brazilian format
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except (ValueError, TypeError):
        return "0,00"
