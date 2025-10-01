from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

class Match(Base):
    __tablename__ = "matches"

    id         = Column(Integer, primary_key=True, index=True)
    date       = Column(String(10), nullable=False)   # 'YYYY-MM-DD'
    home_team  = Column(String,    nullable=False, index=True)
    away_team  = Column(String,    nullable=False, index=True)
    home_score = Column(Integer,   nullable=False)
    away_score = Column(Integer,   nullable=False)
    tournament = Column(String,    nullable=False, index=True)
    city       = Column(String)
    country    = Column(String, index=True)
    neutral    = Column(Boolean,   nullable=False)    # stored as 0/1 in SQLite
