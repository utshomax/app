from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from functools import lru_cache
from typing import Generator
import os
import logging
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('jobby.db')

# Load environment variables
load_dotenv()

# MySQL Database configuration
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME', 'jobby')

# PostgreSQL Database configuration
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', '')
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DB = os.getenv('PG_DATABASE', 'jobby_resume')

# SQLAlchemy setup for MySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy setup for PostgreSQL
PG_DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# MySQL engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# PostgreSQL engine and session
pg_engine = create_engine(PG_DATABASE_URL)
PGSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)

# Create base classes for models
Base = declarative_base()
Base.metadata.bind = engine

PGBase = declarative_base()
PGBase.metadata.bind = pg_engine

# Import models after engine and base setup to avoid circular imports
from models.sql import User, CandidateResume

def sync_schema_changes():
    """Synchronize schema changes with the database"""
    try:
        # Drop and recreate tables for schema changes
        PGBase.metadata.drop_all(bind=pg_engine)
        PGBase.metadata.create_all(bind=pg_engine)
        logger.info("PostgreSQL schema synchronized successfully")
    except Exception as e:
        logger.error(f"Error synchronizing PostgreSQL schema: {str(e)}")
        raise

def create_all_tables():
    """Create all database tables"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        PGBase.metadata.create_all(bind=pg_engine)
        logger.info("All database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

# Create tables on module import
#create_all_tables()
# Synchronize schema changes
#sync_schema_changes()

# Remove @lru_cache() decorator as it's causing issues with async context
def get_db() -> Generator[Session, None, None]:
    """Dependency for getting MySQL database session"""
    db = SessionLocal()
    logger.info('MySQL Database session created')
    try:
        yield db
    finally:
        db.close()
        logger.info('MySQL Database session closed')

# Remove @lru_cache() decorator as it's causing issues with async context
def get_pg_db() -> Generator[Session, None, None]:
    """Dependency for getting PostgreSQL database session"""
    db = PGSessionLocal()
    logger.info('PostgreSQL Database session created')
    try:
        yield db
    finally:
        db.close()        
        logger.info('PostgreSQL Database session closed')

# Set up SQLAlchemy event listeners for MySQL
@event.listens_for(engine, 'connect')
def receive_connect(dbapi_connection, connection_record):
    logger.info('MySQL Database connection established')

@event.listens_for(engine, 'engine_disposed')
def receive_engine_disposed(engine):
    logger.info('MySQL Database connection disposed')

@event.listens_for(engine, 'checkout')
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.info('MySQL Database connection checked out from pool')

@event.listens_for(engine, 'checkin')
def receive_checkin(dbapi_connection, connection_record):
    logger.info('MySQL Database connection returned to pool')

@event.listens_for(engine, 'reset')
def receive_reset(dbapi_connection, connection_record):
    logger.info('MySQL Database connection reset')

@event.listens_for(SessionLocal, 'after_begin')
def receive_after_begin(session, transaction, connection):
    logger.info('MySQL Database transaction began')

@event.listens_for(SessionLocal, 'after_commit')
def receive_after_commit(session):
    logger.info('MySQL Database transaction committed')

@event.listens_for(SessionLocal, 'after_rollback')
def receive_after_rollback(session):
    logger.info('MySQL Database transaction rolled back')

# Set up SQLAlchemy event listeners for PostgreSQL
@event.listens_for(pg_engine, 'connect')
def receive_pg_connect(dbapi_connection, connection_record):
    logger.info('PostgreSQL Database connection established')

@event.listens_for(pg_engine, 'engine_disposed')
def receive_pg_engine_disposed(engine):
    logger.info('PostgreSQL Database engine disposed')

@event.listens_for(PGSessionLocal, 'after_begin')
def receive_pg_after_begin(session, transaction, connection):
    logger.info('PostgreSQL Database transaction began')

@event.listens_for(PGSessionLocal, 'after_commit')
def receive_pg_after_commit(session):
    logger.info('PostgreSQL Database transaction committed')

@event.listens_for(PGSessionLocal, 'after_rollback')
def receive_pg_after_rollback(session):
    logger.info('PostgreSQL Database transaction rolled back')
