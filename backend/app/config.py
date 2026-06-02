from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_image_model: str = "gemini-2.5-flash-image"
    storage_dir: str = "./app/storage"
    max_upload_mb: int = 15
    cors_origins: str = "http://localhost:3000"

    @property
    def storage_path(self) -> Path:
        return Path(self.storage_dir).resolve()

    @property
    def upload_dir(self) -> Path:
        p = self.storage_path / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def output_dir(self) -> Path:
        p = self.storage_path / "outputs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
