"""Application configuration."""


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # API Keys
    tavily_api_key: str | None = None
    anthropic_api_key: str | None = None
    exa_api_key: str | None = None
    brave_api_key: str | None = None
    semantic_scholar_api_key: str | None = None

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_num_parallel: int = 4

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    # Paths
    data_dir: str = "./data"


settings = Settings()
