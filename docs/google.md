# Google Home speakers

Speaker kind `google` makes speech on this machine with [Piper](https://github.com/rhasspy/piper), serves it on the home network, and casts it to a Google Home or Nest speaker.

1. `make setup EXTRAS=google` (needs `RUNTIME=cpu`). Use the same `EXTRAS` for `make dev` and `make install`.
2. Download a Piper voice (`.onnx` and `.onnx.json`) into the private data folder, such as `voices/en_US-lessac-medium.onnx`.
3. Add the speaker:

   ```toml
   [[speakers]]
   name = "Kitchen"
   kind = "google"
   device = "Kitchen speaker"   # its name in the Google Home app
   voice = "voices/en_US-lessac-medium.onnx"
   serve_port = 8766            # speakers fetch the speech from here
   # volume = 0.6
   # known_hosts = ["..."]      # speaker addresses, if finding them by name fails
   ```

4. Allow `serve_port` through this machine's firewall on the home network.

Each speaker says messages in its own thread, Urgent ones first, so a slow speaker never holds up the watcher. `urgencies = ["urgent"]` makes a speaker say only those.
