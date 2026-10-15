from datetime import UTC, datetime, timedelta

import pytest
from fake_states import Dark, FakeModel, Light, frame

from camwatch.config import ConfigError, StateSettings
from camwatch.domain import Urgency
from camwatch.interfaces import SavedState
from camwatch.model_runner import ModelRunner
from camwatch.parts.memory_state_store import MemoryStateStore
from camwatch.state_machine import StateMachine

START = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
SETTINGS = {"light": StateSettings(urgency=Urgency.URGENT, lasted_minutes=1)}

pytestmark = pytest.mark.usefixtures("test_states")


def machine(store: MemoryStateStore | None = None) -> tuple[StateMachine, FakeModel]:
    model = FakeModel()
    made = StateMachine.resume(
        start_name="dark",
        now=START,
        store=store or MemoryStateStore(),
        runner=ModelRunner({"bright": model}),
        settings=lambda name: SETTINGS.get(name, StateSettings()),
    )
    return made, model


def test_starts_in_the_start_state_and_saves_it():
    store = MemoryStateStore()
    m, _ = machine(store)
    assert m.state_name == "dark"
    assert store.last() == SavedState("dark", "{}", START)


def test_moving_makes_left_and_entered_events_with_the_model_output():
    store = MemoryStateStore()
    m, _ = machine(store)
    left, entered = m.see(frame(START, 200))
    assert (left.kind, left.state, left.urgency) == ("dark_left", "dark", Urgency.NORMAL)
    assert (entered.kind, entered.state, entered.urgency) == (
        "light_entered",
        "light",
        Urgency.URGENT,
    )
    assert entered.details == {"from": "dark", "to": "light"}
    assert entered.subject_action == "lights on"
    assert entered.model_output == {"bright": {"value": pytest.approx(200 / 255)}}
    assert m.state_name == "light" and m.since == START
    assert store.last() == SavedState("light", '{"dark_frames":0}', START)


def test_the_state_picks_which_models_run_and_how_often():
    m, model = machine()
    m.see(frame(START, 200))  # dark runs it on every Frame
    for _ in range(4):
        m.see(frame(START, 200))  # light, on every second Frame
    assert model.runs == 3


def test_a_states_own_events_get_the_state_and_subject_action():
    m, _ = machine()
    m.see(frame(START, 200))  # frame 1: into light
    [flicker] = m.see(frame(START, 250))  # frame 2: light runs the Model
    assert (flicker.kind, flicker.state, flicker.subject_action) == ("flicker", "light", "reading")


def test_a_state_remembers_its_fields_between_frames():
    m, _ = machine()
    m.see(frame(START, 200))
    events = [e.kind for n in range(8) for e in m.see(frame(START, 0))]
    assert events == ["light_left", "dark_entered"]
    assert m.subject_action == "lights off"


def test_time_in_a_state_makes_lasted_events():
    m, _ = machine()
    m.see(frame(START, 200))
    assert m.tick(START + timedelta(seconds=59)) == []
    [lasted] = m.tick(START + timedelta(minutes=1))
    assert (lasted.kind, lasted.state) == ("light_lasted", "light")


def test_a_person_can_ask_for_a_state_by_name():
    m, _ = machine()
    kinds = [e.kind for e in m.ask("light", START)]
    assert kinds == ["dark_left", "light_entered"]
    assert m.ask("light", START) == []
    with pytest.raises(ConfigError, match="nowhere"):
        m.ask("nowhere", START)


def test_after_a_restart_it_goes_back_to_the_saved_state_and_its_fields():
    store = MemoryStateStore()
    store.save(SavedState("light", '{"dark_frames": 1}', START - timedelta(hours=1)))
    m, _ = machine(store)
    assert isinstance(m.state, Light) and m.state.dark_frames == 1
    assert m.since == START - timedelta(hours=1)


@pytest.mark.parametrize(
    "saved", [SavedState("gone", "{}", START), SavedState("light", "{x", START)]
)
def test_a_saved_state_it_cannot_go_back_to_is_replaced_by_the_start_state(saved, caplog):
    store = MemoryStateStore()
    store.save(saved)
    m, _ = machine(store)
    assert isinstance(m.state, Dark)
    assert "cannot go back" in caplog.text
