from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError
from src.database import get_db, engine
from src.models import Base, User
from src.schemas import UserCreate, UserResponse, Token
from src.auth import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token, get_current_user
from src.auth import router as auth_router
from src.routers.contacts import router as contacts_router
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from src.limiter import limiter
from slowapi import Limiter
from slowapi.util import get_remote_address

app = FastAPI(title="Контактна книга API")

app.state.limiter = limiter

app.include_router(auth_router)
app.include_router(contacts_router)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    """

    :param request:
    :param exc:
    :return:
    """
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests, slow down!"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """

    :return:
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    """

    :return:
    """
    return {"message": "API працює!"}

@app.post("/auth/signup", response_model=UserResponse, status_code=201)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """

    :param user_data:
    :param db:
    :return:
    """
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """

    :param form_data:
    :param db:
    :return:
    """
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token}

@app.post("/auth/refresh_token", response_model=Token)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """

    :param credentials:
    :return:
    """
    try:
        payload = decode_token(credentials.credentials, refresh=True)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(data={"sub": str(user_id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user_id)})
    return {"access_token": new_access_token, "refresh_token": new_refresh_token}


@app.get("/auth/verify_email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """

    :param token:
    :param db:
    :return:
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    await db.commit()
    return {"message": "Email successfully verified"}

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    """
    
    :param request:
    :param exc:
    :return:
    """
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests, slow down!"}
    )


@app.get("/auth/verify_email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """

    :param token:
    :param db:
    :return:
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    await db.commit()
    return {"message": "Email successfully verified"}


app.include_router(contacts_router)


