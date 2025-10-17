from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from config.settings import SUPABASE_DB_URL

def init_database():
    try:
        engine = create_engine(SUPABASE_DB_URL)
        db = SQLDatabase(engine=engine, include_tables=['product_details'])
        return db
    except Exception as e:
        raise RuntimeError(f"Database connection failed: {e}")
