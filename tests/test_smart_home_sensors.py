from camwatch.alexa_smart_home.sensors import Sensor, kind_of, sensors

TEMPLATES = {
    "desk_entered": "{subject} sat down.",
    "desk_lasted": "{subject} has been here {minutes} minutes.",
    "on_break_lasted": "Break over!",
}
NAMES = {"subject": "Sam"}


def test_one_sensor_per_message_kind():
    assert sensors(TEMPLATES)[2] == Sensor(
        "on_break_lasted", "camwatch-on-break-lasted", "Camera watch on break lasted"
    )
    assert len(sensors(TEMPLATES)) == 3


def test_text_is_matched_back_to_its_kind():
    assert kind_of("Sam sat down.", TEMPLATES, NAMES) == "desk_entered"
    assert kind_of("Sam has been here 50 minutes.", TEMPLATES, NAMES) == "desk_lasted"
    assert kind_of("Break over!", TEMPLATES, NAMES) == "on_break_lasted"


def test_text_from_no_template_has_no_kind():
    assert kind_of("Hello there", TEMPLATES, NAMES) is None
    assert kind_of("Tom sat down.", TEMPLATES, NAMES) is None
