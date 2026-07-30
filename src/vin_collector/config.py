"""Configuración central del proyecto (Pydantic Settings + rutas fijas)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), extra="ignore")

    # Rutas
    root_dir: Path = ROOT_DIR
    input_dir: Path = ROOT_DIR / "input"
    output_dir: Path = ROOT_DIR / "output"
    images_dir: Path = ROOT_DIR / "output" / "images"
    thumbnails_dir: Path = ROOT_DIR / "output" / "thumbnails"
    cache_dir: Path = ROOT_DIR / "cache"
    logs_dir: Path = ROOT_DIR / "logs"
    database_dir: Path = ROOT_DIR / "database"
    config_dir: Path = ROOT_DIR / "config"

    @property
    def db_path(self) -> Path:
        return self.database_dir / "catalog.db"

    @property
    def brands_path(self) -> Path:
        return self.config_dir / "marcas.json"

    @property
    def categories_path(self) -> Path:
        return self.config_dir / "categorias.json"

    # API keys opcionales
    anthropic_api_key: str | None = None
    google_cse_api_key: str | None = None
    google_cse_cx: str | None = None

    # Comportamiento
    log_level: str = "INFO"
    http_timeout_seconds: float = 20.0
    max_search_results_per_query: int = 10
    min_acceptable_score: int = 60
    thumbnail_sizes: tuple[int, ...] = (200, 400, 800, 1200)
    request_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VINProductImageCollector/0.1"
    )

    def ensure_dirs(self) -> None:
        for d in (
            self.input_dir,
            self.output_dir,
            self.images_dir,
            self.thumbnails_dir,
            self.cache_dir,
            self.logs_dir,
            self.database_dir,
            self.config_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
