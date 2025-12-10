"""Semantic privacy detection using sentence-transformers.

Task #229: Enhance recommend_privacy_mode() with NLP.

Uses semantic similarity to detect sensitive content that keyword matching
would miss. For example, "my patient's symptoms" is medical-sensitive even
without the word "medical".
"""

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from research_tool.core.logging import get_logger

logger = get_logger(__name__)


# Sensitive topic categories with representative phrases
# These are used to create embeddings for semantic comparison
SENSITIVE_CATEGORIES: dict[str, list[str]] = {
    "medical": [
        "patient medical records",
        "diagnosis and treatment",
        "prescription medication",
        "health condition symptoms",
        "clinical test results",
        "medical history",
        "disease diagnosis",
        "patient health information",
        "HIPAA protected data",
        "healthcare treatment plan",
        "prescribe medication",
        "blood test results",
        "patient symptoms",
        "medical prescription",
        "healthcare data",
    ],
    "financial": [
        "bank account balance",
        "credit card number",
        "financial transactions",
        "investment portfolio",
        "tax return information",
        "salary and compensation",
        "loan application details",
        "banking credentials",
        "stock trading account",
        "personal finance records",
        "tax deduction calculation",
        "income tax filing",
        "financial tax records",
        "money transfer banking",
        "savings account",
    ],
    "pii": [
        "social security number",
        "passport identification",
        "home address location",
        "date of birth",
        "personal identity information",
        "driver's license number",
        "full legal name",
        "phone number contact",
        "email address personal",
        "biometric data",
    ],
    "corporate": [
        "confidential business strategy",
        "trade secret information",
        "proprietary technology",
        "internal company documents",
        "merger acquisition plans",
        "non-disclosure agreement",
        "competitive intelligence",
        "corporate financial reports",
        "employee personnel files",
        "business confidential data",
    ],
}

# Default similarity threshold for detecting sensitivity
# Based on empirical testing:
# - Sensitive queries typically score 0.25-0.50
# - Non-sensitive queries typically score <0.10
DEFAULT_THRESHOLD = 0.20


class SemanticPrivacyDetector:
    """Detect sensitive content using semantic similarity.

    Uses sentence-transformers to create embeddings of queries and compare
    them to known sensitive topic embeddings. This catches semantically
    similar queries even without exact keyword matches.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        threshold: float = DEFAULT_THRESHOLD,
    ):
        """Initialize semantic privacy detector.

        Args:
            model_name: Name of sentence-transformer model to use.
                       Default is lightweight model good for similarity.
            threshold: Cosine similarity threshold for detecting sensitivity.
                      Higher = fewer false positives, more false negatives.
        """
        self.model_name = model_name
        self.default_threshold = threshold
        self._model: SentenceTransformer | None = None
        self._category_embeddings: dict[str, NDArray[np.float32]] | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the sentence transformer model."""
        if self._model is None:
            logger.info("Loading sentence-transformer model", model=self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    @property
    def category_embeddings(self) -> dict[str, NDArray[np.float32]]:
        """Get or compute category embeddings (cached)."""
        if self._category_embeddings is None:
            self._category_embeddings = self._compute_category_embeddings()
        return self._category_embeddings

    def _compute_category_embeddings(self) -> dict[str, NDArray[np.float32]]:
        """Compute average embeddings for each sensitive category."""
        logger.info("Computing category embeddings for privacy detection")
        embeddings: dict[str, NDArray[np.float32]] = {}

        for category, phrases in SENSITIVE_CATEGORIES.items():
            # Get embeddings for all phrases in category
            phrase_embeddings = self.model.encode(
                phrases, convert_to_numpy=True, normalize_embeddings=True
            )
            # Average the embeddings to get category centroid
            embeddings[category] = np.mean(phrase_embeddings, axis=0).astype(np.float32)

        return embeddings

    def detect_sensitivity(
        self,
        query: str,
        threshold: float | None = None,
    ) -> tuple[bool, str | None]:
        """Detect if query contains sensitive content.

        Args:
            query: The user's query text
            threshold: Optional custom threshold (uses default if not specified)

        Returns:
            Tuple of (is_sensitive, category_name or None)
        """
        is_sensitive, category, _ = self.detect_sensitivity_with_confidence(
            query, threshold
        )
        return is_sensitive, category

    def detect_sensitivity_with_confidence(
        self,
        query: str,
        threshold: float | None = None,
    ) -> tuple[bool, str | None, float]:
        """Detect sensitivity with confidence score.

        Args:
            query: The user's query text
            threshold: Optional custom threshold

        Returns:
            Tuple of (is_sensitive, category_name or None, confidence_score)
        """
        if not query or not query.strip():
            return False, None, 0.0

        threshold = threshold if threshold is not None else self.default_threshold

        # Truncate very long queries to avoid memory issues
        # Most semantic meaning is in first 512 tokens anyway
        truncated_query = query[:2000] if len(query) > 2000 else query

        # Get query embedding
        query_embedding = self.model.encode(
            truncated_query, convert_to_numpy=True, normalize_embeddings=True
        )

        # Compare to each category
        best_category: str | None = None
        best_similarity: float = 0.0

        for category, cat_embedding in self.category_embeddings.items():
            # Cosine similarity (embeddings are normalized, so dot product = cosine)
            similarity = float(np.dot(query_embedding, cat_embedding))

            if similarity > best_similarity:
                best_similarity = similarity
                best_category = category

        # Check if best match exceeds threshold
        is_sensitive = best_similarity >= threshold

        logger.debug(
            "Privacy detection result",
            query_preview=query[:50],
            is_sensitive=is_sensitive,
            category=best_category if is_sensitive else None,
            confidence=best_similarity,
            threshold=threshold,
        )

        return (
            is_sensitive,
            best_category if is_sensitive else None,
            best_similarity,
        )

    def get_all_similarities(
        self, query: str
    ) -> dict[str, float]:
        """Get similarity scores for all categories (for debugging/transparency).

        Args:
            query: The user's query text

        Returns:
            Dict mapping category name to similarity score
        """
        if not query or not query.strip():
            return dict.fromkeys(SENSITIVE_CATEGORIES, 0.0)

        truncated_query = query[:2000] if len(query) > 2000 else query
        query_embedding = self.model.encode(
            truncated_query, convert_to_numpy=True, normalize_embeddings=True
        )

        return {
            category: float(np.dot(query_embedding, cat_embedding))
            for category, cat_embedding in self.category_embeddings.items()
        }


# Module-level singleton for efficiency (model loading is expensive)
_detector_instance: SemanticPrivacyDetector | None = None


def get_semantic_privacy_detector() -> SemanticPrivacyDetector:
    """Get or create singleton SemanticPrivacyDetector.

    Using singleton because model loading is expensive (~1-2 seconds)
    and the model can be safely shared across requests.
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SemanticPrivacyDetector()
    return _detector_instance
