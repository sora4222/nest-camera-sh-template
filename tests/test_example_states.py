"""The example States. TODO(template): replace these tests with tests of your own States."""

from datetime import UTC, datetime

import numpy as np

from camwatch.domain import Frame
from camwatch.model_output import ModelOutput
from camwatch.models.model_x.model_x_schema import Found, ModelXOutput
from camwatch.state_registry import all_states
from camwatch.states.no_one_at_desk import SEEN_FRAMES, NoOneAtDesk
from camwatch.states.on_break import OnBreak
from camwatch.states.person_at_desk import GONE_FRAMES, PersonAtDesk

AT = datetime(2026, 1, 1, tzinfo=UTC)
PERSON = Found(label="person", score=0.9, box=(0.1, 0.1, 0.5, 0.9))


def output(*found: Found) -> ModelOutput:
    out = ModelOutput(Frame(AT, np.zeros((2, 2, 3), np.uint8)))
    out.add("model_x", ModelXOutput(found=list(found)))
    return out


def test_the_example_states_are_registered():
    assert {"no_one_at_desk", "person_at_desk", "on_break"} <= set(all_states())


def test_a_person_must_stay_in_view_before_they_are_at_the_desk():
    state = NoOneAtDesk()
    for _ in range(SEEN_FRAMES - 1):
        assert state.next(output(PERSON)).state is state
    assert state.next(output()).state is state  # gone again: start counting over
    for _ in range(SEEN_FRAMES - 1):
        state.next(output(PERSON))
    moved = state.next(output(PERSON))
    assert isinstance(moved.state, PersonAtDesk)
    assert moved.subject_action == "sitting down"


def test_a_frame_model_x_skipped_changes_nothing():
    state = NoOneAtDesk(seen=2)
    empty = ModelOutput(Frame(AT, np.zeros((2, 2, 3), np.uint8)))
    assert state.next(empty).state is state
    assert state.seen == 2


def test_the_person_leaves_after_enough_frames_without_them():
    state = PersonAtDesk()
    for _ in range(GONE_FRAMES - 1):
        assert state.next(output()).subject_action == "at the desk"
    assert isinstance(state.next(output()).state, NoOneAtDesk)


def test_a_break_is_only_left_by_voice():
    state = OnBreak()
    assert state.next(output(PERSON)).state is state
    assert "on a break" in OnBreak.voice_names
    assert OnBreak.models == {}
