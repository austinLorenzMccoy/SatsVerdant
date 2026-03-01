#!/usr/bin/env python3
"""
Database initialization script for SatsVerdant backend.
This script creates tables, runs migrations, and seeds initial data.
"""

import asyncio
import logging
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, create_tables
from app.core.config import settings
from alembic import command
from alembic.config import Config as AlembicConfig
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migrations():
    """Run Alembic migrations."""
    try:
        # Get the directory containing this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        alembic_ini_path = os.path.join(project_root, "alembic.ini")

        if not os.path.exists(alembic_ini_path):
            logger.warning("alembic.ini not found, creating tables directly")
            create_tables()
            return

        # Run migrations
        alembic_cfg = AlembicConfig(alembic_ini_path)
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        logger.info("Falling back to direct table creation")
        create_tables()


def seed_initial_data():
    """Seed database with initial data."""
    db: Session = SessionLocal()
    try:
        # Check if we already have data
        from app import models
        admin_exists = db.query(models.User).filter(models.User.role == "admin").first()

        if admin_exists:
            logger.info("Initial data already exists, skipping seed")
            return

        # Create default admin user (for development)
        admin_wallet = "STADMIN..."
        admin_user = models.User(
            wallet_address=admin_wallet,
            role="admin",
            display_name="Admin"
        )
        db.add(admin_user)
        db.commit()

        logger.info(f"Created admin user: {admin_wallet}")

        # Create sample validator
        validator_wallet = "STVALIDATOR..."
        validator_user = models.User(
            wallet_address=validator_wallet,
            role="recycler"  # Will be upgraded to validator
        )
        db.add(validator_user)
        db.commit()

        logger.info("Initial data seeded successfully")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()


def create_admin_user():
    """Create admin user if specified in environment."""
    admin_wallet = os.getenv("ADMIN_WALLET_ADDRESS")
    if not admin_wallet:
        return

    db: Session = SessionLocal()
    try:
        from app import models

        # Check if admin already exists
        existing = db.query(models.User).filter(
            models.User.wallet_address == admin_wallet
        ).first()

        if existing:
            if existing.role != "admin":
                existing.role = "admin"
                db.commit()
                logger.info(f"Updated user {admin_wallet} to admin")
            return

        # Create admin user
        admin_user = models.User(
            wallet_address=admin_wallet,
            role="admin",
            display_name="Administrator"
        )
        db.add(admin_user)
        db.commit()

        logger.info(f"Created admin user: {admin_wallet}")

    except Exception as e:
        logger.error(f"Admin user creation failed: {e}")
        db.rollback()
    finally:
        db.close()


async def init_db():
    """Initialize the database."""
    logger.info("Initializing database...")

    # Run migrations
    run_migrations()

    # Seed initial data
    seed_initial_data()

    # Create admin user if specified
    create_admin_user()

    logger.info("Database initialization completed")


if __name__ == "__main__":
    asyncio.run(init_db())
