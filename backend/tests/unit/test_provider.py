"""Tests for SearchProvider abstract interface."""

from abc import ABC

import pytest

from research_tool.services.search.provider import SearchProvider


class TestSearchProviderInterface:
    """Test suite for SearchProvider ABC."""

    def test_search_provider_is_abstract(self) -> None:
        """SearchProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SearchProvider()  # type: ignore

    def test_search_provider_inherits_from_abc(self) -> None:
        """SearchProvider inherits from ABC."""
        assert issubclass(SearchProvider, ABC)

    def test_name_is_abstract_property(self) -> None:
        """name is declared as abstract property."""
        assert hasattr(SearchProvider, "name")
        assert isinstance(
            SearchProvider.name, property
        )

    def test_requests_per_second_is_abstract_property(self) -> None:
        """requests_per_second is declared as abstract property."""
        assert hasattr(SearchProvider, "requests_per_second")
        assert isinstance(
            SearchProvider.requests_per_second, property
        )

    def test_search_is_abstract_method(self) -> None:
        """search is declared as abstract method."""
        assert hasattr(SearchProvider, "search")
        assert callable(SearchProvider.search)

    def test_is_available_is_abstract_method(self) -> None:
        """is_available is declared as abstract method."""
        assert hasattr(SearchProvider, "is_available")
        assert callable(SearchProvider.is_available)


class MockSearchProvider(SearchProvider):
    """Mock implementation for testing."""

    @property
    def name(self) -> str:
        return "mock_provider"

    @property
    def requests_per_second(self) -> float:
        return 10.0

    async def search(
        self,
        query: str,
        max_results: int = 10,
        filters: dict | None = None
    ) -> list[dict]:
        return [
            {
                "url": "https://example.com",
                "title": "Test Result",
                "snippet": f"Results for: {query}",
                "source_name": self.name,
                "full_content": None,
                "metadata": {}
            }
        ]

    async def is_available(self) -> bool:
        return True


class TestMockSearchProvider:
    """Test mock implementation to verify interface works."""

    def test_mock_provider_can_be_instantiated(self) -> None:
        """Mock provider implementing all methods can be created."""
        provider = MockSearchProvider()
        assert provider is not None

    def test_name_returns_string(self) -> None:
        """name property returns string."""
        provider = MockSearchProvider()
        assert provider.name == "mock_provider"
        assert isinstance(provider.name, str)

    def test_requests_per_second_returns_float(self) -> None:
        """requests_per_second property returns float."""
        provider = MockSearchProvider()
        assert provider.requests_per_second == 10.0
        assert isinstance(provider.requests_per_second, float)

    @pytest.mark.asyncio
    async def test_search_returns_list(self) -> None:
        """search method returns list of dicts."""
        provider = MockSearchProvider()
        results = await provider.search("test query")
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["source_name"] == "mock_provider"

    @pytest.mark.asyncio
    async def test_search_with_max_results(self) -> None:
        """search accepts max_results parameter."""
        provider = MockSearchProvider()
        results = await provider.search("test", max_results=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_filters(self) -> None:
        """search accepts filters parameter."""
        provider = MockSearchProvider()
        results = await provider.search(
            "test",
            filters={"category": "science"}
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_is_available_returns_bool(self) -> None:
        """is_available returns boolean."""
        provider = MockSearchProvider()
        available = await provider.is_available()
        assert available is True
        assert isinstance(available, bool)
