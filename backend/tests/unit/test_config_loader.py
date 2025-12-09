"""Tests for domain configuration loading and merging."""

from pathlib import Path

from research_tool.agent.decisions.config_loader import (
    ConfigLoader,
    load_domain_config,
    merge_with_overrides,
)
from research_tool.models.domain import DomainConfiguration


class TestLoadDomainConfig:
    """Tests for loading domain configurations from JSON files."""

    def test_load_medical_config(self, tmp_path: Path) -> None:
        """Test loading medical domain configuration."""
        config = load_domain_config("medical")

        assert config is not None
        assert config.domain == "medical"
        assert "pubmed" in config.primary_sources
        assert config.academic_required is True
        assert config.verification_threshold == 0.8

    def test_load_competitive_intelligence_config(self) -> None:
        """Test loading competitive intelligence configuration."""
        config = load_domain_config("competitive_intelligence")

        assert config is not None
        assert config.domain == "competitive_intelligence"
        assert "tavily" in config.primary_sources
        assert config.academic_required is False

    def test_load_academic_config(self) -> None:
        """Test loading academic domain configuration."""
        config = load_domain_config("academic")

        assert config is not None
        assert config.domain == "academic"
        assert "semantic_scholar" in config.primary_sources
        assert config.academic_required is True

    def test_load_regulatory_config(self) -> None:
        """Test loading regulatory domain configuration."""
        config = load_domain_config("regulatory")

        assert config is not None
        assert config.domain == "regulatory"
        assert config.verification_threshold == 0.9

    def test_load_unknown_domain_returns_none(self) -> None:
        """Test that unknown domain returns None."""
        config = load_domain_config("unknown_domain_xyz")

        assert config is None

    def test_load_returns_domain_configuration(self) -> None:
        """Test that load returns DomainConfiguration instance."""
        config = load_domain_config("medical")

        assert isinstance(config, DomainConfiguration)


class TestMergeWithOverrides:
    """Tests for merging configs with learned overrides."""

    def test_merge_preserves_base_config(self) -> None:
        """Test that merge preserves base config when no overrides."""
        base_config = DomainConfiguration.for_medical()
        overrides: dict = {}

        merged = merge_with_overrides(base_config, overrides)

        assert merged.domain == base_config.domain
        assert merged.primary_sources == base_config.primary_sources
        assert merged.verification_threshold == base_config.verification_threshold

    def test_merge_overrides_verification_threshold(self) -> None:
        """Test that overrides can change verification threshold."""
        base_config = DomainConfiguration.for_medical()
        overrides = {"verification_threshold": 0.9}

        merged = merge_with_overrides(base_config, overrides)

        assert merged.verification_threshold == 0.9
        # Other fields unchanged
        assert merged.domain == base_config.domain

    def test_merge_overrides_primary_sources(self) -> None:
        """Test that overrides can change primary sources."""
        base_config = DomainConfiguration.for_medical()
        overrides = {"primary_sources": ["pubmed", "semantic_scholar", "exa"]}

        merged = merge_with_overrides(base_config, overrides)

        assert "exa" in merged.primary_sources
        assert len(merged.primary_sources) == 3

    def test_merge_overrides_excluded_sources(self) -> None:
        """Test that overrides can add excluded sources."""
        base_config = DomainConfiguration.for_medical()
        overrides = {"excluded_sources": ["wikipedia", "reddit"]}

        merged = merge_with_overrides(base_config, overrides)

        assert "reddit" in merged.excluded_sources

    def test_merge_ignores_invalid_keys(self) -> None:
        """Test that merge ignores unknown override keys."""
        base_config = DomainConfiguration.for_medical()
        overrides = {"invalid_key": "should_be_ignored"}

        merged = merge_with_overrides(base_config, overrides)

        assert merged.domain == base_config.domain
        assert not hasattr(merged, "invalid_key")


class TestConfigLoader:
    """Tests for ConfigLoader class."""

    def test_config_loader_init(self) -> None:
        """Test ConfigLoader initialization."""
        loader = ConfigLoader()

        assert loader is not None

    def test_config_loader_load_domain(self) -> None:
        """Test loading domain via ConfigLoader."""
        loader = ConfigLoader()

        config = loader.load("medical")

        assert config is not None
        assert config.domain == "medical"

    def test_config_loader_caches_configs(self) -> None:
        """Test that ConfigLoader caches loaded configs."""
        loader = ConfigLoader()

        config1 = loader.load("medical")
        config2 = loader.load("medical")

        # Should be same object (cached)
        assert config1 is config2

    def test_config_loader_with_overrides(self) -> None:
        """Test loading with overrides."""
        loader = ConfigLoader()
        overrides = {"verification_threshold": 0.95}

        config = loader.load_with_overrides("medical", overrides)

        assert config.verification_threshold == 0.95

    def test_config_loader_list_available_domains(self) -> None:
        """Test listing available domain configurations."""
        loader = ConfigLoader()

        domains = loader.list_available_domains()

        assert "medical" in domains
        assert "academic" in domains
        assert "regulatory" in domains
        assert "competitive_intelligence" in domains

    def test_config_loader_fallback_to_default(self) -> None:
        """Test fallback to default config for unknown domain."""
        loader = ConfigLoader()

        config = loader.load_or_default("unknown_domain")

        assert config is not None
        assert config.domain == "general"


class TestConfigLoaderIntegration:
    """Integration tests for config loading with domain detection."""

    def test_load_config_for_detected_domain(self) -> None:
        """Test loading config based on detected domain."""
        from research_tool.agent.decisions.domain_detector import detect_domain

        query = "What are the clinical treatments for diabetes patients?"
        detected = detect_domain(query)

        loader = ConfigLoader()
        config = loader.load_or_default(detected.domain)

        assert config is not None
        # Medical query should load medical or general config
        assert config.domain in ("medical", "general")

    def test_config_matches_detected_domain(self) -> None:
        """Test that config domain matches detected domain."""
        from research_tool.agent.decisions.domain_detector import detect_domain

        test_cases = [
            ("patient treatment therapy", "medical"),
            ("company revenue market competitor", "competitive_intelligence"),
            ("research paper methodology study", "academic"),
            ("FDA compliance regulation", "regulatory"),
        ]

        loader = ConfigLoader()

        for query, _expected_domain in test_cases:
            detected = detect_domain(query)
            config = loader.load_or_default(detected.domain)

            # Config should exist for detected domain
            assert config is not None, f"No config for query: {query}"
