from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VOXSHIELD_", env_file=".env", extra="ignore")
    demo_mode: bool = False
    cors_origins: str = "http://localhost:5173"
    sse_queue_size: int = Field(default=64, ge=1, le=1024)
    event_history_size: int = Field(default=128, ge=1, le=4096)
    max_sessions: int = Field(default=256, ge=1, le=4096)

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]
