# Camera

`[parts] camera` picks where Frames come from.

## Video file (the default)

Plays a saved clip as if it were the camera: good for trying States without a camera.

```toml
[camera]
file = "clips/example.mp4"   # inside the private data folder
every_seconds = 0.5
loop = true
```

## Nest camera

Uses [googlenestcam](https://github.com/sora4222/nest-camera-access-python).

1. Follow its login guide once. Put `GOOGLENESTCAM_*` in `.env`, and keep the Token file outside the repo.
2. Set `[parts] camera = "nest"`:

   ```toml
   [camera]
   device = "Office"   # its name in the Google Home app
   size = 720
   ```

No picture for `[watcher] camera_offline_minutes` makes a `camera_offline` Event. A refused login makes `login_expired`. Give them `[messages]` templates to hear them.
