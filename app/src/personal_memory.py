import sqlite3
import os
from datetime import datetime

class MemoryManager:
    def __init__(self, db_path="users.db"):
        # app.py와 같은 폴더에 DB 파일 생성
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, db_path)
        self.init_db()

    def init_db(self):
        """DB 테이블이 없으면 생성"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # user_id: 사용자 아이디
        # summary: 사용자에 대한 요약 정보 (LLM이 만든 것)
        # updated_at: 마지막 업데이트 시간
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_memory (
                user_id TEXT PRIMARY KEY,
                summary TEXT,
                updated_at TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def get_user_summary(self, user_id):
        """사용자의 요약된 정보를 가져옴"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT summary FROM user_memory WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None

    def save_user_summary(self, user_id, new_summary):
        """요약된 정보를 저장/업데이트"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 있으면 업데이트, 없으면 삽입 (UPSERT)
        c.execute('''
            INSERT OR REPLACE INTO user_memory (user_id, summary, updated_at)
            VALUES (?, ?, ?)
        ''', (user_id, new_summary, now))
        
        conn.commit()
        conn.close()
        print(f"💾 [Memory] {user_id}의 정보가 저장되었습니다.")