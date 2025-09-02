from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, UploadFile, File, APIRouter
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models import User
from src.schemas import UserCreate, UserOut, Token
import os
import smtplib
from email.mime.text import MIMEText
import cloudinary
import cloudinary.uploader

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "mysecret")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "refreshsecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


def get_password_hash(password: str) -> str:
    """
    :param password:
    :return:
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """

    :param plain_password:
    :param hashed_password:
    :return:
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """

    :param data:
    :param expires_delta:
    :return:
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """

    :param data:
    :param expires_delta:
    :return:
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str, refresh: bool = False) -> dict:
    """

    :param token:
    :param refresh:
    :return:
    """
    key = REFRESH_SECRET_KEY if refresh else SECRET_KEY
    try:
        return jwt.decode(token, key, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """

    :param token:
    :param db:
    :return:
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, int(user_id))
    if user is None:
        raise credentials_exception
    return user

def create_email_verification_token(user_id: int) -> str:
    """

    :param user_id:
    :return:
    """
    to_encode = {"sub": str(user_id)}
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def send_verification_email(email: str, token: str):
    """

    :param email:
    :param token:
    :return:
    """
    verify_link = f"http://localhost:8000/auth/verify/{token}"
    msg = MIMEText(f"Please verify your email: {verify_link}")
    msg["Subject"] = "Verify your email"
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = email

    with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        server.send_message(msg)


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """

    :param user:
    :param db:
    :return:
    """
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_email_verification_token(new_user.id)
    send_verification_email(new_user.email, token)

    return new_user

@router.get("/verify/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """

    :param token:
    :param db:
    :return:
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_verified = True
        await db.commit()
        return {"msg": "Email verified successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Verification token expired")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

@router.post("/login", response_model=Token)
async def login(form_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """

    :param form_data:
    :param db:
    :return:
    """
    result = await db.execute(select(User).where(User.email == form_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/avatar")
async def update_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """

    :param file:
    :param db:
    :param current_user:
    :return:
    """
    result = cloudinary.uploader.upload(file.file, folder="avatars")
    url = result["secure_url"]
    current_user.avatar = url
    await db.commit()
    return {"avatar_url": url}
