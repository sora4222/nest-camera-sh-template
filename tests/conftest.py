"""Shared fixtures: one PostgreSQL server per test run, and an empty schema per test."""

from collections.abc import Generator

import pytest
from fake_states import TEST_STATES
from postgres_server import empty_schema, postgres_server

import camwatch.state_registry as registry


@pytest.fixture(scope="session")
def postgres_url() -> Generator[str]:
    """A PostgreSQL server for the whole run (see `postgres_server`)."""
    yield from postgres_server()


@pytest.fixture
def database_url(postgres_url: str) -> Generator[str]:
    """A new, empty schema on that server, dropped after the test."""
    yield from empty_schema(postgres_url)


@pytest.fixture
def test_states(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register the test-only States in `fake_states` for one test, and only them."""
    registry.all_states()  # import the app's States first, then hide them
    monkeypatch.setattr(registry, "_STATES", dict(TEST_STATES))
