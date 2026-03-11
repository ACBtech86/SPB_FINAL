#!/usr/bin/env python3
"""
Migration: Add user profiles and message permissions
Creates profiles, profile_message_permissions tables and adds profile_id to users
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.database import engine, async_session


async def create_profiles_table():
    """Create profiles table."""
    print("Creating profiles table...")

    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS profiles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description VARCHAR(500),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

    print("[OK] Profiles table created")


async def create_profile_message_permissions_table():
    """Create profile_message_permissions junction table."""
    print("Creating profile_message_permissions table...")

    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS profile_message_permissions (
                id SERIAL PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                msg_id VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(profile_id, msg_id)
            )
        """))

        # Create indexes for better query performance
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_profile_msg_profile_id
            ON profile_message_permissions(profile_id)
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_profile_msg_msg_id
            ON profile_message_permissions(msg_id)
        """))

    print("[OK] Profile message permissions table created")


async def add_profile_id_to_users():
    """Add profile_id column to users table."""
    print("Adding profile_id column to users table...")

    async with engine.begin() as conn:
        # Check if column already exists
        result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'profile_id'
        """))

        if result.fetchone():
            print("[WARN]  profile_id column already exists in users table")
            return

        # Add profile_id column
        await conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN profile_id INTEGER REFERENCES profiles(id) ON DELETE SET NULL
        """))

        # Create index
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_profile_id ON users(profile_id)
        """))

    print("[OK] profile_id column added to users table")


async def create_default_profiles():
    """Create default profiles with message permissions."""
    print("\nCreating default profiles...")

    async with async_session() as session:
        # Check if profiles already exist
        result = await session.execute(text("SELECT COUNT(*) FROM profiles"))
        count = result.scalar()

        if count > 0:
            print("[WARN]  Profiles already exist")
            return

        # Create 'Administrador' profile (full access to all messages)
        await session.execute(text("""
            INSERT INTO profiles (name, description, is_active)
            VALUES ('Administrador', 'Acesso completo a todos os tipos de mensagens', true)
        """))

        # Get the admin profile ID
        result = await session.execute(
            text("SELECT id FROM profiles WHERE name = 'Administrador'")
        )
        admin_profile_id = result.scalar()

        # Grant admin profile access to all message types
        # This inserts all msg_id from spb_mensagem_view into permissions
        await session.execute(text(f"""
            INSERT INTO profile_message_permissions (profile_id, msg_id)
            SELECT {admin_profile_id}, msg_id FROM spb_mensagem_view
        """))

        # Create 'Operador Básico' profile (limited to common message types)
        await session.execute(text("""
            INSERT INTO profiles (name, description, is_active)
            VALUES ('Operador Básico', 'Acesso a mensagens básicas do SPB', true)
        """))

        # Get the operator profile ID
        result = await session.execute(
            text("SELECT id FROM profiles WHERE name = 'Operador Básico'")
        )
        operator_profile_id = result.scalar()

        # Grant operator profile access to common message types (GEN, STR, LTR, LDL, etc.)
        await session.execute(text(f"""
            INSERT INTO profile_message_permissions (profile_id, msg_id)
            SELECT {operator_profile_id}, msg_id
            FROM spb_mensagem_view
            WHERE msg_id LIKE 'GEN%'
               OR msg_id LIKE 'STR%'
               OR msg_id LIKE 'LTR%'
               OR msg_id LIKE 'LDL%'
        """))

        await session.commit()

        print("[OK] Default profiles created:")
        print("   - Administrador (full access)")
        print("   - Operador Básico (limited access)")


async def update_existing_users():
    """Assign admin profile to existing users."""
    print("\nUpdating existing users...")

    async with async_session() as session:
        # Get admin profile ID
        result = await session.execute(
            text("SELECT id FROM profiles WHERE name = 'Administrador'")
        )
        admin_profile_id = result.scalar()

        if not admin_profile_id:
            print("[WARN]  Admin profile not found, skipping user update")
            return

        # Assign admin profile to all existing users
        await session.execute(text(f"""
            UPDATE users
            SET profile_id = {admin_profile_id}
            WHERE profile_id IS NULL
        """))

        result = await session.execute(
            text("SELECT COUNT(*) FROM users WHERE profile_id IS NOT NULL")
        )
        count = result.scalar()

        await session.commit()

        print(f"[OK] Updated {count} existing user(s) with Administrador profile")


async def verify_migration():
    """Verify the migration completed successfully."""
    print("\nVerifying migration...")

    async with async_session() as session:
        # Check profiles
        result = await session.execute(text("SELECT COUNT(*) FROM profiles"))
        profile_count = result.scalar()

        # Check permissions
        result = await session.execute(
            text("SELECT COUNT(*) FROM profile_message_permissions")
        )
        permission_count = result.scalar()

        # Check users with profiles
        result = await session.execute(
            text("SELECT COUNT(*) FROM users WHERE profile_id IS NOT NULL")
        )
        user_count = result.scalar()

        print(f"[OK] Profiles: {profile_count}")
        print(f"[OK] Message permissions: {permission_count}")
        print(f"[OK] Users with profiles: {user_count}")


async def main():
    """Main migration function."""
    print("=" * 60)
    print("SPBSite - User Profiles Migration")
    print("=" * 60)
    print()

    try:
        await create_profiles_table()
        await create_profile_message_permissions_table()
        await add_profile_id_to_users()
        await create_default_profiles()
        await update_existing_users()
        await verify_migration()

        print()
        print("=" * 60)
        print("[OK] Migration Complete!")
        print("=" * 60)
        print()
        print("Default Profiles Created:")
        print("  1. Administrador - Full access to all message types")
        print("  2. Operador Básico - Limited to common message types")
        print()
        print("All existing users have been assigned the Administrador profile.")
        print("You can now create new users with different profiles.")
        print()

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
