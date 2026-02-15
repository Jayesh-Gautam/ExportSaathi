"""
Users API Router
Handles user authentication and profile management

Requirements: 8.1
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timedelta
import logging
import uuid
import re

from passlib.context import CryptContext
from jose import JWTError, jwt

from models.user import UserProfile, UserMetrics
from models.enums import BusinessType, CompanySize
from database.connection import get_db
from database.models import User as DBUser, UserMetrics as DBUserMetrics
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = getattr(settings, 'SECRET_KEY', "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


# Request/Response Models
class RegisterRequest(BaseModel):
    """User registration request."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    business_type: BusinessType = Field(..., description="Type of business")
    company_size: CompanySize = Field(..., description="Size of the company")
    company_name: str = Field(..., min_length=1, max_length=255, description="Company name")
    monthly_volume: Optional[float] = Field(None, gt=0, description="Monthly export volume")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class LoginRequest(BaseModel):
    """User login request."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """User login response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    business_type: str = Field(..., description="Business type")


class ProfileUpdateRequest(BaseModel):
    """Profile update request."""
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    monthly_volume: Optional[float] = Field(None, gt=0)
    business_type: Optional[BusinessType] = None
    company_size: Optional[CompanySize] = None


# Helper Functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> DBUser:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = db.query(DBUser).filter(DBUser.id == uuid.UUID(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


# API Endpoints
@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Creates a new user account with the provided credentials and profile information.
    Returns an access token for immediate authentication.
    
    **Request Body:**
    - email: Valid email address (unique)
    - password: Strong password (min 8 chars, uppercase, lowercase, digit)
    - business_type: Manufacturing, SaaS, or Merchant
    - company_size: Micro, Small, or Medium
    - company_name: Company name
    - monthly_volume: Optional monthly export volume
    
    **Returns:**
    - access_token: JWT token for authentication
    - user_id: Unique user identifier
    - email: User email
    - business_type: User's business type
    """
    logger.info(f"Registration attempt for email: {request.email}")
    
    # Check if user already exists
    existing_user = db.query(DBUser).filter(DBUser.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = hash_password(request.password)
    
    # Create new user
    new_user = DBUser(
        id=uuid.uuid4(),
        email=request.email,
        password_hash=hashed_password,
        business_type=request.business_type.value,
        company_size=request.company_size.value,
        company_name=request.company_name,
        monthly_volume=int(request.monthly_volume) if request.monthly_volume else None,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    
    # Create user metrics record
    user_metrics = DBUserMetrics(
        id=uuid.uuid4(),
        user_id=new_user.id
    )
    db.add(user_metrics)
    
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"User registered successfully: {new_user.id}")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(new_user.id),
        email=new_user.email,
        business_type=new_user.business_type
    )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return an access token.
    
    Validates user credentials and returns a JWT token for subsequent requests.
    
    **Request Body:**
    - email: User email address
    - password: User password
    
    **Returns:**
    - access_token: JWT token for authentication
    - user_id: Unique user identifier
    - email: User email
    - business_type: User's business type
    """
    logger.info(f"Login attempt for email: {request.email}")
    
    # Find user by email
    user = db.query(DBUser).filter(DBUser.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info(f"User logged in successfully: {user.id}")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        email=user.email,
        business_type=user.business_type
    )


@router.get("/profile", response_model=UserProfile)
async def get_profile(
    current_user: DBUser = Depends(get_current_user)
):
    """
    Get the current user's profile.
    
    Returns the authenticated user's profile information.
    Requires valid JWT token in Authorization header.
    
    **Headers:**
    - Authorization: Bearer <access_token>
    
    **Returns:**
    - user_id: Unique user identifier
    - email: User email
    - business_type: Type of business
    - company_size: Size of company
    - company_name: Company name
    - monthly_volume: Monthly export volume
    - created_at: Account creation timestamp
    """
    logger.info(f"Profile retrieval for user: {current_user.id}")
    
    return UserProfile(
        user_id=str(current_user.id),
        email=current_user.email,
        business_type=BusinessType(current_user.business_type),
        company_size=CompanySize(current_user.company_size),
        company_name=current_user.company_name,
        monthly_volume=float(current_user.monthly_volume) if current_user.monthly_volume else None,
        created_at=current_user.created_at
    )


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile.
    
    Updates the authenticated user's profile information.
    Only provided fields will be updated.
    Requires valid JWT token in Authorization header.
    
    **Headers:**
    - Authorization: Bearer <access_token>
    
    **Request Body:**
    - company_name: Optional company name
    - monthly_volume: Optional monthly export volume
    - business_type: Optional business type
    - company_size: Optional company size
    
    **Returns:**
    - Updated user profile
    """
    logger.info(f"Profile update for user: {current_user.id}")
    
    # Update fields if provided
    if request.company_name is not None:
        current_user.company_name = request.company_name
    if request.monthly_volume is not None:
        current_user.monthly_volume = int(request.monthly_volume)
    if request.business_type is not None:
        current_user.business_type = request.business_type.value
    if request.company_size is not None:
        current_user.company_size = request.company_size.value
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"Profile updated successfully for user: {current_user.id}")
    
    return UserProfile(
        user_id=str(current_user.id),
        email=current_user.email,
        business_type=BusinessType(current_user.business_type),
        company_size=CompanySize(current_user.company_size),
        company_name=current_user.company_name,
        monthly_volume=float(current_user.monthly_volume) if current_user.monthly_volume else None,
        created_at=current_user.created_at
    )
