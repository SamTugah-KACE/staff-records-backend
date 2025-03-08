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
# Offload blocking operations to a threadpool in an async context.
from starlette.concurrency import run_in_threadpool

settings = DevelopmentConfig()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Try to use cachetools for TTL caching; if unavailable, fall back to a plain dict.
try:
    from cachetools import TTLCache
except ImportError:
    TTLCache = None



class Security:
    def __init__(self, secret_key: str, algorithm: str, token_expire_minutes: int = 60): #, length:int=8#):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes
        # self.length =length
        # Setup a TTL cache for decoded tokens if possible
        if TTLCache:
            self.token_cache = TTLCache(maxsize=1024, ttl=token_expire_minutes * 60)
        else:
            self.token_cache = {}



    # @staticmethod
    # def hash_password(password: str) -> str:
    #     return pwd_context.hash(password)

    def hash_password(self, password: str) -> str:
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
    def generate_random_string(length:int):
        
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
        return "".join(secrets.choice(characters) for _ in range(length))
    
    def generate_random_char(length:int):
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return "".join(secrets.choice(characters) for _ in range(length))

    # @staticmethod 
    # def verify_password(plain_password, hashed_password):
    #     return pwd_context.verify(plain_password, hashed_password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
        
    # @staticmethod 
    # def get_password_hash(password='password'):
    #     return pwd_context.hash(password)

    def get_password_hash(self, password: str = 'password') -> str:
        return pwd_context.hash(password)
    

    # @staticmethod
    # def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    #     to_encode = data.copy()
    #     if expires_delta:
    #         expire = datetime.now(timezone.utc) + expires_delta
    #     else:
    #         expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    #     to_encode.update({"exp": expire})
    #     encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    #     return encoded_jwt

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    # @staticmethod
    # def generate_token(data: Dict, expires_in: int = 3600) -> str:
    #     """
    #     Generates a JWT token for authentication.
        
    #     :param data: Dictionary containing user information (e.g., user_id, role)
    #     :param expires_in: Token expiration time in seconds (default: 1 hour)
    #     :return: Encoded JWT token as a string
    #     """
    #     to_encode = data.copy()
    #     expiration = datetime.utcnow() + timedelta(seconds=expires_in)
    #     to_encode.update({"exp": expiration})
    #     token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
    #     return token

    def generate_token(self, data: Dict[str, Any], expires_in: int = 3600) -> str:
        """
        Generates a JWT token that includes tenant-specific data (e.g., organization_id).
        """
        to_encode = data.copy()
        expiration = datetime.utcnow() + timedelta(seconds=expires_in)
        to_encode.update({"exp": expiration})
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return token
    

    # Generate reset password token function
    # @staticmethod
    # def generate_reset_password_token(expires: int = None):
    #     if expires is not None:
    #         expires = datetime.now(timezone.utc) + expires
    #     else:
    #         expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    #     to_encode = {"exp": expires}
    #     encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)
    #     return encoded_jwt

    def generate_reset_password_token(self, expires: Optional[timedelta] = None) -> str:
        if expires is not None:
            expire = datetime.now(timezone.utc) + expires
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.token_expire_minutes)
        to_encode = {"exp": expire}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    

    # @staticmethod
    # def decode_token(token_str: str):
    #     try:
        
    #         payload = jwt.decode(token=token_str, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    #         print("\n\njwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]):\n", jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]))
    #         print("decode payload: ", payload)
    #         return payload
    #     except JWTError as e:
    #         print("\n\nerror: ",e)
    #         return None

    async def decode_token(self, token_str: str) -> Optional[Dict[str, Any]]:
        """
        Asynchronously decodes a JWT token using a threadpool to offload the synchronous operation.
        Uses caching to speed up repeated decodes.
        """
        if token_str in self.token_cache:
            logger.debug("Returning cached token payload")
            return self.token_cache[token_str]

        try:
            payload = await run_in_threadpool(
                jwt.decode, token_str, self.secret_key, algorithms=[self.algorithm]
            )
            logger.debug(f"Decoded token payload: {payload}")
            self.token_cache[token_str] = payload
            return payload
        except JWTError as e:
            logger.error(f"JWT decoding error: {e}")
            return None
