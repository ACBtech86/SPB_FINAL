#!/usr/bin/env python3
"""
Load SPB message catalog data from XSD schemas into the unified catalog database.

NOTE: The preferred way to manage catalog data is via Carga_Mensageria (main.py).
This script is provided as a standalone alternative for BCSrvSqlMq environments
where Carga_Mensageria is not available.

Target database: banuxSPB

Tables populated:
  - SPB_MENSAGEM     - Message definitions
  - SPB_DICIONARIO   - Data dictionary (field types)
  - SPB_MSGFIELD     - Message field structures

Usage:
    python load_catalog_from_xsd.py
    python load_catalog_from_xsd.py /path/to/spb_schemas.zip
"""

import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import psycopg2
from psycopg2 import sql

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'banuxSPB',
    'user': 'postgres',
    'password': 'Rama1248',
}

# Default XSD schemas zip file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ZIP_PATH = os.path.join(SCRIPT_DIR, '../Carga_Mensageria/spb_schemas.zip')

# XML namespaces
XS = "{http://www.w3.org/2001/XMLSchema}"
CAT = "{http://www.bcb.gov.br/catalogomsg}"


def find_cat_text(elem, cat_tag):
    """Find text inside a cat: namespaced child element."""
    node = elem.find(f".//{CAT}{cat_tag}")
    if node is not None and node.text:
        return node.text.strip()
    return ""


def parse_simple_types(root):
    """Parse all xs:simpleType definitions and return a dict name→info."""
    types = {}
    for st in root.findall(f"{XS}simpleType"):
        name = st.get("name")
        if not name:
            continue

        info = {
            "name": name,
            "base": "",
            "maxLength": "",
            "totalDigits": "",
            "fractionDigits": "",
            "description": "",
            "format": "",
            "size": "",
            "enumerations": 0,
        }

        # Description
        doc = st.find(f".//{CAT}DescricaoTipo")
        if doc is not None and doc.text:
            info["description"] = doc.text.strip()

        # Restriction facets
        restr = st.find(f"{XS}restriction")
        if restr is not None:
            info["base"] = restr.get("base", "")
            enum_count = 0
            for child in restr:
                local_tag = child.tag.split("}")[-1]
                if local_tag in ("maxLength", "totalDigits", "fractionDigits"):
                    info[local_tag] = child.get("value", "")
                elif local_tag == "enumeration":
                    enum_count += 1
            info["enumerations"] = enum_count

        # Derive format and size
        base = info["base"]
        if "string" in base:
            info["format"] = "Alfanumérico"
            if info["maxLength"]:
                info["size"] = info["maxLength"]
        elif "decimal" in base:
            info["format"] = "Numérico"
            total = info["totalDigits"]
            frac = info["fractionDigits"]
            if total and frac:
                info["size"] = f"{total},{frac}"
            elif total:
                info["size"] = total
        elif "integer" in base or "int" in base:
            info["format"] = "Numérico"
            if info["totalDigits"]:
                info["size"] = info["totalDigits"]

        types[name] = info
    return types


def parse_all_elements(root):
    """Parse all xs:element definitions in the schema recursively."""
    fields = []
    idx = 0

    # Find all elements in all complex types
    for ct in root.findall(f".//{XS}complexType"):
        seq = ct.find(f"{XS}sequence")
        if seq is None:
            continue

        for elem in seq.findall(f"{XS}element"):
            idx += 1
            elem_name = elem.get("name", "")
            elem_type = elem.get("type", "")
            min_occurs = elem.get("minOccurs", "1")
            max_occurs = elem.get("maxOccurs", "1")

            # Get field description from annotation
            descr = ""
            annot = elem.find(f"{XS}annotation/{XS}documentation")
            if annot is not None:
                descr_elem = annot.find(f"{CAT}DescricaoCampo")
                if descr_elem is not None and descr_elem.text:
                    descr = descr_elem.text.strip()

            obrig = "X" if min_occurs == "1" else ""

            if elem_name:  # Only add if it has a name
                fields.append({
                    "seq": idx,
                    "tag": elem_name,
                    "type": elem_type,
                    "description": descr,
                    "obrig": obrig,
                    "maxOccurs": max_occurs,
                })

    return fields


def process_xsd_file(xsd_content, filename, cur, conn):
    """Process a single XSD file and insert data into PostgreSQL."""
    try:
        root = ET.fromstring(xsd_content)
    except ET.ParseError as e:
        print(f"  ⚠️  XML parse error: {e}")
        return False

    # Extract message ID from filename (e.g., BMC0004.XSD -> BMC0004)
    msg_id = os.path.splitext(os.path.basename(filename))[0]

    # Try to find message info in annotation
    evento_text = find_cat_text(root, "Evento")
    descr_text = find_cat_text(root, "Descricao")

    # Get description from Evento or Descricao
    msg_descr = descr_text if descr_text else evento_text

    # Try to find the root element name for msg_tag
    root_elem = root.find(f"{XS}element")
    msg_tag = root_elem.get("name") if root_elem is not None else msg_id

    # Emissor and destinatario (not always available)
    msg_emissor = ""
    msg_dest = ""

    if not msg_id:
        print("  ⚠️  No message ID found")
        return False

    # Parse types for dictionary
    types = parse_simple_types(root)

    # Parse all elements in the schema
    fields = parse_all_elements(root)

    if not fields:
        # Skip files with no elements (might be just type definitions)
        return True  # Return True to not count as failed

    # Insert into SPB_MENSAGEM
    cur.execute("""
        INSERT INTO SPB_MENSAGEM (MSG_ID, MSG_DESCR)
        VALUES (%s, %s)
        ON CONFLICT (MSG_ID) DO UPDATE
        SET MSG_DESCR = EXCLUDED.MSG_DESCR
    """, (msg_id, msg_descr))

    # Insert types into SPB_DICIONARIO
    for type_name, type_info in types.items():
        cur.execute("""
            INSERT INTO SPB_DICIONARIO
            (MSG_CPOTAG, MSG_CPOTIPO, MSG_CPOTAM, MSG_CPOFORM)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (MSG_CPOTAG) DO UPDATE
            SET MSG_CPOTIPO = EXCLUDED.MSG_CPOTIPO,
                MSG_CPOTAM = EXCLUDED.MSG_CPOTAM,
                MSG_CPOFORM = EXCLUDED.MSG_CPOFORM
        """, (
            type_name,
            type_info["description"][:50] if type_info["description"] else type_name,
            type_info["size"],
            type_info["format"]
        ))

    # Insert fields into SPB_MSGFIELD
    for field in fields:
        # Map COD_GRADE - using a default value for now
        cod_grade = "PROD"  # Default grade

        cur.execute("""
            INSERT INTO SPB_MSGFIELD
            (COD_GRADE, MSG_ID, MSG_TAG, MSG_DESCR, MSG_EMISSOR, MSG_DESTINATARIO,
             MSG_SEQ, MSG_CPOTAG, MSG_CPONOME, MSG_CPOOBRIG)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cod_grade,
            msg_id,
            msg_tag,
            msg_descr,
            msg_emissor,
            msg_dest,
            field["seq"],
            field["tag"],
            field["description"][:200] if field["description"] else field["tag"],
            field["obrig"]
        ))

    conn.commit()
    return True


def load_catalog_from_xsd(zip_path):
    """Load catalog data from XSD schemas zip file."""
    print("=" * 70)
    print("Loading SPB Catalog from XSD Schemas")
    print("=" * 70)
    print(f"Source: {zip_path}")
    print(f"Database: {DB_CONFIG['dbname']}")
    print("=" * 70)

    if not os.path.exists(zip_path):
        print(f"❌ Error: File not found: {zip_path}")
        return False

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("✅ Connected to database\n")
    except psycopg2.Error as e:
        print(f"❌ Database connection error: {e}")
        return False

    # Clear existing catalog data
    print("Clearing existing catalog data...")
    try:
        cur.execute("DELETE FROM SPB_MSGFIELD")
        cur.execute("DELETE FROM SPB_MENSAGEM")
        cur.execute("DELETE FROM SPB_DICIONARIO")
        conn.commit()
        print("✅ Existing data cleared\n")
    except psycopg2.Error as e:
        print(f"❌ Error clearing data: {e}")
        conn.rollback()
        return False

    # Process XSD files from zip
    print("Processing XSD files...\n")
    processed = 0
    failed = 0

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            xsd_files = [f for f in zf.namelist()
                        if f.upper().endswith('.XSD') and not f.endswith('/')]
            total = len(xsd_files)

            for idx, filename in enumerate(xsd_files, 1):
                print(f"[{idx}/{total}] {filename:50}", end=" ")
                try:
                    xsd_content = zf.read(filename)
                    if process_xsd_file(xsd_content, filename, cur, conn):
                        print("✅")
                        processed += 1
                    else:
                        print("⚠️  Skipped")
                        failed += 1
                except Exception as e:
                    print(f"❌ Error: {e}")
                    failed += 1

    except zipfile.BadZipFile:
        print(f"❌ Error: Invalid zip file: {zip_path}")
        return False
    except Exception as e:
        print(f"❌ Error processing zip file: {e}")
        return False
    finally:
        conn.commit()

    # Show summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    # Count records
    cur.execute("SELECT COUNT(*) FROM SPB_MENSAGEM")
    msg_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM SPB_DICIONARIO")
    dict_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM SPB_MSGFIELD")
    field_count = cur.fetchone()[0]

    print(f"XSD files processed:  {processed}")
    print(f"XSD files failed:     {failed}")
    print(f"\nDatabase records:")
    print(f"  SPB_MENSAGEM:       {msg_count:5}")
    print(f"  SPB_DICIONARIO:     {dict_count:5}")
    print(f"  SPB_MSGFIELD:       {field_count:5}")
    print("=" * 70)

    cur.close()
    conn.close()

    if processed > 0:
        print("\n✅ Catalog data loaded successfully!")
        return True
    else:
        print("\n❌ No data was loaded")
        return False


def main():
    """Main function."""
    if len(sys.argv) > 1:
        zip_path = sys.argv[1]
    else:
        zip_path = DEFAULT_ZIP_PATH

    zip_path = os.path.abspath(zip_path)

    success = load_catalog_from_xsd(zip_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
