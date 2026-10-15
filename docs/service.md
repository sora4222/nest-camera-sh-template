# Running as a service

On a Linux server, the watcher runs as a systemd **user** service from this checkout.

```sh
make install RUNTIME=cpu EXTRAS=google   # the same RUNTIME and EXTRAS as make setup
sudo loginctl enable-linger $USER        # once: start at boot, keep running after logout
```

`make uninstall` removes it. `uv run camwatch service show` prints the unit without installing it.

## Secrets

- **With `op` (1Password CLI)**: the service runs `op run --env-file=.env`. Make a 1Password service account that can read only this app's items. Put `OP_SERVICE_ACCOUNT_TOKEN=...` in `~/.config/camwatch/service.env` (`chmod 600`).
- **Without `op`**: `.env` holds plain values; keep it `chmod 600`.

## Logs and restarts

```sh
journalctl --user -u camwatch -f
systemctl --user restart camwatch    # after changing config.toml or .env
```

Only one watcher runs per user, so stop the service before `make dev`. After `git pull`, run `make setup` if dependencies changed, then restart.
