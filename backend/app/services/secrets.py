"""API 키 등 민감 정보의 암호화 저장.

- 디스크: storage/secrets.bin 에 Fernet(AES-128-CBC + HMAC) 토큰으로 저장.
- 키 도출: PBKDF2-SHA256(머신 지문, salt, 200k iter) → 32 bytes → base64.
  머신 지문은 호스트명 + 사용자명 + 설치경로 조합이라 다른 PC/계정으로
  파일만 복사해도 복호화되지 않는다.
- 프로그램 내: 메모리에 상수로 보관하지 않고, 사용 시점에만 복호화해서
  로컬 변수로 전달한다.
"""
from __future__ import annotations

import base64
import hashlib
import os
import platform
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from ..config import settings

_SECRETS_FILE = "secrets.bin"
_APP_SALT = b"PetMe-Moji::v1::do-not-change-this-salt"
_PBKDF2_ITER = 200_000


def _machine_fingerprint() -> bytes:
    install_root = Path(__file__).resolve().parents[2]  # backend/
    parts = [
        platform.node(),
        os.environ.get("USERNAME") or os.environ.get("USER") or "",
        os.environ.get("COMPUTERNAME", ""),
        str(install_root),
    ]
    return "|".join(parts).encode("utf-8")


def _fernet() -> Fernet:
    raw = hashlib.pbkdf2_hmac("sha256", _machine_fingerprint(), _APP_SALT, _PBKDF2_ITER, dklen=32)
    return Fernet(base64.urlsafe_b64encode(raw))


def _path() -> Path:
    return settings.storage_path / _SECRETS_FILE


def _sanitize_key(value: str) -> str:
    """붙여넣기 사고 방어: 공백·줄바꿈·non-ASCII 문자 모두 제거."""
    if not value:
        return ""
    # ASCII만, 공백류(스페이스/탭/줄바꿈/NBSP/제로폭 등) 전부 제외
    return "".join(c for c in value if c.isascii() and not c.isspace())


def save_api_key(value: str) -> None:
    value = _sanitize_key(value)
    if not value:
        raise ValueError("빈 키는 저장할 수 없습니다.")
    token = _fernet().encrypt(value.encode("utf-8"))
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(token)
    try:
        os.chmod(p, 0o600)  # POSIX 한정. Windows에선 무시됨.
    except OSError:
        pass


def delete_api_key() -> bool:
    p = _path()
    if p.exists():
        p.unlink()
        return True
    return False


def load_api_key() -> str | None:
    """디스크에서 복호화. 없거나 변조됐으면 None.

    호출자는 받은 값을 로컬 변수로만 쓰고 즉시 폐기해야 한다.
    """
    p = _path()
    if not p.exists():
        return None
    try:
        return _fernet().decrypt(p.read_bytes()).decode("utf-8")
    except InvalidToken:
        return None


def mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def is_configured() -> bool:
    return load_api_key() is not None


def get_api_key_required() -> str:
    """우선순위: 암호화 저장 → .env 폴백. 없으면 RuntimeError."""
    key = load_api_key()
    if key:
        return key
    env_key = settings.gemini_api_key
    if env_key and not env_key.startswith("your_"):
        return env_key
    raise RuntimeError(
        "Gemini API 키가 설정되지 않았습니다. UI 우측 상단 설정(⚙)에서 키를 등록하세요."
    )
