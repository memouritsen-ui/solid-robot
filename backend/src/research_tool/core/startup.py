"""Startup self-test to verify critical components."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from research_tool.core.config import settings
from research_tool.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StartupTestResult:
    """Result of a single startup test."""

    name: str
    passed: bool
    message: str
    duration_ms: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class StartupReport:
    """Complete startup test report."""

    tests: list[StartupTestResult]
    total_duration_ms: float
    all_passed: bool
    critical_failures: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "tests": [
                {
                    "name": t.name,
                    "passed": t.passed,
                    "message": t.message,
                    "duration_ms": t.duration_ms
                }
                for t in self.tests
            ],
            "total_duration_ms": self.total_duration_ms,
            "all_passed": self.all_passed,
            "critical_failures": self.critical_failures,
            "warnings": self.warnings
        }


async def test_data_directory() -> StartupTestResult:
    """Test that data directory exists and is writable."""
    start = datetime.now()

    data_dir = Path(settings.data_dir)

    try:
        # Create if not exists
        data_dir.mkdir(parents=True, exist_ok=True)

        # Test write
        test_file = data_dir / ".startup_test"
        test_file.write_text("test")
        test_file.unlink()

        duration = (datetime.now() - start).total_seconds() * 1000
        return StartupTestResult(
            name="data_directory",
            passed=True,
            message=f"Data directory OK: {data_dir.absolute()}",
            duration_ms=duration,
            details={"path": str(data_dir.absolute())}
        )
    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        return StartupTestResult(
            name="data_directory",
            passed=False,
            message=f"Data directory error: {e}",
            duration_ms=duration,
            details={"error": str(e)}
        )


async def test_domain_configs() -> StartupTestResult:
    """Test that domain configuration files exist."""
    start = datetime.now()

    data_dir = Path(settings.data_dir)
    config_dir = data_dir / "domain_configs"

    expected_configs = [
        "medical.json",
        "academic.json",
        "regulatory.json",
        "competitive_intelligence.json"
    ]

    try:
        missing = []
        found = []

        for config in expected_configs:
            config_path = config_dir / config
            if config_path.exists():
                found.append(config)
            else:
                missing.append(config)

        duration = (datetime.now() - start).total_seconds() * 1000

        if missing:
            return StartupTestResult(
                name="domain_configs",
                passed=False,
                message=f"Missing domain configs: {missing}",
                duration_ms=duration,
                details={"found": found, "missing": missing}
            )

        return StartupTestResult(
            name="domain_configs",
            passed=True,
            message=f"All {len(found)} domain configs found",
            duration_ms=duration,
            details={"found": found}
        )
    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        return StartupTestResult(
            name="domain_configs",
            passed=False,
            message=f"Domain config error: {e}",
            duration_ms=duration,
            details={"error": str(e)}
        )


async def test_llm_configuration() -> StartupTestResult:
    """Test that at least one LLM is configured."""
    start = datetime.now()

    has_cloud = bool(settings.anthropic_api_key)
    has_local = False

    # Quick check for Ollama
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            has_local = response.status_code == 200
    except Exception:
        pass

    duration = (datetime.now() - start).total_seconds() * 1000

    if not has_cloud and not has_local:
        return StartupTestResult(
            name="llm_configuration",
            passed=False,
            message="No LLM available - need ANTHROPIC_API_KEY or running Ollama",
            duration_ms=duration,
            details={"cloud": has_cloud, "local": has_local}
        )

    return StartupTestResult(
        name="llm_configuration",
        passed=True,
        message=f"LLM available (cloud={has_cloud}, local={has_local})",
        duration_ms=duration,
        details={"cloud": has_cloud, "local": has_local}
    )


async def test_search_providers() -> StartupTestResult:
    """Test that at least one search provider is available."""
    start = datetime.now()

    available = []

    # Free providers are always available
    available.extend(["semantic_scholar", "pubmed", "arxiv"])

    # Check configured providers
    if settings.tavily_api_key:
        available.append("tavily")
    if settings.brave_api_key:
        available.append("brave")
    if settings.exa_api_key:
        available.append("exa")

    duration = (datetime.now() - start).total_seconds() * 1000

    return StartupTestResult(
        name="search_providers",
        passed=True,
        message=f"{len(available)} search providers available",
        duration_ms=duration,
        details={"available": available}
    )


async def run_startup_tests() -> StartupReport:
    """Run all startup tests and return report.

    Returns:
        StartupReport with all test results
    """
    logger.info("startup_tests_begin")
    start = datetime.now()

    # Run all tests
    tests = [
        test_data_directory,
        test_domain_configs,
        test_llm_configuration,
        test_search_providers,
    ]

    results = await asyncio.gather(*[t() for t in tests])

    # Analyze results
    critical_failures = []
    warnings = []

    for result in results:
        if not result.passed:
            if result.name in ["llm_configuration"]:
                critical_failures.append(f"{result.name}: {result.message}")
            else:
                warnings.append(f"{result.name}: {result.message}")

        # Log each result
        if result.passed:
            logger.info(
                "startup_test_passed",
                test=result.name,
                message=result.message,
                duration_ms=result.duration_ms
            )
        else:
            logger.warning(
                "startup_test_failed",
                test=result.name,
                message=result.message,
                duration_ms=result.duration_ms
            )

    total_duration = (datetime.now() - start).total_seconds() * 1000
    all_passed = len(critical_failures) == 0

    report = StartupReport(
        tests=list(results),
        total_duration_ms=total_duration,
        all_passed=all_passed,
        critical_failures=critical_failures,
        warnings=warnings
    )

    logger.info(
        "startup_tests_complete",
        all_passed=all_passed,
        total_duration_ms=total_duration,
        critical_failures=len(critical_failures),
        warnings=len(warnings)
    )

    return report
