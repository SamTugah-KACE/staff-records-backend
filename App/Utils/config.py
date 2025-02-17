import os
from pydantic import  Field, EmailStr
from typing import Dict, Optional
from pydantic_settings import BaseSettings
import secrets


class BaseConfig(BaseSettings):
    """
    Base configuration for the application.
    """
    APP_NAME: str = Field("User Management System", description="The name of the application.")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT", description="Application environment (development, production, testing).")
    DEBUG: bool = Field(False, description="Debug mode for the application.")
    SECRET_KEY: str = Field(secrets.token_urlsafe(32), env="SECRET_KEY", description="Secret key for application security.")
    ALGORITHM: str = "HS256"
    COOKIE_REFRESH_EXPIRE = 290500

    # Database Configurations
    DATABASE_URL: str = Field("postgresql://postgres:password@localhost/records_db", env="DATABASE_URL", description="Database connection string.")

    #Token Configuration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 2700
    REFRESH_TOKEN_DURATION_IN_MINUTES: int =  2592000
    REMEMBER_ME_REFRESH_TOKEN_IN_MINUTES: int = 5184000
    REFRESH_TOKEN_REMEMBER_ME_DAYS: int = 60
    COOKIE_ACCESS_EXPIRE: int = 1800
    COOKIE_REFRESH_EXPIRE: int = 2592000 # 1 Month


    #External api
    FACIAL_AUTH_API_URL:str = 'https://facial-authentication-system.onrender.com/'
    FACIAL_AUTH_API_TIMEOUT:int = 120  # 120 seconds


    # Email Configurations
    SMTP_SENDER_EMAIL: EmailStr = Field("dev.aiti.com.gh@gmail.com", env="SMTP_SENDER_EMAIL", description="Sender email address for SMTP.")
    SMTP_SENDER_PASSWORD: str = Field("", env="SMTP_SENDER_PASSWORD", description="Password for the SMTP sender email.")
    SMTP_HOST: str = Field("smtp.gmail.com", env="SMTP_HOST", description="SMTP host.")
    SMTP_PORT: int = Field(587, env="SMTP_PORT", description="SMTP port.")
    
    MAIL_USERNAME: str =Field("dev.aiti.com.gh@gmail.com", env="MAIL_USERNAME")
    MAIL_PASSWORD: str =Field("", env="MAIL_PASSWORD")
    MAIL_FROM: str =Field("dev.aiti.com.gh@gmail.com", env="MAIL_FROM", )
    MAIL_PORT: int =Field(587, env="MAIL_PORT")
    MAIL_SERVER: str =Field("smtp.gmail.com",env="MAIL_SERVER")
    MAIL_STARTTLS: bool = Field(True, env="MAIL_STARTTLS")
    MAIL_SSL_TLS: bool =Field(False, env="MAIL_SSL_TLS")
    USE_CREDENTIALS: bool = Field(True, env="USE_CREDENTIALS")
    VALIDATE_CERTS: bool = Field(True, env="VALIDATE_CERTS")


    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL", description="Logging level (DEBUG, INFO, WARNING, ERROR).")

    # Role Permissions
    DEFAULT_PERMISSIONS: Dict[str, Dict[str, bool]] = Field(
        default={
            "staff": {
                "create_task": True,
                "view_task": True,
                "update_task": False,
                "delete_task": False,
            },
            "manager": {
                "create_task": True,
                "view_task": True,
                "update_task": True,
                "delete_task": False,
            },
            "admin": {
                "create_task": True,
                "view_task": True,
                "update_task": True,
                "delete_task": True,
            },
        },
        description="Default permissions for user roles.",
    )

    # Bulk Operation Configurations
    BULK_OPERATION_CONCURRENCY_LIMIT: int = Field(10, description="Maximum number of concurrent tasks for bulk operations.")

    # Email Retry Logic
    EMAIL_RETRY_ATTEMPTS: int = Field(3, description="Number of retry attempts for sending emails.")
    EMAIL_RETRY_DELAY: float = Field(1.0, description="Delay between email retries (in seconds).")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class DevelopmentConfig(BaseConfig):
    """
    Configuration for the development environment.
    """
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    BUCKET_NAME: str = "developers-bucket" 
    #GOOGLE_APPLICATION_CREDENTIALS:str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "google_cloud_storage_api.json")
    GOOGLE_APPLICATION_CREDENTIALS:str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'service_account.json'

class ProductionConfig(BaseConfig):
    """
    Configuration for the production environment.
    """
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"


class TestingConfig(BaseConfig):
    """
    Configuration for the testing environment.
    """
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./test.db"
    LOG_LEVEL: str = "DEBUG"


def get_config():
    """
    Load configuration based on the environment.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production":
        return ProductionConfig()
    elif environment == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()


# Load the appropriate configuration
config = get_config()
