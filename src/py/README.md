
<div align="center">
  <a href="https://dash.plotly.com/project-maintenance">
    <img src="https://dash.plotly.com/assets/images/maintained-by-plotly.png"
    width="400px" alt="Maintained by Plotly">
  </a>
</div>

# Overview

Kaleido is a cross-platform Python library for generating static images (e.g. png, svg, pdf, etc.) for Plotly.js, to be used by Plotly.py.

## Installation

Kaleido can be installed from [PyPI](https://pypi.org/project/kaleido) using `pip`:

```bash
$ pip install kaleido --upgrade
```

As of version 1.0.0, Kaleido requires Chrome to be installed. If you already have Chrome on your system, Kaleido should find it; otherwise, you can install a compatible Chrome version using the `kaleido_get_chrome` command:

```bash
$ kaleido_get_chrome
```

or function in Python:

```python
import kaleido
kaleido.get_chrome_sync()
```

## Migrating from v0 to v1

Kaleido v1 introduces a new API. If you're currently using v0, you'll need to make changes to your code and environment where you are running Kaleido.

- If using Kaleido v1 with Plotly.py, you will need to install Plotly.py v6.1.1 or later.
- Chrome is no longer included with Kaleido. Kaleido will look for an existing Chrome installation, but also provides commands for installing Chrome. If you don't have Chrome, you'll need to install it. See the installation section above for instructions.
- If your code uses Kaleido directly: `kaleido.scopes.plotly` has been removed in v1. Kaleido v1 provides `write_fig` and `write_fig_sync` for exporting Plotly figures.
```
from kaleido import write_fig_sync
import plotly.graph_objects as go

fig = go.Figure(data=[go.Scatter(y=[1, 3, 2])])
kaleido.write_fig_sync(fig, path="figure.png")
```

## Development guide

Below are examples of how to use Kaleido directly in your Python program.

If you want to export images of Plotly charts, it's not necessary to call Kaleido directly; you can use functions in the Plotly library. [See the Plotly documentation for instructions.](https://plotly.com/python/static-image-export/)

### Usage examples

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

There are shortcut functions which can be used to generate images without creating a `Kaleido()` object:

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

### Page Customization

Plotly figures are rendered in Chrome before being exported. The HTML of the page on which the Figure is rendered contains scripts that determine how the Figure is rendered. For example, by default if Plotly.py is installed, Kaleido uses the Plotly.js version included with Plotly.py in the HTML template. 

You can customize the specific scripts used in the HTML using the `page` parameter on the `kaleido.Kaleido` class, or through the `kopts` parameter in shortcut functions like `kaleido.write_fig`, `kaleido.write_fig_sync`, `kaleido.calc_fig`, etc.

Provide a path to a HTML file as a string or `pathlib.Path`, or use a `kaleido.PageGenerator` object that specifies which scripts to include in the HTML.

```python
import kaleido
import plotly.graph_objects as go
import pathlib

fig = go.Figure(data=[go.Scatter(y=[1, 3, 2])])
kaleido.write_fig_sync(fig, path="figure.png", kopts=dict(page_generator=pathlib.Path("<path-to-template>")))
```

```python
import kaleido
import plotly.graph_objects as go
import pathlib

fig = go.Figure(data=[go.Scatter(y=[1, 3, 2])])

# Using Kaleido class directly
async with kaleido.Kaleido(page=pathlib.Path("<path-to-template>")) as k:
    await k.write_fig(fig, path="figure.png")
```

#### PageGenerator

The `kaleido.PageGenerator` class allows you to customize the HTML of the page where the Plotly figure is rendered before it is exported. 

`kaleido.PageGenerator` accepts the following arguments and builds a HTML template using the values provided.

- **`plotly`** (str): URL to the Plotly.js script. Default uses Plotly.js included with the installed Plotly.py version. 
- **`mathjax`** (str or bool): URL to MathJax script, or `False` to disable
- **`others`** (list): Additional script URLs to include (strings or `(url, encoding)` tuples)
- **`force_cdn`** (bool): Force CDN usage instead of local Plotly (default: `False`)

Here's an example of a `PageGenerator` configured to use an older version of Plotly.js when rendering and exporting the figure.

```python
import kaleido
import plotly.graph_objects as go

fig = go.Figure(data=[go.Scatter(y=[1, 3, 2])])

custom_page = kaleido.PageGenerator(plotly="https://cdn.plot.ly/plotly-2.0.0.min.js")

kaleido.write_fig_sync(fig, path="my_graph.png", kopts={"page_generator": custom_page})
```

A page generator can also be used on the `kaleido.Kaleido` class by passing it to the `page_generator` parameter. 

```python
import kaleido
import plotly.graph_objects as go

fig = go.Figure(data=[go.Scatter(y=[1, 3, 2])])

async with kaleido.Kaleido(page_generator=kaleido.PageGenerator(plotly="https://cdn.plot.ly/plotly-2.0.0.min.js")) as k:
  await k.write_fig(fig, path="my_graph.png", opts={"format":"jpg"})
```
