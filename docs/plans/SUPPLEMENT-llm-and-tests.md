# SUPPLEMENT: LLM Router Interface & Test Handling

> **KRITISK:** Dette dokument forklarer LLMRouter's faktiske interface og hvordan tests skal håndteres.

---

## DEL 1: LLM ROUTER INTERFACE

### Faktisk Signatur

```python
async def complete(
    self,
    messages: list[dict[str, str]],
    model: str = "local-fast",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    stream: bool = False,
) -> str | AsyncIterator[str]:
```

### VIGTIGT: Return Type

- Når `stream=False`: Returnerer `str`
- Når `stream=True`: Returnerer `AsyncIterator[str]`

### Korrekt Brug i Nodes

**FORKERT (fra original plan):**
```python
# FEJL - dette virker men ignorer return type
response = await router.complete(messages=[...], model="local-fast")
```

**KORREKT (med explicit stream=False):**
```python
# OK - explicit at vi forventer string
response = await router.complete(
    messages=[{"role": "user", "content": prompt}],
    model="local-fast",
    temperature=0.1,
    max_tokens=2000,
    stream=False  # Explicit!
)
# response er nu garanteret str
```

### Opdatering til process.py Implementation

I `extract_facts_with_llm()` funktionen, ændre:

```python
response = await router.complete(
    messages=[{"role": "user", "content": prompt}],
    model="local-fast",
    temperature=0.1,
    max_tokens=2000,
    stream=False  # TILFØJ DENNE LINJE
)
```

### Opdatering til synthesize.py Implementation

I `generate_executive_summary()` funktionen, ændre:

```python
summary = await router.complete(
    messages=[{"role": "user", "content": prompt}],
    model="cloud-best",
    temperature=0.3,
    max_tokens=500,
    stream=False  # TILFØJ DENNE LINJE
)
```

---

## DEL 2: LLM ROUTER INTEGRATION TEST

**Opret fil:** `backend/tests/integration/test_llm_router_live.py`

```python
"""Live integration tests for LLM Router.

These tests require:
- ANTHROPIC_API_KEY set in .env for cloud tests
- Ollama running locally for local tests

Mark with pytest.mark.slow to skip in CI.
"""

import pytest

from research_tool.core.config import settings
from research_tool.services.llm.router import LLMRouter


@pytest.fixture
def router():
    """Create LLM router instance."""
    return LLMRouter()


class TestLLMRouterLive:
    """Live integration tests - require actual LLM services."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not settings.anthropic_api_key,
        reason="ANTHROPIC_API_KEY not configured"
    )
    async def test_cloud_completion(self, router):
        """Test cloud model returns valid response."""
        response = await router.complete(
            messages=[{"role": "user", "content": "Say 'test' and nothing else"}],
            model="cloud-best",
            temperature=0.0,
            max_tokens=10,
            stream=False
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert "test" in response.lower()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_local_completion(self, router):
        """Test local model returns valid response.

        Requires Ollama running with llama3.1:8b model.
        """
        # First check if model is available
        is_available = await router.is_model_available("local-fast")
        if not is_available:
            pytest.skip("local-fast model not available")

        response = await router.complete(
            messages=[{"role": "user", "content": "Say 'hello' and nothing else"}],
            model="local-fast",
            temperature=0.0,
            max_tokens=10,
            stream=False
        )

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not settings.anthropic_api_key,
        reason="ANTHROPIC_API_KEY not configured"
    )
    async def test_cloud_streaming(self, router):
        """Test cloud model streaming works."""
        tokens = []

        response = await router.complete(
            messages=[{"role": "user", "content": "Count to 3"}],
            model="cloud-best",
            temperature=0.0,
            max_tokens=20,
            stream=True
        )

        # Response should be async iterator when stream=True
        async for token in response:
            tokens.append(token)

        assert len(tokens) > 0
        full_response = "".join(tokens)
        assert len(full_response) > 0

    @pytest.mark.asyncio
    async def test_model_availability_check(self, router):
        """Test is_model_available method."""
        # Cloud should be available if API key is set
        if settings.anthropic_api_key:
            result = await router.is_model_available("cloud-best")
            # May or may not be available depending on API status
            assert isinstance(result, bool)

    def test_get_available_models(self, router):
        """Test getting list of configured models."""
        models = router.get_available_models()

        assert "local-fast" in models
        assert "local-powerful" in models
        assert "cloud-best" in models

    def test_get_context_window(self, router):
        """Test getting context window for models."""
        cloud_window = router.get_context_window("cloud-best")
        local_window = router.get_context_window("local-fast")

        assert cloud_window == 200000
        assert local_window == 128000

    def test_is_local_model(self, router):
        """Test checking if model is local."""
        assert router.is_local_model("local-fast") is True
        assert router.is_local_model("local-powerful") is True
        assert router.is_local_model("cloud-best") is False
```

---

## DEL 3: HÅNDTERING AF EKSISTERENDE TESTS

### Problem

Disse test-filer tester PLACEHOLDERS og vil FEJLE efter opdatering:

| Test fil | Tester | Handling |
|----------|--------|----------|
| `test_process.py` | Fake fact generation | ERSTAT med ny test |
| `test_analyze.py` | Tom shell | ERSTAT med ny test |
| `test_synthesize.py` | Dict uden LLM | ERSTAT med ny test |

### Strategi

1. **BACKUP** gamle tests før ændring
2. **ERSTAT** med nye tests fra hovedplanen
3. **KØR** nye tests - de skal FEJLE (rød)
4. **IMPLEMENTER** ny kode
5. **KØR** tests igen - de skal PASSE (grøn)

### Backup Kommandoer

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend

# Opret backup mappe
mkdir -p tests/archive/placeholder_tests

# Flyt gamle tests
mv tests/unit/test_process.py tests/archive/placeholder_tests/
mv tests/unit/test_analyze.py tests/archive/placeholder_tests/
mv tests/unit/test_synthesize.py tests/archive/placeholder_tests/

# Verificer
ls tests/archive/placeholder_tests/
```

### Nye Tests

Nye tests er ALLEREDE defineret i hovedplanen:
- Task 3.1 Step 2: `test_process_node_llm.py`
- Task 3.2 Step 1: `test_analyze_node.py`
- Task 3.3 Step 1: `test_synthesize_node.py`

---

## DEL 4: SEARCH PROVIDER TESTS

### Problem

Provider tests kalder `search()` direkte, men efter refactoring:
- `search()` er nu i base class og kalder `_do_search()`
- Tests skal stadig virke fordi `search()` eksisterer

### Verificering

```bash
cd /Users/madsbruusgaard-mouritsen/SOLID-ROBOT/backend

# Kør provider tests EFTER refactoring
uv run python -m pytest tests/unit/test_tavily.py tests/unit/test_brave.py -v

# Forventet: Tests passer stadig fordi search() eksisterer
```

### Hvis Tests Fejler

Tjek at:
1. `search()` metode eksisterer i base class
2. `_do_search()` er implementeret i hver provider
3. Imports er korrekte

---

## DEL 5: MOCKING I TESTS

### LLM Router Mocking

For tests der bruger LLM, brug mock:

```python
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_llm_router():
    """Create mocked LLM router."""
    mock = AsyncMock()
    mock.complete.return_value = '["fact 1", "fact 2"]'
    return mock


@patch("research_tool.agent.nodes.process.get_llm_router")
async def test_with_mocked_llm(mock_get_router, mock_llm_router):
    mock_get_router.return_value = mock_llm_router

    # Test code here
    result = await process_node(state)

    # Verify LLM was called
    mock_llm_router.complete.assert_called_once()
```

### Provider Mocking

For tests der ikke skal kalde rigtige APIs:

```python
@patch("research_tool.services.search.tavily.TavilyClient")
async def test_tavily_mocked(mock_client):
    mock_client.return_value.search.return_value = {
        "results": [{"url": "test.com", "title": "Test", "content": "..."}]
    }

    provider = TavilyProvider()
    results = await provider.search("test query")

    assert len(results) == 1
```

---

*Dette dokument supplerer hovedplanen med kritiske detaljer.*
