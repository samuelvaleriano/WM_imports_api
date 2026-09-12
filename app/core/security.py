from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _truncate_password(password: str) -> str:
    """Corta a senha em no máximo 72 bytes para evitar exceções do bcrypt."""
    return password.encode('utf-8')[:72].decode('utf-8', errors='ignore')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)