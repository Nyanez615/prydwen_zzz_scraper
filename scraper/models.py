# scraper/models.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float

Base = declarative_base()

class Character(Base):
    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    element = Column(String, nullable=False)
    path = Column(String, nullable=False)
    rarity = Column(String, nullable=False)
    role = Column(String, nullable=False)
    moc_rating = Column(Float)
    pf_rating = Column(Float)
    as_rating = Column(Float)
    average_rating = Column(Float)
