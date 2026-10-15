import json
import threading

import httpx

from camwatch.labeling.clip_labels import ClipLabels
from camwatch.labeling.labeling_app import LabelingApp
from camwatch.labeling.labeling_server import make_server


def test_serves_the_app_on_localhost(tmp_path):
    app = LabelingApp(ClipLabels(tmp_path / "clips", tmp_path / "x.csv"), ["a", "b"], "model_x")
    server = make_server(app, port=0)
    host, port = server.server_address[:2]
    assert host == "127.0.0.1"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False) as client:
            answer = json.loads(client.get("/api/next").content)
            assert answer == {
                "clip": None,
                "remaining": 0,
                "labels": ["a", "b"],
                "model": "model_x",
            }
            assert client.post("/api/label", content=b"{}").status_code == 400
            assert client.get("/").headers["content-type"].startswith("text/html")
    finally:
        server.shutdown()
        server.server_close()
