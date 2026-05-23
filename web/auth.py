import hmac
import hashlib
import base64
import json
import time
import secrets

import os

_SECRET_FILE = ".jwt_secret"

def _load_secret() -> str:
    if env := os.environ.get("JWT_SECRET"):
        return env
    try:
        with open(_SECRET_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        secret = secrets.token_hex(32)
        try:
            fd = os.open(_SECRET_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(secret)
        except (OSError, FileExistsError):
            try:
                with open(_SECRET_FILE) as f:
                    return f.read().strip()
            except FileNotFoundError:
                pass
        return secret

SECRET = _load_secret()
TOKEN_TTL = 86400  # 24 hours


def create_token() -> str:
    from core.config import settings
    password_hash = hashlib.sha256(settings.WEB_PASSWORD.encode()).hexdigest() if settings.WEB_PASSWORD else "nopass"
    payload = json.dumps({"exp": int(time.time()) + TOKEN_TTL, "sub": password_hash}, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode()
    sig = hmac.new(SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_token(token: str) -> bool:
    try:
        payload_b64, sig = token.split(".")
        expected = hmac.new(SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
        return payload.get("exp", 0) > time.time()
    except Exception:
        return False
