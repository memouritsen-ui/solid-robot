"""Domain configuration for research."""

from dataclasses import dataclass


@dataclass
class DomainConfiguration:
    """Per-domain source configuration and requirements."""

    domain: str
    primary_sources: list[str]
    secondary_sources: list[str]
    academic_required: bool
    verification_threshold: float
    keywords: list[str]
    excluded_sources: list[str]

    @classmethod
    def for_medical(cls) -> "DomainConfiguration":
        """Configuration for medical/healthcare research."""
        return cls(
            domain="medical",
            primary_sources=["pubmed", "semantic_scholar"],
            secondary_sources=["arxiv", "unpaywall", "playwright_crawler"],
            academic_required=True,
            verification_threshold=0.8,
            keywords=["clinical", "patient", "treatment", "diagnosis", "therapy",
                     "medical", "disease", "drug", "pharmaceutical"],
            excluded_sources=["wikipedia"]
        )

    @classmethod
    def for_competitive_intelligence(cls) -> "DomainConfiguration":
        """Configuration for competitive intelligence/business research."""
        return cls(
            domain="competitive_intelligence",
            primary_sources=["tavily", "exa", "brave", "playwright_crawler"],
            secondary_sources=["news_api"],
            academic_required=False,
            verification_threshold=0.6,
            keywords=["company", "market", "competitor", "funding", "product",
                     "revenue", "startup", "acquisition", "valuation"],
            excluded_sources=[]
        )

    @classmethod
    def for_academic(cls) -> "DomainConfiguration":
        """Configuration for general academic research."""
        return cls(
            domain="academic",
            primary_sources=["semantic_scholar", "arxiv"],
            secondary_sources=["pubmed", "unpaywall", "playwright_crawler"],
            academic_required=True,
            verification_threshold=0.7,
            keywords=["research", "study", "paper", "journal", "peer-reviewed",
                     "publication", "citation", "methodology"],
            excluded_sources=[]
        )

    @classmethod
    def for_regulatory(cls) -> "DomainConfiguration":
        """Configuration for regulatory/compliance research."""
        return cls(
            domain="regulatory",
            primary_sources=["tavily", "brave", "playwright_crawler"],
            secondary_sources=["pubmed"],
            academic_required=False,
            verification_threshold=0.9,  # High threshold for regulatory
            keywords=["regulation", "compliance", "FDA", "policy", "law",
                     "requirement", "standard", "guideline"],
            excluded_sources=[]
        )

    @classmethod
    def default(cls) -> "DomainConfiguration":
        """Default configuration for unknown domains."""
        return cls(
            domain="general",
            primary_sources=["tavily", "brave", "playwright_crawler"],
            secondary_sources=["semantic_scholar"],
            academic_required=False,
            verification_threshold=0.6,
            keywords=[],
            excluded_sources=[]
        )
