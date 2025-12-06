"""Entity and fact models for research extraction."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SourceResult:
    """Single result from a search source."""

    url: str
    title: str
    snippet: str
    source_name: str
    retrieved_at: datetime
    full_content: str | None = None
    quality_score: float = 0.5
    metadata: dict = field(default_factory=dict)


@dataclass
class Entity:
    """Extracted entity with provenance tracking."""

    name: str
    entity_type: str  # person, organization, product, location, etc.
    sources: list[str]  # URLs where this entity was found
    first_seen: datetime
    mention_count: int = 1
    confidence: float = 0.5
    metadata: dict = field(default_factory=dict)

    def merge(self, other: "Entity") -> None:
        """Merge another entity instance into this one."""
        if other.name == self.name and other.entity_type == self.entity_type:
            # Combine sources (unique)
            self.sources = list(set(self.sources + other.sources))
            # Increment mention count
            self.mention_count += other.mention_count
            # Update confidence (average)
            self.confidence = (self.confidence + other.confidence) / 2
            # Merge metadata
            self.metadata.update(other.metadata)


@dataclass
class Fact:
    """Verified fact with confidence and contradiction tracking."""

    statement: str
    sources: list[str]  # URLs supporting this fact
    confidence: float  # 0.0 to 1.0
    verified: bool
    contradictions: list[str] = field(default_factory=list)  # Conflicting statements
    extracted_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def add_source(self, url: str) -> None:
        """Add a supporting source and increase confidence."""
        if url not in self.sources:
            self.sources.append(url)
            # Increase confidence with more sources (with diminishing returns)
            source_boost = 0.1 / len(self.sources)
            self.confidence = min(1.0, self.confidence + source_boost)

    def add_contradiction(self, contradicting_statement: str) -> None:
        """Add a contradicting statement and reduce confidence."""
        if contradicting_statement not in self.contradictions:
            self.contradictions.append(contradicting_statement)
            # Reduce confidence when contradictions exist
            self.confidence = max(0.1, self.confidence - 0.15)
            self.verified = False
