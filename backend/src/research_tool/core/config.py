"""Application configuration with validation and status reporting."""

from enum import Enum
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from research_tool.core.logging import get_logger

logger = get_logger(__name__)


class FeatureStatus(Enum):
    """Status of optional features based on configuration."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    DEGRADED = "degraded"


class Settings(BaseSettings):
    """Application settings loaded from environment with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required API Keys
    anthropic_api_key: str | None = None

    # Optional Search Provider API Keys
    tavily_api_key: str | None = None
    exa_api_key: str | None = None
    brave_api_key: str | None = None
    semantic_scholar_api_key: str | None = None
    unpaywall_email: str | None = None

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_num_parallel: int = 4

    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    # Paths
    data_dir: str = "./data"

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str | None) -> str | None:
        """Validate Anthropic API key format."""
        if v and not v.startswith("sk-ant-"):
            logger.warning(
                "anthropic_key_format_warning",
                message="Anthropic API key should start with 'sk-ant-'"
            )
        return v

    @field_validator("tavily_api_key")
    @classmethod
    def validate_tavily_key(cls, v: str | None) -> str | None:
        """Validate Tavily API key format."""
        if v and not v.startswith("tvly-"):
            logger.warning(
                "tavily_key_format_warning",
                message="Tavily API key should start with 'tvly-'"
            )
        return v

    def get_feature_status(self) -> dict[str, FeatureStatus]:
        """Get status of all features based on configuration.

        Returns:
            dict mapping feature name to its status
        """
        return {
            "cloud_llm": (
                FeatureStatus.ENABLED if self.anthropic_api_key
                else FeatureStatus.DISABLED
            ),
            "tavily_search": (
                FeatureStatus.ENABLED if self.tavily_api_key
                else FeatureStatus.DISABLED
            ),
            "brave_search": (
                FeatureStatus.ENABLED if self.brave_api_key
                else FeatureStatus.DISABLED
            ),
            "exa_search": (
                FeatureStatus.ENABLED if self.exa_api_key
                else FeatureStatus.DISABLED
            ),
            "semantic_scholar": FeatureStatus.ENABLED,  # No key required
            "pubmed": FeatureStatus.ENABLED,  # No key required
            "arxiv": FeatureStatus.ENABLED,  # No key required
            "unpaywall": (
                FeatureStatus.ENABLED if self.unpaywall_email
                else FeatureStatus.DEGRADED
            ),
        }

    def get_missing_keys(self) -> list[str]:
        """Get list of missing but recommended API keys.

        Returns:
            list of missing key names with descriptions
        """
        missing = []

        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY (REQUIRED for cloud LLM)")
        if not self.tavily_api_key:
            missing.append("TAVILY_API_KEY (recommended for web search)")

        return missing

    def get_configured_keys(self) -> list[str]:
        """Get list of configured API keys.

        Returns:
            list of configured key names
        """
        configured = []

        if self.anthropic_api_key:
            configured.append("ANTHROPIC_API_KEY")
        if self.tavily_api_key:
            configured.append("TAVILY_API_KEY")
        if self.brave_api_key:
            configured.append("BRAVE_API_KEY")
        if self.exa_api_key:
            configured.append("EXA_API_KEY")
        if self.semantic_scholar_api_key:
            configured.append("SEMANTIC_SCHOLAR_API_KEY")
        if self.unpaywall_email:
            configured.append("UNPAYWALL_EMAIL")

        return configured

    def validate_at_startup(self) -> bool:
        """Validate configuration at startup and log status.

        Returns:
            True if minimum required config is present, False otherwise
        """
        logger.info("config_validation_start")

        # Log configured keys
        configured = self.get_configured_keys()
        logger.info(
            "config_keys_configured",
            keys=configured,
            count=len(configured)
        )

        # Log missing keys
        missing = self.get_missing_keys()
        if missing:
            logger.warning(
                "config_keys_missing",
                keys=missing,
                count=len(missing)
            )

        # Log feature status
        features = self.get_feature_status()
        for feature, status in features.items():
            if status == FeatureStatus.DISABLED:
                logger.warning(
                    "feature_disabled",
                    feature=feature,
                    reason="Missing API key"
                )
            elif status == FeatureStatus.DEGRADED:
                logger.warning(
                    "feature_degraded",
                    feature=feature,
                    reason="Optional config missing"
                )

        # Check minimum requirements
        is_valid = self.anthropic_api_key is not None

        if not is_valid:
            logger.error(
                "config_validation_failed",
                reason="ANTHROPIC_API_KEY is required but not set"
            )
        else:
            logger.info("config_validation_passed")

        return is_valid

    def to_safe_dict(self) -> dict[str, Any]:
        """Get configuration as dict with secrets masked.

        Returns:
            dict with sensitive values replaced with '***'
        """
        return {
            "anthropic_api_key": "***" if self.anthropic_api_key else None,
            "tavily_api_key": "***" if self.tavily_api_key else None,
            "brave_api_key": "***" if self.brave_api_key else None,
            "exa_api_key": "***" if self.exa_api_key else None,
            "semantic_scholar_api_key": "***" if self.semantic_scholar_api_key else None,
            "unpaywall_email": self.unpaywall_email,  # Email is not secret
            "ollama_base_url": self.ollama_base_url,
            "ollama_num_parallel": self.ollama_num_parallel,
            "host": self.host,
            "port": self.port,
            "debug": self.debug,
            "data_dir": self.data_dir,
        }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance.

    Returns:
        Settings instance
    """
    return settings
