import hmac
import hashlib
import base64
import json
import time
import secrets

SECRET = secrets.token_hex(32)
TOKEN_TTL = 86400  # 24 hours


def create_token() -> str:
    payload = json.dumps({"exp": int(time.time()) + TOKEN_TTL}, separators=(",", ":"))
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
