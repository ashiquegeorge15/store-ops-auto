from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "store_ops"
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    
    # Akeneo settings
    AKENEO_URL: str = ""
    AKENEO_CLIENT_ID_SECRET: str = ""
    AKENEO_USERNAME: str = ""
    AKENEO_PASSWORD: str = ""
    
    # Falcon API settings
    FALCON_API_URL: str = ""
    FALCON_API_KEY: str = ""
    
    # Campaign settings
    DEFAULT_MOP_MULTIPLIER: float = 0.979
    DEFAULT_COINS: int = 2000
    
    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 