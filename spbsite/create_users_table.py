#!/usr/bin/env python3
"""
Create users table and add default admin user for SPBSite
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from passlib.context import CryptContext

from app.database import engine, async_session
from spb_shared.models.auth import User
from spb_shared.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_users_table():
    """Create the users table if it doesn't exist."""
    print("Creating users table...")

    async with engine.begin() as conn:
        # Create users table
        await conn.run_sync(Base.metadata.create_all)

    print("[OK] Users table created")


async def create_default_user():
    """Create default admin user if it doesn't exist."""
    print("\nCreating default admin user...")

    async with async_session() as session:
        # Check if admin user already exists
        result = await session.execute(
            text("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        )
        count = result.scalar()

        if count > 0:
            print("[WARN]  Admin user already exists")
            return

        # Create admin user with password "admin"
        # Note: Change this password in production!
        password_hash = pwd_context.hash("admin")

        await session.execute(
            text("""
                INSERT INTO users (username, password_hash, is_active, created_at)
                VALUES (:username, :password_hash, :is_active, NOW())
            """),
            {
                "username": "admin",
                "password_hash": password_hash,
                "is_active": True
            }
        )

        await session.commit()

        print("[OK] Default admin user created")
        print("   Username: admin")
        print("   Password: admin")
        print("   [WARN]  IMPORTANT: Change this password in production!")


async def verify_setup():
    """Verify the setup is correct."""
    print("\nVerifying setup...")

    async with async_session() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()

        print(f"[OK] Users table exists with {count} user(s)")


async def main():
    """Main function."""
    print("=" * 60)
    print("SPBSite - Users Table Setup")
    print("=" * 60)
    print()

    try:
        await create_users_table()
        await create_default_user()
        await verify_setup()

        print()
        print("=" * 60)
        print("[OK] Setup Complete!")
        print("=" * 60)
        print()
        print("You can now log in to SPBSite:")
        print("  Username: admin")
        print("  Password: admin")
        print()
        print("[WARN]  Remember to change the password after first login!")
        print()

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
