import sqlite3
import logging
import os
from datetime import datetime
from typing import Optional
from src.config import DB_PATH
from src.crypto_manager import CryptoManager

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(self):
        self.db_path = DB_PATH
        self.crypto = CryptoManager()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        # DB 파일이 저장될 폴더가 없으면 생성
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                # user_id를 PK로 지정하여 유저당 무조건 1개의 Row만 존재하도록 강제
                c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_memory (
                        user_id TEXT PRIMARY KEY,
                        summary TEXT,
                        updated_at TEXT
                    )
                """
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f"DB 초기화 중 에러 발생: {e}")

    def get_user_summary(self, user_id: str) -> Optional[str]:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT summary FROM user_memory WHERE user_id = ?", (user_id,)
                )
                result = c.fetchone()

                if result:
                    return self.crypto.decrypt(result[0])
                return None
        except sqlite3.Error as e:
            print(f"메모리 조회 실패 ({user_id}): {e}")
            return None

    def save_user_summary(self, user_id: str, new_summary: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        encrypted_summary = self.crypto.encrypt(new_summary)

        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute(
                    """
                    INSERT OR REPLACE INTO user_memory (user_id, summary, updated_at)
                    VALUES (?, ?, ?)
                """,
                    (user_id, encrypted_summary, now),
                )
                conn.commit()

            print(f"[Memory] {user_id}의 장기 기억이 업데이트되었습니다.")

        except sqlite3.Error as e:
            print(f"메모리 저장 실패 ({user_id}): {e}")
