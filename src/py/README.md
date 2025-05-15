
<div align="center">
  <a href="https://dash.plotly.com/project-maintenance">
    <img src="https://dash.plotly.com/assets/images/maintained-by-plotly.png"
    width="400px" alt="Maintained by Plotly">
  </a>
</div>

# Pre-Launch Kaleido v1.0.0

Kaleido allows you to convert plotly figures to images. Kaleido v1 is currently available as a release candidate.

## Migrating from v0 to v1

Kaleido v1 introduces a new API. If you're currently using v0, you'll need to make changes to your code and environment where you are running Kaleido.

- Chrome is no longer included with Kaleido. Kaleido will look for an existing Chrome installation, but also provides commands for installing Chrome. If you don't have Chrome, you'll need to install it. See the following installation section for more details.
- `kaleido.scopes.plotly` has been removed in v1. Kaleido v1 provides `write_fig` and `write_fig_sync` for exporting Plotly figures.
  ```
  from kaleido import write_fig_sync
  import plotly.graph_objects as go

  fig = go.Figure(data=[go.Scatter(y=[1, 3, 2])])
  kaleido.write_fig_sync(fig, path="figure.png")
  ```
  See the Quickstart section below for more details on usage for v1.

Note: Kaleido v1 works with Plotly v6.1.0 and later.

## Installation

To install the Kaleido release candidate:

```bash
$ pip install kaleido --upgrade --pre
```

To install Chrome, we recommend using Kaleido's CLI command:

```bash
$ kaleido_get_chrome
```

or functions in Python:

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

[choreographer]: https://pypi.org/project/choreographer/
[plotly]: https://plotly.com/
[plotly-export]: https://plotly.com/python/static-image-export/
[pypi]: https://pypi.org/
[repo]: https://github.com/plotly/Kaleido
