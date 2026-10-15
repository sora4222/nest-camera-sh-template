import logging
import threading
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fake_clock import FakeClock

from camwatch.communications.switches import Switches
from camwatch.config import Config, ConfigError, QuietHours, load_config
from camwatch.domain import Event, Presence, Urgency
from camwatch.parts.standard_communications import (
    CommunicationOptions,
    RoutedSpeaker,
    StandardCommunications,
)
from camwatch.registry import COMMUNICATIONS, default_registry

START = datetime(2026, 6, 1, 20, 0, tzinfo=UTC)  # a Monday
NIGHTS = QuietHours(
    days=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
    start=time(22),
    end=time(7),
    allow=[Urgency.URGENT],
)
MESSAGES = {
    "ball_entered": "{subject} is in.",
    "desk_entered": "{subject} sat down.",
    "desk_reminder": "Still at the desk.",
    "fire_entered": "{other} is on fire.",
}


class FakeSpeaker:
    def __init__(self, name: str, fails: bool = False) -> None:
        self.name = name
        self.said: list[str] = []
        self.fails = fails

    def say(self, text: str) -> None:
        if self.fails:
            raise ConnectionError("speaker unplugged")
        self.said.append(text)


class HangingSpeaker:
    """A speaker that does not answer (a Google speaker that is off) until `answer` is set."""

    def __init__(self) -> None:
        self.name = "Hanging"
        self.answer = threading.Event()

    def say(self, text: str) -> None:
        self.answer.wait(5)


class FakePresence:
    def __init__(self, presence: Presence = Presence.UNKNOWN) -> None:
        self.presence = presence

    def check(self, listener: str) -> Presence:
        return self.presence


class Setup:
    """A handler with one Speaker for every Urgency, at the fake clock's time."""

    def __init__(self, tmp_path, quiet=(), presence=None, speakers=None, **options) -> None:
        self.clock = FakeClock(START)
        self.speaker = FakeSpeaker("Living room")
        self.switches = Switches(tmp_path / "switches.json")
        self.presence = presence or FakePresence()
        self.handler = StandardCommunications(
            speakers=speakers or [RoutedSpeaker(self.speaker, frozenset(Urgency))],
            presence=self.presence,
            listeners=["Partner"],
            quiet_hours=list(quiet),
            zone=ZoneInfo("UTC"),
            messages=MESSAGES,
            names={"subject": "Sam", "other": "The toaster"},
            switches=self.switches,
            options=CommunicationOptions(**options),
        )

    def event(self, kind, urgency=Urgency.NORMAL, announce=True, **details) -> None:
        self.handler.handle(Event(kind, urgency, self.clock.now(), details, announce))
        assert self.handler.wait_until_said(5)


def test_an_event_is_said_on_every_speaker_from_its_message_template(tmp_path):
    first, second = FakeSpeaker("Living room"), FakeSpeaker("Kitchen")
    setup = Setup(
        tmp_path,
        speakers=[
            RoutedSpeaker(first, frozenset(Urgency)),
            RoutedSpeaker(second, frozenset(Urgency)),
        ],
    )
    setup.event("desk_entered")
    assert first.said == second.said == ["Sam sat down."]


def test_urgency_is_logged_but_never_spoken(tmp_path, caplog):
    setup = Setup(tmp_path)
    with caplog.at_level(logging.INFO):
        setup.event("fire_entered", Urgency.URGENT)
    assert setup.speaker.said == ["The toaster is on fire."]
    assert "urgent" in caplog.text


def test_log_only_events_are_logged_and_not_said(tmp_path, caplog):
    setup = Setup(tmp_path)
    with caplog.at_level(logging.INFO):
        setup.event("ball_left", Urgency.INFO, announce=False)
        setup.event("ball_entered", Urgency.INFO, announce=False)
    assert setup.speaker.said == []
    assert "ball_left" in caplog.text


def test_an_event_with_no_message_template_is_not_said(tmp_path):
    setup = Setup(tmp_path)
    setup.event("camera_offline")
    assert setup.speaker.said == []


def test_speakers_only_say_the_urgencies_they_are_for(tmp_path):
    bedroom = FakeSpeaker("Bedroom")
    hall = FakeSpeaker("Hall")
    setup = Setup(
        tmp_path,
        speakers=[
            RoutedSpeaker(bedroom, frozenset({Urgency.URGENT})),
            RoutedSpeaker(hall, frozenset(Urgency)),
        ],
    )
    setup.event("desk_entered")
    setup.event("fire_entered", Urgency.URGENT)
    assert bedroom.said == ["The toaster is on fire."]
    assert hall.said == ["Sam sat down.", "The toaster is on fire."]


def test_a_broken_speaker_does_not_stop_the_others(tmp_path, caplog):
    broken, working = FakeSpeaker("Broken", fails=True), FakeSpeaker("Working")
    setup = Setup(
        tmp_path,
        speakers=[
            RoutedSpeaker(broken, frozenset(Urgency)),
            RoutedSpeaker(working, frozenset(Urgency)),
        ],
    )
    setup.event("desk_entered")
    assert working.said == ["Sam sat down."]
    assert "Broken" in caplog.text


def test_quiet_hours_hold_back_urgencies_they_do_not_allow(tmp_path):
    setup = Setup(tmp_path, quiet=[NIGHTS])
    setup.clock.advance(3 * 3600)  # 23:00
    setup.event("desk_entered")
    setup.event("fire_entered", Urgency.URGENT)
    assert setup.speaker.said == ["The toaster is on fire."]


def test_do_not_disturb_holds_back_all_but_the_configured_urgencies(tmp_path):
    setup = Setup(tmp_path)
    setup.switches.set_do_not_disturb(START + timedelta(hours=2))
    setup.event("desk_entered")
    setup.event("fire_entered", Urgency.URGENT)
    assert setup.speaker.said == ["The toaster is on fire."]
    setup.clock.advance(2 * 3600)
    setup.event("desk_reminder")
    assert setup.speaker.said[-1] == "Still at the desk."


def test_do_not_disturb_can_hold_back_everything(tmp_path):
    setup = Setup(tmp_path)
    setup.switches.set_do_not_disturb(START + timedelta(hours=2), allow=[])
    setup.event("fire_entered", Urgency.URGENT)
    assert setup.speaker.said == []


def test_default_dnd_allow_comes_from_the_options(tmp_path):
    setup = Setup(tmp_path, dnd_allow=[Urgency.NORMAL, Urgency.URGENT])
    setup.switches.set_do_not_disturb(START + timedelta(hours=2))
    setup.event("desk_entered")
    setup.event("ball_entered", Urgency.INFO)
    assert setup.speaker.said == ["Sam sat down."]


def test_nothing_is_said_while_every_listener_is_away(tmp_path):
    setup = Setup(tmp_path, presence=FakePresence(Presence.AWAY))
    setup.event("fire_entered", Urgency.URGENT)
    assert setup.speaker.said == []
    setup.presence.presence = Presence.UNKNOWN  # the check is off or broken: still said
    setup.event("desk_entered")
    assert setup.speaker.said == ["Sam sat down."]


def test_the_same_text_is_not_said_again_within_repeat_seconds(tmp_path):
    setup = Setup(tmp_path, repeat_seconds=30)
    setup.event("desk_entered")
    setup.clock.advance(29)
    setup.event("desk_entered")
    setup.clock.advance(1)
    setup.event("desk_entered")
    assert setup.speaker.said == ["Sam sat down.", "Sam sat down."]


def test_standard_communications_are_built_from_the_example_config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    config = load_config(Path(__file__).parents[1] / "config.example.toml")
    handler = default_registry().create(
        COMMUNICATIONS, config.parts.communications, config, config.communications
    )
    assert isinstance(handler, StandardCommunications)


def test_wrong_options_and_speaker_urgencies_are_config_errors(tmp_path):
    def config(speaker: dict) -> Config:
        return Config.model_validate(
            {
                "app": {"start_state": "no_one_at_desk"},
                "paths": {"private_data": str(tmp_path)},
                "speakers": [{"name": "Hall", "kind": "log", **speaker}],
            }
        )

    registry = default_registry()
    with pytest.raises(ConfigError, match="repeat_secs"):
        registry.create(COMMUNICATIONS, "standard", config({}), {"repeat_secs": 1})
    with pytest.raises(ConfigError, match="loud"):
        registry.create(COMMUNICATIONS, "standard", config({"urgencies": ["loud"]}), {})
    built = registry.create(COMMUNICATIONS, "standard", config({"urgencies": ["urgent"]}), {})
    assert isinstance(built, StandardCommunications)


def test_a_hanging_speaker_holds_up_neither_the_caller_nor_the_others(tmp_path):
    hanging, working = HangingSpeaker(), FakeSpeaker("Working")
    setup = Setup(
        tmp_path,
        speakers=[
            RoutedSpeaker(hanging, frozenset(Urgency)),
            RoutedSpeaker(working, frozenset(Urgency)),
        ],
    )
    setup.handler.handle(Event("desk_entered", Urgency.NORMAL, setup.clock.now()))
    assert not setup.handler.wait_until_said(0.1)
    assert working.said == ["Sam sat down."]
    hanging.answer.set()
    assert setup.handler.wait_until_said(5)


def test_text_no_speaker_could_say_is_not_held_back_as_said(tmp_path, caplog):
    setup = Setup(tmp_path, repeat_seconds=30)
    setup.speaker.fails = True
    with caplog.at_level(logging.INFO):
        setup.event("desk_entered")
    assert "no Speaker said it" in caplog.text
    setup.speaker.fails = False
    setup.clock.advance(5)
    setup.event("desk_entered")
    assert setup.speaker.said == ["Sam sat down."]
