"""Model selection logic based on task complexity and privacy requirements.

Implements decision tree from META-BUILD-GUIDE-v2.md Section 7.1.
"""

from dataclasses import dataclass
from enum import Enum

from research_tool.core.logging import get_logger

logger = get_logger(__name__)


class PrivacyMode(Enum):
    """Privacy mode settings controlling model selection.

    LOCAL_ONLY: Data never leaves device. Only local models allowed.
    CLOUD_ALLOWED: Cloud APIs can be used for better results.
    HYBRID: Per-field privacy (future implementation).
    """

    LOCAL_ONLY = "local_only"
    CLOUD_ALLOWED = "cloud_allowed"
    HYBRID = "hybrid"


class TaskComplexity(Enum):
    """Task complexity levels affecting model choice.

    LOW: Simple queries, quick lookups
    MEDIUM: Standard analysis, summaries
    HIGH: Complex reasoning, multi-step analysis
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ModelRecommendation:
    """Result of model selection with reasoning.

    Attributes:
        model: Selected model name (e.g., 'local-fast', 'cloud-best')
        reasoning: Human-readable explanation of selection
        privacy_compliant: True if selection respects privacy mode
    """

    model: str
    reasoning: str
    privacy_compliant: bool


class ModelSelector:
    """Select appropriate model based on task complexity and privacy requirements.

    Implements decision tree from META-BUILD-GUIDE-v2.md Section 7.1:

    1. If privacy_mode == LOCAL_ONLY:
       - High complexity → local-powerful
       - Otherwise → local-fast
       - NEVER fall back to cloud

    2. If privacy_mode == CLOUD_ALLOWED:
       - High complexity → cloud-best (fallback: local-powerful)
       - Medium complexity → local-powerful
       - Low complexity → local-fast

    3. If privacy_mode == HYBRID:
       - Apply specific rules per data type (future)
    """

    # Sensitive keywords that trigger local-only recommendation
    SENSITIVE_KEYWORDS: list[str] = [
        "confidential",
        "private",
        "internal",
        "secret",
        "proprietary",
        "nda",
        "personal",
        "medical",
        "financial",
        "patient",
        "salary",
        "ssn",
        "password",
        "credentials",
        "hipaa",
        "gdpr",
        "pii",
    ]

    def select(
        self,
        task_complexity: TaskComplexity,
        privacy_mode: PrivacyMode,
        available_models: list[str] | None = None,
    ) -> ModelRecommendation:
        """Select the best model for the task.

        Args:
            task_complexity: Complexity level of the task
            privacy_mode: Privacy requirements
            available_models: List of available model names (defaults to all)

        Returns:
            ModelRecommendation with selected model and reasoning

        Raises:
            ValueError: If no compliant model is available
        """
        available = available_models or ["local-fast", "local-powerful", "cloud-best"]

        if privacy_mode == PrivacyMode.LOCAL_ONLY:
            return self._select_local_only(task_complexity, available)

        if privacy_mode == PrivacyMode.CLOUD_ALLOWED:
            return self._select_cloud_allowed(task_complexity, available)

        # HYBRID mode - default to cloud-allowed behavior for now
        return self._select_cloud_allowed(task_complexity, available)

    def _select_local_only(
        self, complexity: TaskComplexity, available: list[str]
    ) -> ModelRecommendation:
        """Select model when privacy requires local-only processing.

        CRITICAL: Never returns cloud model regardless of complexity.
        """
        if complexity == TaskComplexity.HIGH:
            if "local-powerful" in available:
                return ModelRecommendation(
                    model="local-powerful",
                    reasoning=(
                        "High complexity task with local-only privacy. "
                        "Using most capable local model."
                    ),
                    privacy_compliant=True,
                )
            if "local-fast" in available:
                return ModelRecommendation(
                    model="local-fast",
                    reasoning=(
                        "High complexity task but local-powerful unavailable. "
                        "Using local-fast with potential quality trade-off."
                    ),
                    privacy_compliant=True,
                )
            raise ValueError("No local models available but LOCAL_ONLY privacy mode set")

        # LOW or MEDIUM complexity
        if "local-fast" in available:
            return ModelRecommendation(
                model="local-fast",
                reasoning="Lower complexity task with local-only privacy. Using fast local model.",
                privacy_compliant=True,
            )
        if "local-powerful" in available:
            return ModelRecommendation(
                model="local-powerful",
                reasoning="Local-fast unavailable. Using local-powerful for local-only privacy.",
                privacy_compliant=True,
            )
        raise ValueError("No local models available but LOCAL_ONLY privacy mode set")

    def _select_cloud_allowed(
        self, complexity: TaskComplexity, available: list[str]
    ) -> ModelRecommendation:
        """Select model when cloud processing is allowed."""
        if complexity == TaskComplexity.HIGH:
            if "cloud-best" in available:
                return ModelRecommendation(
                    model="cloud-best",
                    reasoning=(
                        "High complexity task with cloud allowed. "
                        "Using most capable model for best results."
                    ),
                    privacy_compliant=True,
                )
            if "local-powerful" in available:
                return ModelRecommendation(
                    model="local-powerful",
                    reasoning="High complexity but cloud unavailable. Falling back to local.",
                    privacy_compliant=True,
                )

        if complexity == TaskComplexity.MEDIUM and "local-powerful" in available:
            return ModelRecommendation(
                model="local-powerful",
                reasoning=(
                    "Medium complexity task. "
                    "Local-powerful provides good balance of capability and efficiency."
                ),
                privacy_compliant=True,
            )

        # LOW complexity or fallback
        if "local-fast" in available:
            return ModelRecommendation(
                model="local-fast",
                reasoning="Low complexity task. Using fast model for efficiency.",
                privacy_compliant=True,
            )

        # Ultimate fallback
        if available:
            return ModelRecommendation(
                model=available[0],
                reasoning=f"Fallback to first available model: {available[0]}",
                privacy_compliant=True,
            )

        raise ValueError("No models available")

    def recommend_privacy_mode(
        self,
        query: str,
        has_sensitive_data: bool = False,
    ) -> tuple[PrivacyMode, str]:
        """Recommend privacy mode based on query content analysis.

        Analyzes query for sensitive keywords and patterns to recommend
        appropriate privacy mode. Errs on the side of privacy.

        Args:
            query: User's query text
            has_sensitive_data: Explicit flag if user marked data as sensitive

        Returns:
            Tuple of (recommended mode, human-readable reasoning)
        """
        if has_sensitive_data:
            return (
                PrivacyMode.LOCAL_ONLY,
                "Data explicitly marked as sensitive. Recommending local-only processing.",
            )

        query_lower = query.lower()
        found_sensitive = [kw for kw in self.SENSITIVE_KEYWORDS if kw in query_lower]

        if found_sensitive:
            keywords_str = ", ".join(found_sensitive[:3])
            if len(found_sensitive) > 3:
                keywords_str += f" (+{len(found_sensitive) - 3} more)"
            return (
                PrivacyMode.LOCAL_ONLY,
                f"Detected potentially sensitive content ({keywords_str}). "
                "Recommending local-only processing for privacy.",
            )

        return (
            PrivacyMode.CLOUD_ALLOWED,
            "No sensitive content detected. Cloud processing allowed for best results.",
        )

    def estimate_complexity(self, query: str, context_length: int = 0) -> TaskComplexity:
        """Estimate task complexity from query characteristics.

        Simple heuristic based on query length and certain keywords.
        Can be enhanced with more sophisticated analysis.

        Args:
            query: User's query text
            context_length: Length of conversation context

        Returns:
            Estimated TaskComplexity level
        """
        # Long queries or contexts suggest higher complexity
        total_length = len(query) + context_length

        # Keywords suggesting complex analysis
        complex_indicators = [
            "analyze",
            "compare",
            "evaluate",
            "synthesize",
            "critique",
            "comprehensive",
            "detailed",
            "in-depth",
            "multi-step",
            "reasoning",
        ]

        query_lower = query.lower()
        has_complex_indicators = any(ind in query_lower for ind in complex_indicators)

        if total_length > 2000 or has_complex_indicators:
            return TaskComplexity.HIGH

        if total_length > 500:
            return TaskComplexity.MEDIUM

        return TaskComplexity.LOW
