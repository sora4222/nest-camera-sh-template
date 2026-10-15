from datetime import UTC, datetime, timedelta

import pytest

from camwatch.config import Config, ConfigError
from camwatch.database import engine, upgrade
from camwatch.interfaces import SavedState
from camwatch.parts.postgres_event_log import URL_ENV
from camwatch.parts.postgres_state_store import PostgresStateStore
from camwatch.registry import STATE_STORE, default_registry

AT = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)


def test_nothing_is_saved_at_first(database_url):
    upgrade(database_url)
    assert PostgresStateStore(engine(database_url)).last() is None


def test_the_newest_state_comes_back_after_a_restart(database_url):
    upgrade(database_url)
    store = PostgresStateStore(engine(database_url))
    store.save(SavedState("no_one_at_desk", '{"seen":0}', AT))
    store.save(SavedState("person_at_desk", '{"missing":2}', AT + timedelta(minutes=1)))
    again = PostgresStateStore(engine(database_url))
    assert again.last() == SavedState("person_at_desk", '{"missing":2}', AT + timedelta(minutes=1))


def test_it_is_built_from_config_and_applies_the_migrations(database_url, monkeypatch):
    monkeypatch.setenv(URL_ENV, database_url)
    config = Config.model_validate({"app": {"start_state": "no_one_at_desk"}})
    store = default_registry().create(STATE_STORE, "postgres", config, {})
    assert store.last() is None
    with pytest.raises(ConfigError, match="no options"):
        default_registry().create(STATE_STORE, "postgres", config, {"table": "x"})
