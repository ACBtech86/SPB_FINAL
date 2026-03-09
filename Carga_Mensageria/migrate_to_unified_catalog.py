#!/usr/bin/env python3
"""
Migrate data from Carga_Mensageria database to unified catalog.

This script:
1. Reads data from spb_mensageria database
2. Writes to spb_catalog database
3. Verifies data integrity
"""

import sys
import psycopg

# Source database (Carga_Mensageria - uses uppercase BCSPBSTR)
SOURCE_DB = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': '',
    'dbname': 'BCSPBSTR'
}

# Target database (Unified Catalog)
TARGET_DB = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': '',
    'dbname': 'spb_catalog'
}


def migrate_table(source_conn, target_conn, table_name, column_mapping=None):
    """
    Migrate data from source to target database.

    Args:
        source_conn: Source database connection
        target_conn: Target database connection
        table_name: Name of the table to migrate (lowercase for target)
        column_mapping: Optional dict mapping source columns to target columns
    """
    # Source uses uppercase, target uses lowercase
    source_table = table_name.upper()

    source_cur = source_conn.cursor()
    target_cur = target_conn.cursor()

    try:
        # Get data from source (uppercase table name)
        source_cur.execute(f'SELECT * FROM "{source_table}"')
        rows = source_cur.fetchall()

        if not rows:
            print(f"  [WARN]  No data in source table")
            return 0

        # Get column names
        columns = [desc[0] for desc in source_cur.description]

        # Apply column mapping if provided
        if column_mapping:
            target_columns = [column_mapping.get(col, col) for col in columns]
        else:
            target_columns = columns

        # Clear target table (lowercase)
        target_cur.execute(f'DELETE FROM {table_name}')

        # Insert data into target (lowercase table name)
        placeholders = ', '.join(['%s'] * len(columns))
        col_names = ', '.join([f'"{col}"' for col in target_columns])
        insert_sql = f'INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})'

        count = 0
        for row in rows:
            target_cur.execute(insert_sql, row)
            count += 1

        target_conn.commit()
        print(f"  [OK] Migrated {count} rows")
        return count

    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        target_conn.rollback()
        import traceback
        traceback.print_exc()
        return 0
    finally:
        source_cur.close()
        target_cur.close()


def migrate_spb_msgfield(source_conn, target_conn):
    """
    Special handling for SPB_MSGFIELD (no primary key in source).
    """
    source_cur = source_conn.cursor()
    target_cur = target_conn.cursor()

    try:
        # Get data from source (uppercase)
        source_cur.execute('SELECT * FROM "SPB_MSGFIELD"')
        rows = source_cur.fetchall()

        if not rows:
            print(f"  [WARN]  No data in source table")
            return 0

        columns = [desc[0] for desc in source_cur.description]

        # Clear target table (lowercase)
        target_cur.execute('DELETE FROM spb_msgfield')

        # Insert with explicit columns (excluding 'id' which is auto-generated)
        col_names = ', '.join([f'"{col}"' for col in columns])
        placeholders = ', '.join(['%s'] * len(columns))
        insert_sql = f'INSERT INTO spb_msgfield ({col_names}) VALUES ({placeholders})'

        count = 0
        for row in rows:
            target_cur.execute(insert_sql, row)
            count += 1

        target_conn.commit()
        print(f"  [OK] Migrated {count} rows")
        return count

    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        target_conn.rollback()
        import traceback
        traceback.print_exc()
        return 0
    finally:
        source_cur.close()
        target_cur.close()


def verify_migration(source_conn, target_conn):
    """Verify data was migrated correctly."""
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    # Source tables are uppercase, target are lowercase
    tables = [
        ('SPB_MENSAGEM', 'spb_mensagem'),
        ('SPB_DICIONARIO', 'spb_dicionario'),
        ('SPB_MSGFIELD', 'spb_msgfield'),
        ('SPB_XMLXSL', 'spb_xmlxsl'),
        ('SPB_DOMINIOS', 'spb_dominios'),
        ('SPB_ISPB', 'spb_ispb')
    ]

    source_cur = source_conn.cursor()
    target_cur = target_conn.cursor()

    all_match = True

    for source_table, target_table in tables:
        try:
            source_cur.execute(f'SELECT COUNT(*) FROM "{source_table}"')
            source_count = source_cur.fetchone()[0]

            target_cur.execute(f'SELECT COUNT(*) FROM {target_table}')
            target_count = target_cur.fetchone()[0]

            match = "[OK]" if source_count == target_count else "[ERROR]"
            status = "OK" if source_count == target_count else "MISMATCH"

            print(f"{source_table:<20} Source: {source_count:>6}  Target: {target_count:>6}  {match} {status}")

            if source_count != target_count:
                all_match = False

        except Exception as e:
            print(f"{source_table:<20} [ERROR] Error: {e}")
            all_match = False

    source_cur.close()
    target_cur.close()

    return all_match


def main():
    """Main migration function."""
    print("=" * 70)
    print("MIGRATE TO UNIFIED CATALOG")
    print("=" * 70)
    print(f"Source: {SOURCE_DB['dbname']}")
    print(f"Target: {TARGET_DB['dbname']}")
    print("=" * 70)

    # Get password if not set
    if not SOURCE_DB['password']:
        password = input("Enter PostgreSQL password: ").strip()
        if not password:
            print("[ERROR] Password required")
            sys.exit(1)
        SOURCE_DB['password'] = password
        TARGET_DB['password'] = password

    # Connect to databases
    print("\nConnecting to databases...")
    try:
        source_conn = psycopg.connect(**SOURCE_DB)
        print(f"  [OK] Connected to {SOURCE_DB['dbname']}")

        target_conn = psycopg.connect(**TARGET_DB)
        print(f"  [OK] Connected to {TARGET_DB['dbname']}")
    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}")
        sys.exit(1)

    # Migrate tables (order matters due to foreign keys)
    # Note: Source uses uppercase, target uses lowercase
    total = 0

    # 1. Independent tables first
    print("\n[1/6] Migrating SPB_ISPB...")
    total += migrate_table(source_conn, target_conn, 'spb_ispb')

    print("\n[2/6] Migrating SPB_DOMINIOS...")
    total += migrate_table(source_conn, target_conn, 'spb_dominios')

    print("\n[3/6] Migrating SPB_MENSAGEM...")
    total += migrate_table(source_conn, target_conn, 'spb_mensagem')

    print("\n[4/6] Migrating SPB_DICIONARIO...")
    total += migrate_table(source_conn, target_conn, 'spb_dicionario')

    # 2. Tables with foreign keys
    print("\n[5/6] Migrating SPB_MSGFIELD...")
    total += migrate_spb_msgfield(source_conn, target_conn)

    print("\n[6/6] Migrating SPB_XMLXSL...")
    total += migrate_table(source_conn, target_conn, 'spb_xmlxsl')

    # Verify migration
    all_match = verify_migration(source_conn, target_conn)

    # Close connections
    source_conn.close()
    target_conn.close()

    # Summary
    print("\n" + "=" * 70)
    if all_match:
        print("[OK] MIGRATION COMPLETED SUCCESSFULLY!")
        print(f"   Total rows migrated: {total}")
    else:
        print("[WARN]  MIGRATION COMPLETED WITH WARNINGS")
        print("   Some table counts don't match - review verification above")
    print("=" * 70)

    print("\n[NOTE] Next Steps:")
    print("1. Update Carga_Mensageria config.py:")
    print("   DB_CONFIG['database'] = 'spb_catalog'")
    print("\n2. Update BCSrvSqlMq to connect to spb_catalog")
    print("\n3. Update SPBSite catalog_database_url:")
    print("   postgresql+asyncpg://user:pass@localhost/spb_catalog")
    print("\n4. Test all applications")
    print("=" * 70)


if __name__ == '__main__':
    main()
