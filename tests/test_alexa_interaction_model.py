"""The interaction model in the repo matches what the skill code answers.

If a test here fails after you changed an intent or a State's `voice_names`, run
`make alexa-model` and paste the new file into the Alexa developer console.
"""

import json
import re
from pathlib import Path

from camwatch.alexa_skill.interaction_model import interaction_model
from camwatch.alexa_skill.run import voice_states
from camwatch.alexa_skill.skill import all_intents
from camwatch.config import load_config

REPO = Path(__file__).parents[1]
MODEL = REPO / "alexa" / "interactionModels" / "custom" / "en-US.json"


def language_model(model: dict) -> dict:
    return model["interactionModel"]["languageModel"]


def made() -> dict:
    invocation = load_config(REPO / "config.example.toml").alexa_skill.invocation
    return interaction_model(invocation, all_intents().values(), voice_states())


def test_the_file_in_the_repo_is_up_to_date():
    assert json.loads(MODEL.read_text()) == made()


def test_every_intent_has_a_handler_and_the_required_built_ins_are_there():
    names = {intent["name"] for intent in language_model(made())["intents"]}
    assert set(all_intents()) <= names
    assert {"AMAZON.HelpIntent", "AMAZON.StopIntent", "AMAZON.CancelIntent"} <= names


def test_invocation_name_is_lower_case_words():
    assert re.fullmatch(r"[a-z]+( [a-z]+)+", language_model(made())["invocationName"])


def test_samples_are_unique_and_use_only_declared_slots():
    seen: set[str] = set()
    for intent in language_model(made())["intents"]:
        slots = {slot["name"] for slot in intent.get("slots", [])}
        for sample in intent["samples"]:
            assert sample not in seen, sample
            seen.add(sample)
            assert re.fullmatch(r"[a-z' {}]+", sample), sample
            assert set(re.findall(r"{(\w+)}", sample)) <= slots, sample


def test_a_slot_only_sample_is_alone_in_its_intent():
    for intent in language_model(made())["intents"]:
        if any(re.fullmatch(r"{\w+}", sample) for sample in intent["samples"]):
            assert len(intent["samples"]) == 1, intent["name"]


def test_state_voice_names_are_the_values_of_the_state_slot():
    [state_type] = language_model(made())["types"]
    values = {value["name"]["value"] for value in state_type["values"]}
    assert values == set(voice_states())
    assert "on a break" in values
