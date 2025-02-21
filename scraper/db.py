# scraper/db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scraper.models import Base

DB_URL = os.environ.get("DB_URL", "sqlite:///hsr.db")
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)