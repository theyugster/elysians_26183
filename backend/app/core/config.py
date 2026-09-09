from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ChainTrace-I4C Forensics Engine"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/chaintrace_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "default_secret_key_for_dev_mode"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day for IO field investigations
    
    # Forensic traversal parameters (Slide 3 & 4)
    MAX_HOPS: int = 5
    DUST_FILTER_PERCENTAGE: float = 3.0  # Branches < 3% of root victim value pruned

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="allow")

settings = Settings()