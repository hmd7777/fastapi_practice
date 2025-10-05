# backend/app/models.py
from sqlalchemy import Column, Integer, Float, String
from .session import Base

class Iris(Base):
    __tablename__ = "iris"

    id = Column(Integer, primary_key=True, index=True)
    sepal_length = Column(Float)
    sepal_width = Column(Float)
    petal_length = Column(Float)
    petal_width = Column(Float)
    species = Column(String)
