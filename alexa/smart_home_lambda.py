"""AWS Lambda for the Smart Home skill: forward each directive to the watcher.

Amazon only sends Smart Home directives to Lambda. Set CAMWATCH_URL (for example
https://watch.example.com/alexa/smart-home) and CAMWATCH_SECRET (the same as
CAMWATCH_ALEXA_SMART_HOME_SECRET) on the function. Python 3.12, standard library only.
"""

import json
import os
import urllib.request


def lambda_handler(event, context):
    """The watcher's answer to `event`."""
    request = urllib.request.Request(
        os.environ["CAMWATCH_URL"],
        data=json.dumps(event).encode(),
        headers={
            "Authorization": f"Bearer {os.environ['CAMWATCH_SECRET']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=7) as response:
        return json.loads(response.read())
