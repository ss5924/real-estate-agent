import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
KOREAN_LAW_OC = os.getenv("KOREAN_LAW_OC")
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

DATA_DIRECTORY = "data"
