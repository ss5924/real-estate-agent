import logging
from cryptography.fernet import Fernet, InvalidToken
from src.config import ENCRYPTION_KEY

logger = logging.getLogger(__name__)


class CryptoManager:
    def __init__(self):
        if not ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY가 없습니다.")

        try:
            self.cipher = Fernet(ENCRYPTION_KEY)
        except Exception as e:
            raise ValueError(f"유효하지 않은 암호화 키입니다: {e}")

    def encrypt(self, plain_text: str) -> str:
        if not plain_text:
            return ""
        try:
            encrypted_bytes = self.cipher.encrypt(plain_text.encode("utf-8"))
            return encrypted_bytes.decode("utf-8")
        except Exception as e:
            print(f"암호화 중 오류 발생: {e}")
            return ""

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text:
            return ""
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_text.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except InvalidToken:
            print("복호화 실패: 키가 일치하지 않거나 데이터가 손상되었습니다.")
            return "[데이터 손상됨]"
        except Exception as e:
            print(f"복호화 중 알 수 없는 오류: {e}")
            return "[오류]"
