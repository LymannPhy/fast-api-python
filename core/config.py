import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    
    # Database
    DB_USER: str = os.getenv('POSTGRESQL_USER')
    DB_PASSWORD: str = os.getenv('POSTGRESQL_PASSWORD')
    DB_NAME: str = os.getenv('POSTGRESQL_DB')
    DB_HOST: str = os.getenv('POSTGRESQL_SERVER')
    DB_PORT: str = os.getenv('POSTGRESQL_PORT')

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # JWT 
    JWT_SECRET: str = os.getenv('JWT_SECRET', '709d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7')
    JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM', "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv('JWT_TOKEN_EXPIRE_MINUTES', 60)
    
    # Email Configuration
    EMAIL_TOKEN_EXPIRE_HOURS: int = os.getenv('EMAIL_TOKEN_EXPIRE_HOURS', 24)
    EMAIL_SENDER: str = os.getenv('EMAIL_SENDER') 
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD')
    SMTP_SERVER: str = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT: int = os.getenv('SMTP_PORT', 587) 

    
def get_settings() -> Settings:
    return Settings()
