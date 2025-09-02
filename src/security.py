from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models import User

SECRET_KEY = "melnyk2006"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """

    :param plain_password:
    :param hashed_password:
    :return:
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """

    :param password:
    :return:
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """

    :param data:
    :param expires_delta:
    :return:
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    """

    :param data:
    :return:
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    """

    :param token:
    :return:
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db)
):
    """

    :param credentials:
    :param db:
    :return:
    """
    try:
        payload = decode_token(credentials.credentials)
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user

