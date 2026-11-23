import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    """由 SECRET_KEY 派生 Fernet 密钥，用于数据源口令的对称加密。"""
    key = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_text(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_text(cipher: str) -> str:
    """解密失败（如 SECRET_KEY 变更）返回空串，由调用方提示重新配置。"""
    if not cipher:
        return ""
    try:
        return _fernet().decrypt(cipher.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return ""
