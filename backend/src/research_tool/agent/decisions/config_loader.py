"""Domain configuration loading and merging.

Loads domain configurations from JSON files and supports
merging with learned overrides from memory.
"""

import json
from pathlib import Path
from typing import Any

from research_tool.core.logging import get_logger
from research_tool.models.domain import DomainConfiguration

logger = get_logger(__name__)

# Default path to domain config files
DEFAULT_CONFIG_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "domain_configs"


def load_domain_config(
    domain: str,
    config_dir: Path | None = None
) -> DomainConfiguration | None:
    """Load domain configuration from JSON file.

    Args:
        domain: Domain name (e.g., "medical", "academic")
        config_dir: Directory containing config files (default: data/domain_configs)

    Returns:
        DomainConfiguration if found, None if not found
    """
    config_dir = config_dir or DEFAULT_CONFIG_DIR
    config_path = config_dir / f"{domain}.json"

    logger.debug(
        "config_load_attempt",
        domain=domain,
        path=str(config_path)
    )

    if not config_path.exists():
        logger.info(
            "config_not_found",
            domain=domain,
            path=str(config_path)
        )
        return None

    try:
        with open(config_path) as f:
            data = json.load(f)

        config = DomainConfiguration(
            domain=data["domain"],
            primary_sources=data["primary_sources"],
            secondary_sources=data["secondary_sources"],
            academic_required=data["academic_required"],
            verification_threshold=data["verification_threshold"],
            keywords=data["keywords"],
            excluded_sources=data.get("excluded_sources", [])
        )

        logger.info(
            "config_loaded",
            domain=domain,
            primary_sources_count=len(config.primary_sources)
        )

        return config

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(
            "config_load_error",
            domain=domain,
            error=str(e)
        )
        return None


def merge_with_overrides(
    base_config: DomainConfiguration,
    overrides: dict[str, Any]
) -> DomainConfiguration:
    """Merge base configuration with learned overrides.

    Args:
        base_config: Base domain configuration
        overrides: Dictionary of override values

    Returns:
        New DomainConfiguration with overrides applied
    """
    # Start with base values
    domain = base_config.domain
    primary_sources = overrides.get(
        "primary_sources", base_config.primary_sources
    )
    secondary_sources = overrides.get(
        "secondary_sources", base_config.secondary_sources
    )
    academic_required = overrides.get(
        "academic_required", base_config.academic_required
    )
    verification_threshold = overrides.get(
        "verification_threshold", base_config.verification_threshold
    )
    keywords = overrides.get("keywords", base_config.keywords)
    excluded_sources = overrides.get(
        "excluded_sources", base_config.excluded_sources
    )

    # Log applied overrides
    for key in overrides:
        if key in {
            "primary_sources", "secondary_sources", "academic_required",
            "verification_threshold", "keywords", "excluded_sources"
        }:
            logger.debug(
                "config_override_applied",
                field=key,
                value=overrides[key]
            )

    return DomainConfiguration(
        domain=domain,
        primary_sources=primary_sources,
        secondary_sources=secondary_sources,
        academic_required=academic_required,
        verification_threshold=verification_threshold,
        keywords=keywords,
        excluded_sources=excluded_sources
    )


class ConfigLoader:
    """Loader for domain configurations with caching.

    Provides efficient loading and caching of domain configurations,
    with support for overrides from learned preferences.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize config loader.

        Args:
            config_dir: Directory containing config files
        """
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self._cache: dict[str, DomainConfiguration] = {}

    def load(self, domain: str) -> DomainConfiguration | None:
        """Load domain configuration with caching.

        Args:
            domain: Domain name

        Returns:
            DomainConfiguration if found, None otherwise
        """
        if domain in self._cache:
            logger.debug("config_cache_hit", domain=domain)
            return self._cache[domain]

        config = load_domain_config(domain, self.config_dir)

        if config:
            self._cache[domain] = config

        return config

    def load_with_overrides(
        self,
        domain: str,
        overrides: dict[str, Any]
    ) -> DomainConfiguration | None:
        """Load domain configuration and apply overrides.

        Args:
            domain: Domain name
            overrides: Override values to apply

        Returns:
            Merged DomainConfiguration if found, None otherwise
        """
        base_config = self.load(domain)

        if not base_config:
            return None

        return merge_with_overrides(base_config, overrides)

    def load_or_default(self, domain: str) -> DomainConfiguration:
        """Load domain configuration or return default.

        Args:
            domain: Domain name

        Returns:
            DomainConfiguration (loaded or default)
        """
        config = self.load(domain)

        if config:
            return config

        logger.info(
            "config_fallback_default",
            requested_domain=domain
        )

        return DomainConfiguration.default()

    def list_available_domains(self) -> list[str]:
        """List all available domain configurations.

        Returns:
            List of domain names with available configs
        """
        if not self.config_dir.exists():
            return []

        domains = []
        for path in self.config_dir.glob("*.json"):
            domains.append(path.stem)

        return sorted(domains)

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()
        logger.debug("config_cache_cleared")
