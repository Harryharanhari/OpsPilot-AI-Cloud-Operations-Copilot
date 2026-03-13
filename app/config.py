import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OpsPilot"
    DEBUG: bool = True

    # Set USE_SQLITE=true to run without PostgreSQL (great for local dev)
    USE_SQLITE: bool = os.getenv("USE_SQLITE", "false").lower() == "true"

    # Database (only needed when USE_SQLITE=false)
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "opspilot")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            return "sqlite:///./opspilot.db"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # AI Models
    CLASSIFIER_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    SUMMARIZER_MODEL: str = "facebook/bart-large-cnn"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # App Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
