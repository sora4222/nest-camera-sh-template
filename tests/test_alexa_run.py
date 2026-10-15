import json
from dataclasses import dataclass
from datetime import datetime

import httpx
import pytest
from cryptography.x509.verification import Store
from fake_amazon_certs import NOW, make_fake_amazon
from fake_clock import FakeClock
from fastapi.testclient import TestClient

from camwatch.alexa_skill.run import SKILL_ID_ENV, alexa_app
from camwatch.alexa_smart_home.grants import Grants
from camwatch.communications.switches import Switches
from camwatch.config import Config, ConfigError
from camwatch.parts.memory_event_log import MemoryEventLog
from camwatch.state_requests import StateRequests

SKILL_ID = "amzn1.ask.skill.test"


@dataclass
class Status:
    state_name: str = "no_one_at_desk"
    since: datetime = NOW
    subject_action: str | None = None


def app_for(config_: Config, env: dict, **more):
    return alexa_app(
        config_,
        MemoryEventLog(),
        FakeClock(NOW),
        env,
        status=Status(),
        requests=StateRequests(),
        **more,
    )


CERT_URL = "https://s3.amazonaws.com/echo.api/echo-api-cert.pem"


def config(enabled: bool = True) -> Config:
    return Config.model_validate(
        {
            "app": {"start_state": "no_one_at_desk"},
            "alexa_skill": {"enabled": enabled, "port": 0},
        }
    )


class Certificates:
    def __init__(self, chain: bytes) -> None:
        self.chain = chain

    def fetch(self, url: str) -> bytes:
        return self.chain


def status_request() -> bytes:
    return json.dumps(
        {
            "version": "1.0",
            "context": {"System": {"application": {"applicationId": SKILL_ID}}},
            "request": {
                "type": "IntentRequest",
                "timestamp": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "intent": {"name": "StatusIntent", "slots": {}},
            },
        }
    ).encode()


def test_when_off_there_is_no_app():
    assert app_for(config(enabled=False), {}) is None


def test_when_on_it_needs_the_skill_id():
    with pytest.raises(ConfigError, match=SKILL_ID_ENV):
        app_for(config(), {})


def test_a_signed_status_request_is_answered_end_to_end(tmp_path):
    amazon = make_fake_amazon()
    body = status_request()
    app = app_for(
        config(),
        {SKILL_ID_ENV: SKILL_ID},
        certificates=Certificates(amazon.chain),
        trusted=Store([amazon.root]),
        switches=Switches(tmp_path / "switches.json"),
    )
    assert app is not None
    client = TestClient(app)
    headers = {"SignatureCertChainUrl": CERT_URL, "Signature-256": amazon.sign(body)}
    answer = client.post("/alexa", content=body, headers=headers)
    forged = client.post("/alexa", content=body.replace(b"Status", b"Statux"), headers=headers)
    other = client.get("/")
    docs = client.get("/docs")
    assert answer.status_code == 200
    assert answer.json()["response"]["outputSpeech"]["text"].startswith("No one at desk since")
    assert forged.status_code == 400
    assert other.status_code == 404
    assert docs.status_code == 404


def test_smart_home_needs_its_secret():
    on = config().model_copy(
        update={"alexa_skill": config().alexa_skill.model_copy(update={"smart_home": True})}
    )
    with pytest.raises(ConfigError, match="CAMWATCH_ALEXA_SMART_HOME_SECRET"):
        app_for(on, {SKILL_ID_ENV: "x"})


def test_smart_home_is_served_next_to_the_skill(tmp_path):
    on = config().model_copy(
        update={
            "alexa_skill": config().alexa_skill.model_copy(update={"smart_home": True}),
            "messages": {"on_break_lasted": "Break over."},
        }
    )
    env = {SKILL_ID_ENV: "x", "CAMWATCH_ALEXA_SMART_HOME_SECRET": "s3cret"}
    grants = Grants("id", "secret", tmp_path / "grant.json", FakeClock(NOW), httpx.Client())
    discover = {"directive": {"header": {"namespace": "Alexa.Discovery", "name": "Discover"}}}
    app = app_for(on, env, grants=grants)
    assert app is not None
    answer = TestClient(app).post(
        "/alexa/smart-home", json=discover, headers={"Authorization": "Bearer s3cret"}
    )
    [sensor] = answer.json()["event"]["payload"]["endpoints"]
    assert sensor["friendlyName"] == "Camera watch on break lasted"
