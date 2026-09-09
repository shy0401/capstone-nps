from functools import lru_cache
from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: str = "dev"
    database_url: str = "sqlite:///./storage/local.db"
    redis_url: str = "redis://redis:6379/0"
    storage_root: Path = Path("storage")
    jwt_secret: str = ""
    access_minutes: int = 10
    refresh_days: int = 1
    dev_insecure_cookie: bool = False
    auth_provider: str = "local"
    scan_mode: str = "clamav"
    clamav_host: str = "clamav"
    clamav_port: int = 3310
    scan_timeout: int = 30
    upload_max_bytes: int = 100 * 1024 * 1024
    archive_max_bytes: int = 200 * 1024 * 1024
    archive_max_entries: int = 2000
    archive_max_ratio: int = 100
    parse_timeout: int = 45
    parse_memory_mb: int = 768
    max_pages: int = 200
    max_sheets: int = 30
    max_cells: int = 50000
    chunk_tokens: int = 500
    llm_mode: str = "mock"
    llm_adapter_url: str = "http://llm-adapter:8010"
    llm_backend_url: str = "http://llm-server:11434"
    llm_model: str = "TBD-NPS-GPU-001"
    llm_backend_hosts: str = "llm-server"
    llm_timeout: int = 60
    llm_retries: int = 2
    comfy_mode: str = "mock"
    comfy_adapter_url: str = "http://comfy-adapter:8020"
    comfy_backend_url: str = "http://comfyui-image:8188"
    comfy_backend_hosts: str = "comfyui-image,comfyui-video"
    adapter_secret: str = ""
    hwp_enabled: bool = True
    allowed_origins: str = "http://localhost:8080,http://127.0.0.1:8080"
    worker_lease_seconds: int = 120
    worker_vram_mb: int = 0
    worker_capability: str = "cpu"
    video_fps: int = 24
    video_scene_seconds: float = 2
    font_path: str = ""
    template_policy: Path = Path("templates/default.json")
    seed_password: str = ""

    @model_validator(mode="after")
    def secure_configuration(self):
        if self.environment in {"prod", "offline"}:
            if self.scan_mode != "clamav" or self.dev_insecure_cookie:
                raise ValueError("prod/offline requires real malware scan and secure cookies")
            if self.database_url.startswith("sqlite"):
                raise ValueError("prod/offline requires PostgreSQL")
        return self


@lru_cache
def settings() -> Settings:
    return Settings()
