from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = "sua_chave_secreta_super_segura_wm_imports"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _truncate_password(password: str) -> str:
    return password.encode('utf-8')[:72].decode('utf-8', errors='ignore')

def hash_password(password: str) -> str:
    safe_pwd = _truncate_password(password)
    return pwd_context.hash(safe_pwd)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    safe_pwd = _truncate_password(plain_password)
    return pwd_context.verify(safe_pwd, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt