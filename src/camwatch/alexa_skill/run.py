"""Build the Alexa skill app and run it with uvicorn on a background thread.

It shares the watcher's event log and State machine (for the status), the State requests
(to move to a State) and the switches file (for Do Not Disturb). Off unless
`[alexa_skill] enabled = true`.
"""

import logging
import threading
from collections.abc import Mapping

import uvicorn
from cryptography.x509.verification import Store
from fastapi import FastAPI

from camwatch.alexa_skill.certificates import HttpCertificates
from camwatch.alexa_skill.endpoint import PATH, router
from camwatch.alexa_skill.request_verifier import RequestVerifier
from camwatch.alexa_skill.skill import AlexaSkill
from camwatch.alexa_skill.skill_context import AppStatus, SkillContext
from camwatch.alexa_smart_home.directives import SmartHome
from camwatch.alexa_smart_home.endpoint import router as smart_home_router
from camwatch.alexa_smart_home.grants import Grants
from camwatch.alexa_smart_home.sensors import sensors
from camwatch.clock import Clock
from camwatch.communications.switches import Switches
from camwatch.config import AlexaSkillSettings, Config, ConfigError
from camwatch.interfaces import CertificateSource, EventLog
from camwatch.state_registry import all_states
from camwatch.state_requests import StateRequests

SKILL_ID_ENV = "CAMWATCH_ALEXA_SKILL_ID"
SMART_HOME_SECRET_ENV = "CAMWATCH_ALEXA_SMART_HOME_SECRET"
log = logging.getLogger(__name__)


def alexa_app(
    config: Config,
    event_log: EventLog,
    clock: Clock,
    environ: Mapping[str, str],
    *,
    status: AppStatus,
    requests: StateRequests,
    grants: Grants | None = None,
    certificates: CertificateSource | None = None,
    trusted: Store | None = None,
    switches: Switches | None = None,
) -> FastAPI | None:
    """The skill's FastAPI app, or None when `[alexa_skill]` is off."""
    if not config.alexa_skill.enabled:
        return None
    skill_id = environ.get(SKILL_ID_ENV, "").strip()
    if not skill_id:
        raise ConfigError(f"[alexa_skill] is enabled but {SKILL_ID_ENV} is not set (in .env)")
    verifier = RequestVerifier(skill_id, certificates or HttpCertificates(), clock, trusted)
    skill = AlexaSkill(
        SkillContext(
            clock=clock,
            zone=config.zone,
            switches=switches or Switches.default(),
            requests=requests,
            event_log=event_log,
            status=status,
            voice_states=voice_states(),
        )
    )
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.verifier, app.state.skill = verifier, skill
    app.include_router(router)
    if config.alexa_skill.smart_home:
        secret = environ.get(SMART_HOME_SECRET_ENV, "").strip()
        if not secret:
            raise ConfigError(
                f"[alexa_skill] smart_home is on but {SMART_HOME_SECRET_ENV} is not set"
            )
        grants = grants or Grants.from_env(environ, clock)
        app.state.smart_home_secret = secret
        app.state.smart_home = SmartHome(sensors(config.messages), grants, clock)
        app.include_router(smart_home_router)
    return app


def serve_in_background(app: FastAPI, settings: AlexaSkillSettings) -> None:
    """Run `app` with uvicorn on a daemon thread; it ends with the watcher's process."""
    where = {"host": settings.host, "port": settings.port}
    threading.Thread(
        target=uvicorn.run, args=(app,), kwargs=where | {"log_config": None}, daemon=True
    ).start()
    url = f"http://{settings.host}:{settings.port}{PATH}"
    log.info("Alexa skill endpoint at %s (tunnel: %s)", url, settings.tunnel)


def voice_states() -> dict[str, str]:
    """What people may say -> State name, from every State's `voice_names`."""
    return {
        spoken.lower(): name for name, cls in all_states().items() for spoken in cls.voice_names
    }
