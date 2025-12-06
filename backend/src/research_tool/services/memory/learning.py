"""Source effectiveness learning using exponential moving average."""


from .sqlite_repo import SQLiteRepository


class SourceLearning:
    """Track and learn source effectiveness using exponential moving average."""

    # EMA smoothing factor (α)
    # Higher α = more weight to recent results
    # Lower α = more weight to historical average
    ALPHA = 0.3

    def __init__(self, repo: SQLiteRepository):
        """Initialize source learning.

        Args:
            repo: SQLite repository for persistence
        """
        self.repo = repo

    async def update_effectiveness(
        self,
        source_name: str,
        domain: str,
        success: bool,
        quality_score: float
    ) -> float:
        """Update source effectiveness using exponential moving average.

        Formula: new_score = α * current_result + (1-α) * old_score

        Args:
            source_name: Name of the source
            domain: Domain the source was used for
            success: Whether the source successfully provided results
            quality_score: Quality score of the results (0.0 to 1.0)

        Returns:
            float: The new effectiveness score
        """
        # Get current effectiveness score
        current = await self.repo.get_source_effectiveness(source_name, domain)
        if current is None:
            current = 0.5  # Default neutral score for new sources

        # Calculate result score (0 if failed, quality_score if successful)
        result_score = quality_score if success else 0.0

        # Apply exponential moving average
        new_score = self.ALPHA * result_score + (1 - self.ALPHA) * current

        # Update in database
        await self.repo.set_source_effectiveness(
            source_name=source_name,
            domain=domain,
            effectiveness_score=new_score,
            quality_score=quality_score if success else None,
            success=success
        )

        return new_score

    async def get_ranked_sources(
        self,
        domain: str,
        available_sources: list[str]
    ) -> list[tuple[str, float]]:
        """Get sources ranked by effectiveness for domain.

        Args:
            domain: Domain to get rankings for
            available_sources: List of available source names

        Returns:
            list[tuple[str, float]]: List of (source_name, effectiveness_score) tuples,
                                    sorted by score descending
        """
        return await self.repo.get_ranked_sources(domain, available_sources)

    async def should_use_source(
        self,
        source_name: str,
        domain: str,
        threshold: float = 0.3
    ) -> bool:
        """Determine if a source should be used based on effectiveness.

        Args:
            source_name: Name of the source
            domain: Domain to check
            threshold: Minimum effectiveness score to use source

        Returns:
            bool: True if source should be used
        """
        score = await self.repo.get_source_effectiveness(source_name, domain)

        # Unknown sources get benefit of the doubt
        if score is None:
            return True

        return score >= threshold

    async def get_effectiveness_stats(
        self,
        source_name: str,
        domain: str
    ) -> dict | None:
        """Get detailed effectiveness statistics for a source.

        Args:
            source_name: Name of the source
            domain: Domain to get stats for

        Returns:
            dict: Statistics including score, queries, success rate, etc.
                  None if source has no history in this domain
        """
        score = await self.repo.get_source_effectiveness(source_name, domain)
        if score is None:
            return None

        # This is a simplified version - in a real implementation,
        # we'd query additional fields from the database
        return {
            "effectiveness_score": score,
            "source_name": source_name,
            "domain": domain
        }
