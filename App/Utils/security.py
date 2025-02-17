import secrets
from fastapi import HTTPException, status
# from Models.models import User
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from typing import Any, Dict, Optional
import logging
from .config import DevelopmentConfig


settings = DevelopmentConfig()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



class Security():
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    # @staticmethod
    # def get_user(organization_id: Any,  db: Session):
    #     try:
    #         user = db.query(User).filter(User.organization_id==organization_id).first()
    #         if not user:
    #             return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not Found")
    #     except Exception as e:
    #         logging.DEBUG(f"Error getting user data: {str(e)}")
    #         raise e
    

    # Secure Token Generation
    def generate_random_string(length=12):
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
        return "".join(secrets.choice(characters) for _ in range(length))
    
    def generate_random_char(length=12):
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return "".join(secrets.choice(characters) for _ in range(length))

    @staticmethod 
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
        
    @staticmethod 
    def get_password_hash(password='password'):
        return pwd_context.hash(password)
    

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def generate_token(data: Dict, expires_in: int = 3600) -> str:
        """
        Generates a JWT token for authentication.
        
        :param data: Dictionary containing user information (e.g., user_id, role)
        :param expires_in: Token expiration time in seconds (default: 1 hour)
        :return: Encoded JWT token as a string
        """
        to_encode = data.copy()
        expiration = datetime.utcnow() + timedelta(seconds=expires_in)
        to_encode.update({"exp": expiration})
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        return token
    

    # Generate reset password token function
    @staticmethod
    def generate_reset_password_token(expires: int = None):
        if expires is not None:
            expires = datetime.now(timezone.utc) + expires
        else:
            expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"exp": expires}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)
        return encoded_jwt
    

    @staticmethod
    def decode_token(token_str: str):
        try:
        
            payload = jwt.decode(token=token_str, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            print("\n\njwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]):\n", jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]))
            print("decode payload: ", payload)
            return payload
        except JWTError as e:
            print("\n\nerror: ",e)
            return None
