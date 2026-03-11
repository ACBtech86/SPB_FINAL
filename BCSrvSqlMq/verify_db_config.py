#!/usr/bin/env python3
"""
Verify database configuration from BCSrvSqlMq.ini
Checks that BanuxSPB has both operational and catalog tables.
"""
import configparser
import os
import psycopg2


def verify_database():
    # Read configuration
    config = configparser.ConfigParser()
    ini_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'BCSrvSqlMq.ini')
    config.read(ini_path)

    # Get database settings
    db_server = config.get('DataBase', 'DBServer', fallback='localhost')
    db_name = config.get('DataBase', 'DBName', fallback='BanuxSPB')
    db_port = config.getint('DataBase', 'DBPort', fallback=5432)
    db_user = config.get('DataBase', 'DBUserName', fallback='postgres')
    db_password = config.get('DataBase', 'DBPassword', fallback='Rama1248')

    print("=" * 70)
    print("Database Configuration Verification")
    print("=" * 70)
    print(f"Server:     {db_server}:{db_port}")
    print(f"User:       {db_user}")
    print(f"Database:   {db_name}")
    print("=" * 70)

    success = True

    try:
        conn = psycopg2.connect(
            host=db_server, port=db_port,
            dbname=db_name, user=db_user, password=db_password,
        )
        print(f"\nConnected to: {db_name}\n")
        cur = conn.cursor()

        # Operational tables
        print("--- Operational Tables ---")
        operational_tables = [
            ('SPB_LOG_BACEN', 'Log table'),
            ('SPB_BACEN_TO_LOCAL', 'Bacen to Local messages'),
            ('SPB_LOCAL_TO_BACEN', 'Local to Bacen messages'),
            ('SPB_CONTROLE', 'Control table'),
        ]

        for table_name, description in operational_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                print(f"  {table_name:25} - {count:5} records - {description}")
            except Exception as e:
                print(f"  {table_name:25} - Error: {e}")
                conn.rollback()

        # Catalog tables (quoted uppercase)
        print("\n--- Catalog Tables ---")
        catalog_tables = [
            ('SPB_MENSAGEM', 'Message catalog'),
            ('SPB_DICIONARIO', 'Data dictionary'),
            ('SPB_MSGFIELD', 'Message fields'),
        ]

        for table_name, description in catalog_tables:
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                count = cur.fetchone()[0]
                print(f"  {table_name:25} - {count:5} records - {description}")
            except Exception as e:
                print(f"  {table_name:25} - Error: {e}")
                conn.rollback()

        # Show SPB_CONTROLE data
        try:
            cur.execute("SELECT ispb, nome_ispb, status_geral FROM SPB_CONTROLE")
            rows = cur.fetchall()
            if rows:
                print(f"\n  SPB_CONTROLE data:")
                for row in rows:
                    print(f"    ISPB: {row[0]}, Name: {row[1]}, Status: {row[2]}")
        except Exception:
            conn.rollback()

        cur.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"  Connection failed: {e}")
        success = False

    # Final result
    print("\n" + "=" * 70)
    if success:
        print("All database configuration verified successfully!")
    else:
        print("Some checks failed - review output above.")
    print("=" * 70)
    return success


if __name__ == '__main__':
    verify_database()
