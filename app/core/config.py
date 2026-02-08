from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    FIRECRAWL_API_KEY: str
    PROJECT_NAME: str = "Coletor de Promoções ML"
    MAX_RETRIES: int = 3
    RETRY_MIN_SECONDS: int = 2
    RETRY_MAX_SECONDS: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

settings = Settings()