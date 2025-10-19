from sqlalchemy import create_engine, Table, Column, Integer, Text, MetaData, select, desc
from langchain_community.utilities import SQLDatabase
from config.settings import SUPABASE_DB_URL

# ---------------- SQLDatabase for LangChain ----------------
def init_database():
    try:
        engine = create_engine(SUPABASE_DB_URL) #creates a connection to your database (like a bridge).
        db = SQLDatabase(engine=engine, include_tables=['product_details']) #wraps the SQLAlchemy engine in a LangChain-friendly format, so LangChain tools can query the product_details
        return db
    except Exception as e:
        raise RuntimeError(f"Database connection failed: {e}")

# ---------------- Chat History Table ----------------
engine = create_engine(SUPABASE_DB_URL)
metadata = MetaData() #a container that holds information about your tables.

chat_history_table = Table(
    "chat_history", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_message", Text, nullable=False),
    Column("ai_response", Text, nullable=False)
)
metadata.create_all(engine)  # auto-create table if not exists

# ---------------- Helper Functions ----------------
def store_chat(user_message: str, ai_response: str):
    with engine.connect() as conn:
        conn.execute(chat_history_table.insert().values(
            user_message=user_message,
            ai_response=ai_response
        ))
        conn.commit()  # <--- ADD THIS LINE TO COMMIT THE TRANSACTION

def fetch_last_5_chats():
    with engine.connect() as conn:
        query = select(chat_history_table).order_by(desc(chat_history_table.c.id)).limit(5)
        results = conn.execute(query).fetchall()
        # Return in chronological order (oldest first)
        return [{"user_message": row.user_message, "ai_response": row.ai_response} for row in reversed(results)]



'''Python Code (SQLAlchemy)
       ↓
metadata = MetaData()   ← notebook to hold table blueprints
       ↓
chat_history_table = Table(...)   ← define table "chat_history"
       ↓
metadata.create_all(engine)   ← create table in Supabase/Postgres
'''
