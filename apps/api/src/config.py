from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    CORS_ORIGINS: str = "http://localhost:3000,http://web:3000"

    model_config = {"env_file": ".env"}


settings = Settings()
