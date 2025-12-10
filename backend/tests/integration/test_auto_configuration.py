"""Integration tests for auto-configuration (#236).

Task #236: VALIDATE: Auto-configuration works for test queries

Tests that the full auto-configuration flow works:
1. Query → Domain detection
2. Domain → DomainConfiguration loading
3. Configuration → Correct sources selected
"""

from research_tool.agent.decisions.domain_detector import (
    detect_domain,
    get_domain_configuration,
)
from research_tool.agent.decisions.source_selector import select_sources_for_query
from research_tool.models.domain import DomainConfiguration


class TestAutoConfiguration:
    """Integration tests for auto-configuration flow."""

    def test_medical_query_gets_medical_config(self) -> None:
        """Test that medical queries get medical domain configuration."""
        query = "What are the latest clinical treatments for patients with heart disease?"

        # Step 1: Detect domain
        detected = detect_domain(query)

        # Step 2: Get config
        config = get_domain_configuration(detected)

        # Verify medical config loaded
        assert detected.domain == "medical", f"Expected medical, got {detected.domain}"
        assert config.domain == "medical"
        assert "pubmed" in config.primary_sources
        assert "semantic_scholar" in config.primary_sources
        assert config.academic_required is True
        assert config.verification_threshold >= 0.8

    def test_competitive_intelligence_query_gets_ci_config(self) -> None:
        """Test that CI queries get competitive intelligence configuration."""
        query = "What is the market share and revenue of Tesla competitors?"

        detected = detect_domain(query)
        config = get_domain_configuration(detected)

        assert detected.domain == "competitive_intelligence"
        assert config.domain == "competitive_intelligence"
        assert "tavily" in config.primary_sources or "exa" in config.primary_sources
        assert config.academic_required is False

    def test_academic_query_gets_academic_config(self) -> None:
        """Test that academic queries get academic configuration."""
        query = "Find peer-reviewed research papers on machine learning methodology"

        detected = detect_domain(query)
        config = get_domain_configuration(detected)

        assert detected.domain == "academic"
        assert config.domain == "academic"
        assert "semantic_scholar" in config.primary_sources
        assert "arxiv" in config.primary_sources
        assert config.academic_required is True

    def test_regulatory_query_gets_regulatory_config(self) -> None:
        """Test that regulatory queries get regulatory configuration."""
        query = "FDA compliance requirements for medical device regulations"

        detected = detect_domain(query)
        config = get_domain_configuration(detected)

        assert detected.domain == "regulatory"
        assert config.domain == "regulatory"
        assert config.verification_threshold >= 0.9  # High for regulatory

    def test_general_query_gets_default_config(self) -> None:
        """Test that general queries get default configuration."""
        query = "What is the weather like today?"

        detected = detect_domain(query)
        config = get_domain_configuration(detected)

        assert detected.domain == "general"
        assert config.domain == "general"

    def test_auto_config_selects_correct_sources_medical(self) -> None:
        """Test that auto-config leads to correct source selection for medical."""
        query = "Clinical trial results for diabetes treatment in patients"

        detected = detect_domain(query)
        config = get_domain_configuration(detected)

        # Use source selector with config
        sources = select_sources_for_query(
            query=query,
            domain=detected.domain,
            domain_config=config
        )

        # Medical should prioritize academic sources
        assert "pubmed" in sources or "semantic_scholar" in sources, (
            f"Medical query should include academic sources, got: {sources}"
        )

    def test_auto_config_selects_correct_sources_ci(self) -> None:
        """Test that auto-config leads to correct source selection for CI."""
        query = "Competitor analysis for cloud services market share"

        detected = detect_domain(query)
        config = get_domain_configuration(detected)

        sources = select_sources_for_query(
            query=query,
            domain=detected.domain,
            domain_config=config
        )

        # CI should include web search sources
        has_web_source = any(s in sources for s in ["tavily", "exa", "brave"])
        assert has_web_source, f"CI query should include web sources, got: {sources}"

    def test_auto_config_excludes_specified_sources(self) -> None:
        """Test that auto-config respects excluded sources."""
        query = "Patient treatment outcomes in hospital settings"

        detected = detect_domain(query)
        config = get_domain_configuration(detected)

        sources = select_sources_for_query(
            query=query,
            domain=detected.domain,
            domain_config=config
        )

        # Medical config excludes wikipedia
        assert "wikipedia" not in sources, (
            f"Medical should exclude wikipedia, got: {sources}"
        )

    def test_auto_config_end_to_end_multiple_queries(self) -> None:
        """Test end-to-end auto-config for multiple query types."""
        test_cases = [
            ("What drugs treat depression in patients?", "medical"),
            ("Company valuation and market trends", "competitive_intelligence"),
            ("Peer-reviewed journal publications on AI", "academic"),
            ("FDA approval process for new drugs", "regulatory"),
        ]

        for query, expected_domain in test_cases:
            detected = detect_domain(query)
            config = get_domain_configuration(detected)

            assert detected.domain == expected_domain, (
                f"Query '{query[:40]}...' expected domain={expected_domain}, "
                f"got={detected.domain}"
            )

            # Config should match detected domain
            expected_config_domain = expected_domain
            if expected_domain == "general":
                expected_config_domain = "general"

            assert config.domain == expected_config_domain, (
                f"Config domain mismatch for '{query[:40]}...': "
                f"expected={expected_config_domain}, got={config.domain}"
            )

            # Should be able to select sources
            sources = select_sources_for_query(
                query=query,
                domain=detected.domain,
                domain_config=config
            )

            assert len(sources) > 0, (
                f"No sources selected for '{query[:40]}...'"
            )

    def test_config_factory_methods_match_domains(self) -> None:
        """Test that DomainConfiguration factory methods produce correct configs."""
        factories = {
            "medical": DomainConfiguration.for_medical,
            "competitive_intelligence": DomainConfiguration.for_competitive_intelligence,
            "academic": DomainConfiguration.for_academic,
            "regulatory": DomainConfiguration.for_regulatory,
            "general": DomainConfiguration.default,
        }

        for expected_domain, factory in factories.items():
            config = factory()
            assert config.domain == expected_domain, (
                f"Factory for {expected_domain} produced domain={config.domain}"
            )
            assert len(config.primary_sources) > 0, (
                f"Config for {expected_domain} has no primary sources"
            )
