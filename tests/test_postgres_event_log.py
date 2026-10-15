from datetime import UTC, datetime, timedelta

import pytest

from camwatch.config import Config, ConfigError
from camwatch.database import engine, upgrade
from camwatch.domain import Event, Urgency
from camwatch.parts.postgres_event_log import URL_ENV, PostgresEventLog
from camwatch.registry import EVENT_LOG, default_registry

AT = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)


@pytest.fixture
def url(database_url: str) -> str:
    """An empty schema with the migrations applied."""
    upgrade(database_url)
    return database_url


def events() -> list[Event]:
    return [
        Event("desk_entered", Urgency.NORMAL, AT, {"from": "away"}, state="desk"),
        Event(
            "ball_seen",
            Urgency.INFO,
            AT + timedelta(seconds=1),
            announce=False,
            state="desk",
            subject_action="typing",
            model_output={"model_x": {"found": [{"label": "person", "score": 0.9}]}},
        ),
        Event("fire_entered", Urgency.URGENT, AT + timedelta(seconds=2), state="fire"),
    ]


def config() -> Config:
    return Config.model_validate({"app": {"start_state": "no_one_at_desk"}})


def test_events_come_back_newest_first_with_state_subject_action_and_model_output(url):
    log = PostgresEventLog(engine(url))
    for event in events():
        log.record(event)
    assert log.recent(2) == events()[::-1][:2]


def test_events_are_kept_after_a_restart(url):
    first = PostgresEventLog(engine(url))
    for event in events():
        first.record(event)
    assert PostgresEventLog(engine(url)).recent(10) == events()[::-1]


def test_postgres_event_log_is_built_from_config_with_the_url_from_env(database_url, monkeypatch):
    monkeypatch.setenv(URL_ENV, database_url)
    log = default_registry().create(EVENT_LOG, "postgres", config(), {})
    log.record(events()[0])
    assert PostgresEventLog(engine(database_url)).recent(1) == [events()[0]]


def test_without_the_url_it_is_a_config_error(monkeypatch):
    monkeypatch.delenv(URL_ENV, raising=False)
    with pytest.raises(ConfigError, match=URL_ENV):
        default_registry().create(EVENT_LOG, "postgres", config(), {})


def test_event_log_options_are_a_config_error(monkeypatch):
    monkeypatch.setenv(URL_ENV, "postgresql://nowhere/x")
    with pytest.raises(ConfigError, match="no options"):
        default_registry().create(EVENT_LOG, "postgres", config(), {"path": "events.sqlite"})


def test_a_database_it_cannot_reach_is_a_config_error(monkeypatch):
    monkeypatch.setenv(URL_ENV, "postgresql://camwatch@127.0.0.1:1/camwatch?connect_timeout=2")
    with pytest.raises(ConfigError, match="cannot connect"):
        default_registry().create(EVENT_LOG, "postgres", config(), {})
