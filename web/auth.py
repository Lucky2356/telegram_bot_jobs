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
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return f"pbkdf2_sha256$200000${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algo, iterations, salt, digest = stored_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(candidate, digest)
    except Exception:
        return False


def password_is_valid(password: str) -> bool:
    from core.config import settings
    if settings.WEB_PASSWORD_HASH:
        return verify_password(password, settings.WEB_PASSWORD_HASH)
    return bool(settings.WEB_PASSWORD) and hmac.compare_digest(password, settings.WEB_PASSWORD)


def create_token(token_version: int = 0) -> str:
    from core.config import settings
    password_source = settings.WEB_PASSWORD_HASH or settings.WEB_PASSWORD or "nopass"
    password_hash = hashlib.sha256(password_source.encode()).hexdigest()
    payload = json.dumps(
        {"exp": int(time.time()) + settings.WEB_SESSION_TTL_SECONDS, "sub": password_hash, "ver": token_version},
        separators=(",", ":"),
    )
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode()
    sig = hmac.new(SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_token(token: str, token_version: int = 0) -> bool:
    try:
        payload_b64, sig = token.split(".")
        expected = hmac.new(SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
        return payload.get("exp", 0) > time.time() and payload.get("ver", 0) == token_version
    except Exception:
        return False
