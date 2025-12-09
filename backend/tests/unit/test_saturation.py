"""Tests for saturation detection logic."""


from research_tool.agent.decisions.saturation import (
    SaturationMetrics,
    calculate_saturation,
    should_stop,
)


class TestSaturationMetrics:
    """Test suite for SaturationMetrics dataclass."""

    def test_to_dict_converts_to_dictionary(self) -> None:
        """to_dict converts metrics to dictionary."""
        metrics = SaturationMetrics(
            new_entities_ratio=0.10,
            new_facts_ratio=0.15,
            citation_circularity=0.20,
            source_coverage=0.50
        )

        result = metrics.to_dict()

        assert result == {
            "new_entities_ratio": 0.10,
            "new_facts_ratio": 0.15,
            "citation_circularity": 0.20,
            "source_coverage": 0.50
        }


class TestCalculateSaturation:
    """Test suite for calculate_saturation function."""

    def test_calculate_saturation_with_new_entities(self) -> None:
        """calculate_saturation computes new entities ratio correctly."""
        metrics = calculate_saturation(
            entities_before=10,
            entities_after=20,
            facts_before=0,
            facts_after=0,
            circular_citations=0,
            total_citations=1,
            sources_queried=1,
            sources_available=10
        )

        # 10 new entities out of 20 total = 0.5
        assert metrics.new_entities_ratio == 0.5

    def test_calculate_saturation_with_new_facts(self) -> None:
        """calculate_saturation computes new facts ratio correctly."""
        metrics = calculate_saturation(
            entities_before=0,
            entities_after=0,
            facts_before=50,
            facts_after=100,
            circular_citations=0,
            total_citations=1,
            sources_queried=1,
            sources_available=10
        )

        # 50 new facts out of 100 total = 0.5
        assert metrics.new_facts_ratio == 0.5

    def test_calculate_saturation_handles_zero_totals(self) -> None:
        """calculate_saturation handles zero totals without division by zero."""
        metrics = calculate_saturation(
            entities_before=0,
            entities_after=0,
            facts_before=0,
            facts_after=0,
            circular_citations=0,
            total_citations=0,
            sources_queried=0,
            sources_available=0
        )

        # Should use max(x, 1) to avoid division by zero
        assert metrics.new_entities_ratio == 0.0
        assert metrics.new_facts_ratio == 0.0
        assert metrics.citation_circularity == 0.0
        assert metrics.source_coverage == 0.0

    def test_calculate_saturation_citation_circularity(self) -> None:
        """calculate_saturation computes citation circularity correctly."""
        metrics = calculate_saturation(
            entities_before=0,
            entities_after=0,
            facts_before=0,
            facts_after=0,
            circular_citations=8,
            total_citations=10,
            sources_queried=1,
            sources_available=10
        )

        # 8 circular out of 10 total = 0.8
        assert metrics.citation_circularity == 0.8

    def test_calculate_saturation_source_coverage(self) -> None:
        """calculate_saturation computes source coverage correctly."""
        metrics = calculate_saturation(
            entities_before=0,
            entities_after=0,
            facts_before=0,
            facts_after=0,
            circular_citations=0,
            total_citations=1,
            sources_queried=9,
            sources_available=10
        )

        # 9 queried out of 10 available = 0.9
        assert metrics.source_coverage == 0.9


class TestShouldStop:
    """Test suite for should_stop decision function."""

    def test_saturation_detected_at_entity_threshold(self) -> None:
        """should_stop returns True when entity saturation threshold reached.

        Threshold: new_entities_ratio < 0.05
        """
        metrics = SaturationMetrics(
            new_entities_ratio=0.04,  # Below 0.05 threshold
            new_facts_ratio=0.50,
            citation_circularity=0.20,
            source_coverage=0.50
        )

        should_stop_flag, reason = should_stop(metrics)

        assert should_stop_flag is True
        assert "Entity saturation" in reason
        assert "4.0%" in reason or "4%" in reason

    def test_saturation_detected_at_fact_threshold(self) -> None:
        """should_stop returns True when fact saturation threshold reached.

        Threshold: new_facts_ratio < 0.05
        """
        metrics = SaturationMetrics(
            new_entities_ratio=0.50,
            new_facts_ratio=0.03,  # Below 0.05 threshold
            citation_circularity=0.20,
            source_coverage=0.50
        )

        should_stop_flag, reason = should_stop(metrics)

        assert should_stop_flag is True
        assert "Fact saturation" in reason
        assert "3.0%" in reason or "3%" in reason

    def test_saturation_detected_at_source_coverage_threshold(self) -> None:
        """should_stop returns True when source coverage threshold reached.

        Threshold: source_coverage > 0.95
        """
        metrics = SaturationMetrics(
            new_entities_ratio=0.50,
            new_facts_ratio=0.50,
            citation_circularity=0.20,
            source_coverage=0.96  # Above 0.95 threshold
        )

        should_stop_flag, reason = should_stop(metrics)

        assert should_stop_flag is True
        assert "Source coverage" in reason
        assert "96.0%" in reason or "96%" in reason

    def test_saturation_detected_at_circularity_threshold(self) -> None:
        """should_stop returns True when citation circularity threshold reached.

        Threshold: citation_circularity > 0.80
        """
        metrics = SaturationMetrics(
            new_entities_ratio=0.50,
            new_facts_ratio=0.50,
            citation_circularity=0.85,  # Above 0.80 threshold
            source_coverage=0.50
        )

        should_stop_flag, reason = should_stop(metrics)

        assert should_stop_flag is True
        assert "citation circularity" in reason.lower()
        assert "85.0%" in reason or "85%" in reason

    def test_research_continues_below_threshold(self) -> None:
        """should_stop returns False when all metrics below thresholds.

        All thresholds:
        - new_entities_ratio >= 0.05
        - new_facts_ratio >= 0.05
        - source_coverage <= 0.95
        - citation_circularity <= 0.80
        """
        metrics = SaturationMetrics(
            new_entities_ratio=0.10,  # Above 0.05
            new_facts_ratio=0.10,     # Above 0.05
            citation_circularity=0.50, # Below 0.80
            source_coverage=0.50       # Below 0.95
        )

        should_stop_flag, reason = should_stop(metrics)

        assert should_stop_flag is False
        assert "not yet reached" in reason.lower()

    def test_boundary_entity_ratio_at_threshold(self) -> None:
        """should_stop at exact entity threshold (0.05) should continue."""
        metrics = SaturationMetrics(
            new_entities_ratio=0.05,  # Exactly at threshold
            new_facts_ratio=0.50,
            citation_circularity=0.20,
            source_coverage=0.50
        )

        should_stop_flag, reason = should_stop(metrics)

        # Threshold is < 0.05, so 0.05 should continue
        assert should_stop_flag is False

    def test_boundary_fact_ratio_at_threshold(self) -> None:
        """should_stop at exact fact threshold (0.05) should continue."""
        metrics = SaturationMetrics(
            new_entities_ratio=0.50,
            new_facts_ratio=0.05,  # Exactly at threshold
            citation_circularity=0.20,
            source_coverage=0.50
        )

        should_stop_flag, reason = should_stop(metrics)

        # Threshold is < 0.05, so 0.05 should continue
        assert should_stop_flag is False

    def test_boundary_source_coverage_at_threshold(self) -> None:
        """should_stop at exact source coverage threshold (0.95) should continue."""
        metrics = SaturationMetrics(
            new_entities_ratio=0.50,
            new_facts_ratio=0.50,
            citation_circularity=0.20,
            source_coverage=0.95  # Exactly at threshold
        )

        should_stop_flag, reason = should_stop(metrics)

        # Threshold is > 0.95, so 0.95 should continue
        assert should_stop_flag is False

    def test_boundary_circularity_at_threshold(self) -> None:
        """should_stop at exact circularity threshold (0.80) should continue."""
        metrics = SaturationMetrics(
            new_entities_ratio=0.50,
            new_facts_ratio=0.50,
            citation_circularity=0.80,  # Exactly at threshold
            source_coverage=0.50
        )

        should_stop_flag, reason = should_stop(metrics)

        # Threshold is > 0.80, so 0.80 should continue
        assert should_stop_flag is False

    def test_entity_saturation_takes_priority(self) -> None:
        """should_stop checks entity saturation first."""
        metrics = SaturationMetrics(
            new_entities_ratio=0.01,  # Below threshold (checked first)
            new_facts_ratio=0.01,     # Also below threshold
            citation_circularity=0.90, # Also above threshold
            source_coverage=0.99       # Also above threshold
        )

        should_stop_flag, reason = should_stop(metrics)

        # Should return entity saturation reason (checked first)
        assert should_stop_flag is True
        assert "Entity saturation" in reason


class TestIntegrationScenarios:
    """Integration tests for realistic saturation scenarios."""

    def test_early_research_not_saturated(self) -> None:
        """Early research with lots of new info should continue."""
        metrics = calculate_saturation(
            entities_before=10,
            entities_after=50,   # 40 new entities
            facts_before=20,
            facts_after=100,     # 80 new facts
            circular_citations=5,
            total_citations=100,
            sources_queried=2,
            sources_available=10
        )

        should_stop_flag, reason = should_stop(metrics)

        assert should_stop_flag is False
        assert metrics.new_entities_ratio == 0.8  # 40/50
        assert metrics.new_facts_ratio == 0.8     # 80/100

    def test_exhausted_research_saturated(self) -> None:
        """Exhausted research with minimal new info should stop."""
        metrics = calculate_saturation(
            entities_before=100,
            entities_after=102,  # Only 2 new entities
            facts_before=200,
            facts_after=204,     # Only 4 new facts
            circular_citations=50,
            total_citations=60,
            sources_queried=9,
            sources_available=10
        )

        should_stop_flag, reason = should_stop(metrics)

        assert should_stop_flag is True
        # Either entity or fact saturation triggered
        assert metrics.new_entities_ratio < 0.05 or metrics.new_facts_ratio < 0.05
