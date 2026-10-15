"""Integration: each example Alexa request goes over HTTP to the real app and database.

The app is built as the watcher builds it (`alexa_app`, `serve_in_background`) on a free
port, with its Events and States in PostgreSQL (`database_url`, often a Testcontainer with
a random port, user and password), the real example States and real Do Not Disturb
switches. Only Amazon and the clock are fakes.
"""

import logging
import socket
import time
from collections.abc import Generator
from datetime import timedelta
from pathlib import Path

import httpx
import psycopg
import pytest
from cryptography.x509.verification import Store
from fake_amazon_certs import NOW, make_fake_amazon
from fake_clock import FakeClock
from postgres_server import empty_schema

from camwatch.alexa_skill.run import SKILL_ID_ENV, alexa_app, serve_in_background
from camwatch.communications.switches import Switches
from camwatch.config import Config, StateSettings
from camwatch.database import engine
from camwatch.domain import Event, Urgency
from camwatch.model_runner import ModelRunner
from camwatch.parts.postgres_event_log import URL_ENV, PostgresEventLog
from camwatch.parts.postgres_state_store import PostgresStateStore
from camwatch.registry import EVENT_LOG, STATE_STORE, default_registry
from camwatch.state_machine import StateMachine
from camwatch.state_requests import StateRequests

REQUESTS = Path(__file__).parent / "alexa_requests"
SKILL_ID = "amzn1.ask.skill.00000000-0000-0000-0000-000000000000"
CERT_URL = "https://s3.amazonaws.com/echo.api/echo-api-cert.pem"
HELP = "You can ask"
ENTERED_AT = NOW - timedelta(hours=1)

EXPECTED = {  # request file -> (what Alexa says, or None for no speech; does the session end)
    "launch": ("Hello. You can ask", False),
    "status": ("No one at desk since 9 AM.", True),
    "do_not_disturb": ("OK, Do Not Disturb until 12 PM.", True),
    "do_not_disturb_ask": ("For how long?", False),
    "duration": ("OK, Do Not Disturb until 10:30 AM.", True),
    "stop_do_not_disturb": ("Do Not Disturb was not on.", True),
    "set_state": ("OK, on a break.", True),
    "last_event": ("Desk check at 9 AM.", True),
    "help": (HELP, False),
    "stop": ("Bye.", True),
    "cancel": ("Bye.", True),
    "fallback": (HELP, False),
    "navigate_home": (HELP, False),
    "session_ended": (None, None),
}


class Certificates:
    def __init__(self, chain: bytes) -> None:
        self.chain = chain

    def fetch(self, url: str) -> bytes:
        return self.chain


@pytest.fixture(scope="module")
def amazon():
    return make_fake_amazon()


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def config(port: int) -> Config:
    return Config.model_validate(
        {
            "app": {"start_state": "no_one_at_desk"},
            "parts": {"event_log": "postgres", "state_store": "postgres"},
            "alexa_skill": {"enabled": True, "port": port},
        }
    )


def wait_until_served(url: str) -> None:
    for _ in range(200):
        try:
            httpx.get(url, trust_env=False)
            return
        except httpx.ConnectError:
            time.sleep(0.025)
    raise TimeoutError(url)


class Server:
    """The served app, and what it keeps: the database, the switches file and the requests."""

    def __init__(self, url: str, database: str, switches: Path, requests: StateRequests) -> None:
        self.url, self.database, self.switches, self.requests = url, database, switches, requests

    def post(self, amazon, name: str) -> httpx.Response:
        body = (REQUESTS / f"{name}.json").read_bytes()
        headers = {"SignatureCertChainUrl": CERT_URL, "Signature-256": amazon.sign(body)}
        return httpx.post(self.url, content=body, headers=headers, trust_env=False)

    def said(self, amazon, name: str) -> str:
        return self.post(amazon, name).json()["response"]["outputSpeech"]["text"]


@pytest.fixture(scope="module")
def server(amazon, postgres_url, tmp_path_factory) -> Generator[Server]:
    """The Alexa skill app on a free port, its Event log made from config and the env."""
    for database in empty_schema(postgres_url):
        settings = config(free_port())
        with pytest.MonkeyPatch.context() as env:
            env.setenv(URL_ENV, database)
            event_log = default_registry().create(EVENT_LOG, "postgres", settings, {})
            store = default_registry().create(STATE_STORE, "postgres", settings, {})
        assert isinstance(event_log, PostgresEventLog)
        assert isinstance(store, PostgresStateStore)
        machine = StateMachine.resume(
            start_name="no_one_at_desk",
            now=ENTERED_AT,
            store=store,
            runner=ModelRunner({}),
            settings=lambda name: StateSettings(),
        )
        switches = tmp_path_factory.mktemp("switches") / "switches.json"
        requests = StateRequests()
        app = alexa_app(
            settings,
            event_log,
            FakeClock(NOW),
            {SKILL_ID_ENV: SKILL_ID},
            status=machine,
            requests=requests,
            certificates=Certificates(amazon.chain),
            trusted=Store([amazon.root]),
            switches=Switches(switches),
        )
        assert app is not None
        serve_in_background(app, settings.alexa_skill)
        url = f"http://127.0.0.1:{settings.alexa_skill.port}/alexa"
        wait_until_served(url)
        yield Server(url, database, switches, requests)


@pytest.fixture(autouse=True)
def fresh(server: Server) -> None:
    """Each test starts with one Event from an hour ago, every switch off and no requests."""
    with psycopg.connect(server.database, autocommit=True) as db:
        db.execute("TRUNCATE events")
    log = PostgresEventLog(engine(server.database))
    log.record(Event("desk_check", Urgency.NORMAL, ENTERED_AT))
    server.switches.unlink(missing_ok=True)
    server.requests.take()


@pytest.mark.parametrize("name", EXPECTED)
def test_each_command_gets_the_expected_answer(name, server, amazon, caplog):
    with caplog.at_level(logging.WARNING):
        response = server.post(amazon, name)
    assert response.status_code == 200
    assert caplog.records == []
    answer = response.json()
    assert answer["version"] == "1.0"
    said, ends = EXPECTED[name]
    if said is None:
        assert answer["response"] == {}
        return
    assert answer["response"]["outputSpeech"]["text"].startswith(said)
    assert answer["response"]["shouldEndSession"] is ends


def test_do_not_disturb_shows_in_the_status(server, amazon):
    server.post(amazon, "do_not_disturb")
    assert server.said(amazon, "status").endswith("Do Not Disturb is on until 12 PM.")
    assert server.said(amazon, "stop_do_not_disturb") == "OK, Do Not Disturb is off."
    assert "Do Not Disturb" not in server.said(amazon, "status")


def test_the_answer_to_how_long_turns_on_do_not_disturb(server, amazon):
    server.post(amazon, "do_not_disturb_ask")
    server.post(amazon, "duration")
    assert server.said(amazon, "status").endswith("Do Not Disturb is on until 10:30 AM.")


def test_a_state_asked_for_by_voice_waits_for_the_watcher(server, amazon):
    server.post(amazon, "set_state")
    assert server.requests.take() == ["on_break"]
    assert server.said(amazon, "status").startswith("No one at desk")
