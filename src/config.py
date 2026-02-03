"""Application configuration using pydantic-settings."""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Gemini API
    gemini_api_key: str = Field(..., description="Google Gemini API key")

    # ChromaDB
    chroma_persist_dir: str = Field(
        default="./data/chromadb",
        description="ChromaDB persistent storage directory",
    )

    # Output
    output_dir: str = Field(
        default="./output",
        description="Directory for generated markdown files",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Model settings
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Gemini model for general tasks",
    )
    gemini_research_model: str = Field(
        default="gemini-2.0-flash-thinking-exp",
        description="Gemini model for deep research tasks",
    )

    # Ideation settings
    min_ideas: int = Field(default=10, description="Minimum ideas in divergent phase")
    top_plays: int = Field(default=3, description="Number of top plays to select")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def ensure_dirs(self) -> None:
        """Create necessary directories if they don't exist."""
        Path(self.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """Get application settings (cached)."""
    return Settings()
