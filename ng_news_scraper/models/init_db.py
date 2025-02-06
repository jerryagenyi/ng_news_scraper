# models/init_db.py
import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine

# Now we can import our local modules
from models.models import Base
from config.settings import SCRAPER_SETTINGS

def init_database():
    engine = create_engine(SCRAPER_SETTINGS['DATABASE_URL'])
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()