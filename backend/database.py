from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = None

if DATABASE_URL:
    try:
        connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
        test_engine = create_engine(DATABASE_URL, future=True, connect_args=connect_args)
        with test_engine.connect() as conn:
            pass
        engine = test_engine
    except Exception as e:
        print(f"Configured DATABASE_URL failed ({e}). Trying PostgreSQL parameters or SQLite...")

if not engine and DB_USER and DB_PASSWORD and DB_HOST and DB_PORT and DB_NAME:
    try:
        pg_url = URL.create(
            drivername="postgresql+psycopg2",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
        )
        test_engine = create_engine(pg_url, future=True)
        with test_engine.connect() as conn:
            pass
        engine = test_engine
    except Exception as e:
        print(f"PostgreSQL connection failed ({e}). Falling back to SQLite database.")

if not engine:
    sqlite_url = "sqlite:///./food_donation.db"
    engine = create_engine(sqlite_url, future=True, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()