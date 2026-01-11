import os
from typing import Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Supply Chain Intelligence"
    debug: bool = True
    secret_key: str = "change-this-in-production"
    
    # Database
    database_url: str = "postgresql://supply_user:supply_pass@localhost:5432/supply_chain_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # API Keys
    google_api_key: str = ""
    tavily_api_key: str = ""
    
    # Security
    allowed_hosts: Union[str, list[str]] = ["localhost", "127.0.0.1"]
    session_cookie_name: str = "session"
    session_max_age: int = 60 * 60 * 24 * 7  # 7 days
    
    @field_validator('allowed_hosts', mode='before')
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            # Parse comma-separated string
            return [host.strip() for host in v.split(',')]
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra='ignore'
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
