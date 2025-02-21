# scraper/models.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float

Base = declarative_base()

class Agent(Base):
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    rank = Column(String, nullable=False)
    attribute = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    faction = Column(String, nullable=False)
    role = Column(String, nullable=False)
    sd_rating = Column(Float)
    da_rating = Column(Float)
    average_rating = Column(Float)
