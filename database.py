import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import psycopg2

load_dotenv()

# Database connection details using PostgreSQL and psycopg2 with SQLAlchemy
DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('ALLOYDB_USER')}:{os.getenv('ALLOYDB_PASSWORD')}"
    f"@{os.getenv('ALLOYDB_LOCALHOST')}:{os.getenv('ALLOYDB_PORT')}/{os.getenv('ALLOYDB_DATABASE')}"
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

# SessionLocal to interact with the database via ORM
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency function to get the SQLAlchemy session for the ORM.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def getconn():
    """
    Return a raw psycopg2 connection for direct database access.
    """
    conn = psycopg2.connect(
        host=os.getenv("ALLOYDB_LOCALHOST"),
        port=os.getenv("ALLOYDB_PORT"),
        dbname=os.getenv("ALLOYDB_DATABASE"),
        user=os.getenv("ALLOYDB_USER"),
        password=os.getenv("ALLOYDB_PASSWORD")
    )
    return conn
