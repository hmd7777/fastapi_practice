from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite file relative to the folder you run uvicorn from (backend/)
DATABASE_URL = "sqlite:///./data/football.db"

# check_same_thread=False is needed for SQLite with FastAPI's threaded workers
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# FastAPI dependency: opens a session per request then closes it.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
