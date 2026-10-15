"""Built-in part implementations. Importing this package registers them all.

Add a new implementation as its own module here and import it below.
"""

from camwatch.parts import (
    alexa_speaker,
    alexa_web_speaker,
    google_speaker,
    log_speaker,
    memory_event_log,
    memory_state_store,
    nest_camera,
    postgres_event_log,
    postgres_state_store,
    presence_off,
    standard_communications,
    video_file_camera,
    voice_monkey_speaker,
)
