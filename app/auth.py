from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlmodel import Session, select
from fastapi import Request, HTTPException, status
from app.models import User
from app.config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(session: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def create_user(session: Session, username: str, email: str, password: str) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_current_user_from_session(request: Request, session: Session) -> Optional[User]:
    """Get current user from session cookie"""
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user = session.get(User, user_id)
    return user


def require_auth(request: Request, session: Session) -> User:
    """Require authentication, raise exception if not authenticated"""
    user = get_current_user_from_session(request, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user
