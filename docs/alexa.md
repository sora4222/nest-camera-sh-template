# Alexa

Two separate things: **voice commands** (a custom skill the watcher serves) and **Alexa speakers** (making an Echo say messages).

## Voice commands

Built-in commands, after "Alexa, ask camera watch ..." (`[alexa_skill] invocation`):

| Say | Does |
|---|---|
| "what's happening" | the State, since when, and the Subject Action |
| "I'm on a break" | moves to the State with that voice name |
| "do not disturb for two hours" / "stop do not disturb" | Do Not Disturb |
| "what happened last" | the example custom command |

**Let Alexa set a State:** add words to the State's `voice_names`. The watcher moves on its next check.

**Add your own command** in `src/camwatch/alexa_skill/custom_intents.py`:

```python
def is_it_busy(context: SkillContext, slots: Mapping[str, str]) -> Answer:
    busy = context.status.state_name == "person_at_desk"
    return say("Yes." if busy else "No.")


CUSTOM_INTENTS = (Intent("BusyIntent", is_it_busy, ("is anyone at the desk",)),)
```

A handler can read `context.status`, `context.event_log` and `context.switches`. To change the State, call `context.requests.ask("<state>")`. Slots go in braces in samples, with their types in `slots`.

After any change, run `make alexa-model` and paste `alexa/interactionModels/custom/en-US.json` into the console.

## Set up the skill

1. In the [Alexa developer console](https://developer.amazon.com/alexa/console/ask), **Create Skill**: model **Custom**, hosting **Provision your own**.
2. **JSON Editor**: paste the model file, then **Save** and **Build**.
3. Put the skill ID in `.env` as `CAMWATCH_ALEXA_SKILL_ID`, set `[alexa_skill] enabled = true` and restart the watcher.
4. Open only `/alexa` to the internet. `make alexa-tunnel` prints the setup for Cloudflare Tunnel or Tailscale Funnel. With Funnel, nothing else may be served on port 443.
5. In the console, set **Endpoint** to `https://<your host>/alexa` with "a certificate from a trusted certificate authority".
6. Test it in the console's **Test** tab. It works on your own Echos without publishing.

Every request is checked: Amazon's signature, its certificate, a timestamp within 150 seconds, and your skill ID. Anything else gets 400.

## Alexa speakers

Pick one in `[[speakers]]`:

- `voice_monkey`: the simplest. Set `CAMWATCH_VOICE_MONKEY_TOKEN`.
- `alexa_web`: Amazon's unofficial web API. Set `CAMWATCH_ALEXA_REFRESH_TOKEN`.
- `alexa`: a Smart Home skill with one virtual sensor per message, plus one Alexa routine per sensor that says it. It needs an AWS Lambda ([`alexa/smart_home_lambda.py`](../alexa/smart_home_lambda.py)), account linking and `[alexa_skill] smart_home = true`. Use it only if the others will not do.
