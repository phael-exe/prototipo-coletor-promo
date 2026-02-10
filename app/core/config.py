
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    USER_AGENT: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    PROJECT_NAME: str = "Coletor de Promoções ML"
    MAX_RETRIES: int = 3
    RETRY_MIN_SECONDS: int = 2
    RETRY_MAX_SECONDS: int = 10

    # Google Cloud Platform
    GCP_PROJECT_ID: str = "promozone-ml"
    GCP_DATASET_ID: str = "promocoes_teste"
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None  # Caminho para o JSON da service account

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

settings = Settings()
