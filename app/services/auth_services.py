from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pwdlib import PasswordHash

from app.config import settings

session_serializer = URLSafeTimedSerializer(settings.secret_key)

hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(input_password: str, hashed_password: str) -> bool:
    return hasher.verify(input_password, hashed_password)


def create_session_token(user_id: int) -> str:
    return session_serializer.dumps(user_id)


def read_session_token(token: str) -> int | None:
    try:
        return session_serializer.loads(token, max_age=7 * 24 * 3600)
    except (BadSignature, SignatureExpired):
        return None
