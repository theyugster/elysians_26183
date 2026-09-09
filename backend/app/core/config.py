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

    # SIH 2026 — Configurable Hop Limit (with empirical justification)
    # Default: 5 hops | Maximum allowed: 10 hops
    # Justification: Chainalysis/Elliptic research shows >90% of laundered
    # funds reach an exchange within 5 hops. 10-hop hard cap prevents
    # resource exhaustion while allowing extended investigation.
    MAX_HOPS_LIMIT: int = 10

    # SIH 2026 — Value Continuity Threshold
    # If terminal wallet balance exceeds victim outflow by this percentage,
    # flag that funds have merged with innocent co-depositor balances.
    VALUE_CONTINUITY_THRESHOLD: float = 20.0

    # SIH 2026 — Confidence Gate Thresholds (BNSS Sec 94 Legal Compliance)
    CONFIDENCE_HIGH_THRESHOLD: int = 85   # Auto-generate BNSS Sec 94 Draft
    CONFIDENCE_REVIEW_THRESHOLD: int = 60  # Flag for Senior IO Review
    MIN_AGREEING_SIGNALS: int = 3          # Minimum heuristic signals that agree

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="allow")

settings = Settings()