# Roadmap

Kaleido's only goal is to faithfully reproduce Plotly images as static files.

There are currently no goals to support more filetypes, and any non-support is
considered a bug.

Any significant development would likely occur on the browser-renderer layer:
[choreographer](https://www.github.com/plotly/choreographer).

- [ ] To improve performance:

```python
await tab.send_command(
        "Emulation.setIdleOverride",
        params={"isUserActive": True, "isScreenUnlocked": True},
    )
```

- [ ] `start_sync_server`: use `os.register_at_fork` to invalidate server, or
      to switch to using multiprocesses inter-process communication.
