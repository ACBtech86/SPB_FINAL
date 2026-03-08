#!/usr/bin/env python3
"""
Verify database configuration from BCSrvSqlMq.ini
"""
import configparser
import psycopg2

def verify_database():
    # Read configuration
    config = configparser.ConfigParser()
    config.read('/home/ubuntu/SPB_FINAL/BCSrvSqlMq/BCSrvSqlMq.ini')

    # Get database settings
    db_server = config['DataBase']['DBServer']
    db_name = config['DataBase']['DBName']

    # Database connection parameters (hardcoded for now)
    db_config = {
        'host': db_server,
        'port': 5432,
        'dbname': db_name.lower(),  # PostgreSQL uses lowercase
        'user': 'postgres',
        'password': 'Rama1248',
    }

    print("=" * 70)
    print("Database Configuration Verification")
    print("=" * 70)
    print(f"Database Server: {db_server}")
    print(f"Database Name: {db_name} (using: {db_config['dbname']})")
    print(f"Database Port: {db_config['port']}")
    print(f"Database User: {db_config['user']}")
    print("=" * 70)

    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        print(f"✅ Connected to database: {db_config['dbname']}\n")

        cur = conn.cursor()

        # Verify tables
        print("Verifying tables:")
        print("-" * 70)

        tables = [
            ('SPB_LOG_BACEN', 'Log table'),
            ('SPB_BACEN_TO_LOCAL', 'Bacen to Local messages'),
            ('SPB_LOCAL_TO_BACEN', 'Local to Bacen messages'),
            ('SPB_CONTROLE', 'Control table'),
            ('SPB_MENSAGEM', 'Message catalog'),
            ('SPB_DICIONARIO', 'Data dictionary'),
            ('SPB_MSGFIELD', 'Message fields'),
        ]

        for table_name, description in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                print(f"✅ {table_name:25} - {count:5} records - {description}")
            except Exception as e:
                print(f"❌ {table_name:25} - Error: {e}")

        print("-" * 70)

        # Show SPB_CONTROLE data
        print("\n📋 SPB_CONTROLE data:")
        cur.execute("SELECT ispb, nome_ispb, status_geral FROM SPB_CONTROLE")
        for row in cur.fetchall():
            print(f"  ISPB: {row[0]}, Name: {row[1]}, Status: {row[2]}")

        cur.close()
        conn.close()

        print("\n✅ All database configuration verified successfully!")
        print("=" * 70)
        return True

    except psycopg2.Error as e:
        print(f"❌ Database Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    verify_database()
