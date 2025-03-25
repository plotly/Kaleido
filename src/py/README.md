
<div align="center">
  <a href="https://dash.plotly.com/project-maintenance">
    <img src="https://dash.plotly.com/assets/images/maintained-by-plotly.png"
    width="400px" alt="Maintained by Plotly">
  </a>
</div>

# Pre-Launch Kaleido v1.0.0

**NOTE: New api versions of Kaleido v1.0.0rc1+ are only available through github.**
This will change once [plotly.py](https://www.github.com/plotly/plotly.py)
finishes its integration with the new api.

```bash
$ pip install git+https://github.com/plotly/kaleido@latest-tag#subdirectory=src/py

# also works with `uv add` and `uv run --with PACKAGE`
```

# Kaleido

Kaleido allows you to convert plotly figures to images.

```bash
$ pip install kaleido
```

Kaleido's strategy has changed: `chrome` is no longer included. On the other hand,
it's *much* faster and supports parallel processing and memory-saving techniques.

Kaleido will try to use your own platform's `chrome`, but we recommend the following:

```bash
$ kaleido_get_chrome
```

or

```python

import kaleido
await kaleido.get_chrome()
# or
# kaleido.get_chrome_sync()
```

## Quickstart

```python
import kaleido

async with kaleido.Kaleido(n=4, timeout=90) as k:
  # n is number of processes
  await k.write_fig(fig, path="./", opts={"format":"jpg"})

# other `kaleido.Kaleido` arguments:
# page:  Change library version (see PageGenerators below)

# `Kaleido.write_fig()` arguments:
# - fig:       A single plotly figure or an iterable.
# - path:      A directory (names auto-generated based on title)
#              or a single file.
# - opts:      A dictionary with image options:
#              `{"scale":..., "format":..., "width":..., "height":...}`
# - error_log: If you pass a list here, image-generation errors will be appended
#              to the list and generation continues. If left as `None`, the
#              first error will cause failure.

# You can also use Kaleido.write_fig_from_object:
  await k.write_fig_from_object(fig_objects, error_log)
# where `fig_objects` is a dict to be expanded to the fig, path, opts arguments.
```

There are shortcut functions if just want dont want to create a `Kaleido()`.

```python
import asyncio
import kaleido
asyncio.run(
  kaleido.write_fig(
    fig,
    path="./",
    n=4
  )
)
```

## PageGenerators

The `page` argument takes a `kaleido.PageGenerator()` to customize versions.
Normally, kaleido looks for an installed plotly as uses that version. You can pass
`kaleido.PageGenerator(force_cdn=True)` to force use of a CDN version of plotly (the
default if plotly is not installed).
```
my_page = kaleido.PageGenerator(
  plotly="A fully qualified link to plotly (https:// or file://)",
  mathjax=False # no mathjax, or another fully quality link
  others=["a list of other script links to include"]
)
```

## More info

There are plenty of doc strings in the source code.

See the [Plotly static image export documentation][plotly-export] for more information.

[choreographer]: https://pypi.org/project/choreographer/
[plotly]: https://plotly.com/
[plotly-export]: https://plotly.com/python/static-image-export/
[pypi]: https://pypi.org/
[repo]: https://github.com/plotly/Kaleido
