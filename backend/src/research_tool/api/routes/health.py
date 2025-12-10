"""Health check endpoints with deep dependency checking."""

from datetime import datetime
from enum import Enum
from typing import Any

import httpx
from fastapi import APIRouter

from research_tool.core.config import settings
from research_tool.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/health", tags=["health"])


class HealthStatus(str, Enum):
    """Health status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


async def check_ollama() -> dict[str, Any]:
    """Check Ollama availability.

    Returns:
        dict with status and details
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return {
                    "status": HealthStatus.HEALTHY,
                    "models_available": models,
                    "model_count": len(models)
                }
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": f"HTTP {response.status_code}"
            }
    except httpx.ConnectError:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": "Connection refused - is Ollama running?"
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e)
        }


async def check_anthropic() -> dict[str, Any]:
    """Check Anthropic API key validity.

    Returns:
        dict with status and details
    """
    if not settings.anthropic_api_key:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": "ANTHROPIC_API_KEY not configured"
        }

    # Just verify key format - don't make actual API call to save costs
    if settings.anthropic_api_key.startswith("sk-ant-"):
        return {
            "status": HealthStatus.HEALTHY,
            "key_configured": True,
            "key_format_valid": True
        }

    return {
        "status": HealthStatus.DEGRADED,
        "key_configured": True,
        "key_format_valid": False,
        "warning": "Key format unexpected (should start with sk-ant-)"
    }


async def check_search_providers() -> dict[str, Any]:
    """Check search provider availability.

    Returns:
        dict with status per provider
    """
    providers = {}

    # Tavily
    if settings.tavily_api_key:
        providers["tavily"] = {"status": HealthStatus.HEALTHY, "configured": True}
    else:
        providers["tavily"] = {"status": HealthStatus.UNHEALTHY, "configured": False}

    # Brave
    if settings.brave_api_key:
        providers["brave"] = {"status": HealthStatus.HEALTHY, "configured": True}
    else:
        providers["brave"] = {"status": HealthStatus.UNHEALTHY, "configured": False}

    # Free providers (always available)
    providers["semantic_scholar"] = {"status": HealthStatus.HEALTHY, "configured": True}
    providers["pubmed"] = {"status": HealthStatus.HEALTHY, "configured": True}
    providers["arxiv"] = {"status": HealthStatus.HEALTHY, "configured": True}

    return providers


@router.get("")
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint.

    Returns:
        dict with status and version
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/detailed")
async def detailed_health_check() -> dict[str, Any]:
    """Detailed health check with all dependencies.

    Returns:
        dict with status of all components
    """
    logger.info("detailed_health_check_start")

    # Check all components
    ollama_status = await check_ollama()
    anthropic_status = await check_anthropic()
    providers_status = await check_search_providers()

    # Determine overall status
    overall = HealthStatus.HEALTHY

    if anthropic_status["status"] == HealthStatus.UNHEALTHY:
        overall = HealthStatus.UNHEALTHY
    elif (
        ollama_status["status"] == HealthStatus.UNHEALTHY
        and anthropic_status["status"] != HealthStatus.HEALTHY
    ):
        # Ollama is optional if Anthropic works
        overall = HealthStatus.DEGRADED

    # Count available search providers
    available_providers = sum(
        1 for p in providers_status.values()
        if p["status"] == HealthStatus.HEALTHY
    )
    if available_providers < 2:
        overall = HealthStatus.DEGRADED

    result = {
        "status": overall.value,
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "ollama": ollama_status,
            "anthropic": anthropic_status,
            "search_providers": providers_status
        },
        "summary": {
            "search_providers_available": available_providers,
            "llm_available": anthropic_status["status"] == HealthStatus.HEALTHY,
            "local_llm_available": ollama_status["status"] == HealthStatus.HEALTHY
        }
    }

    logger.info(
        "detailed_health_check_complete",
        overall_status=overall.value,
        providers_available=available_providers
    )

    return result


@router.get("/config")
async def config_status() -> dict[str, Any]:
    """Get current configuration status (safe, no secrets).

    Returns:
        dict with configuration status
    """
    feature_status = settings.get_feature_status()

    return {
        "config": settings.to_safe_dict(),
        "features": {k: v.value for k, v in feature_status.items()},
        "missing_keys": settings.get_missing_keys(),
        "configured_keys": settings.get_configured_keys()
    }
