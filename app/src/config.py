import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
KOREAN_LAW_OC = os.getenv("KOREAN_LAW_OC")
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")


# app/src/config.py -> app/src -> app -> agent (ROOT)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "users.db")
SESSION_DIR = os.path.join(DATA_DIR, "sessions")
ENV_PATH = os.path.join(BASE_DIR, ".env")
APP_DIR = os.path.join(BASE_DIR, "app")
RAG_DATA_DIR = os.path.join(DATA_DIR, "rag")
