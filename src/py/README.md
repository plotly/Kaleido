# Launch Kaleido v1.0.0

Right now, Kaledio v1.0.0 is available as a release candidate:

* download `v1.0.0rc1` explicitly
* enable whatever installer you use (`pip --pre`?) to use release candidates

Kaleido's strategy has changed: `chrome` is no longer included. On the other hand,
it's *much* faster and supports parallel processing and memory-saving techniques.

Kaleido will try to use your own platform's `chrome`, but we recommend the following:

```
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

# fig is a plotly figure or an iterable of plotly figures

async with kaleido.Kaleido(n=4, timeout=60) as k: # Those are the defaults! 4 processes, 60 seconds.
	await k.write_fig(fig, path="./", opts={"format":"jpg"}) # default format is `png`
```

If you have to print thousands of graphs, fig can be a generator to save memory.
It can also just be a single graph.

There is a shortcut function:

```
import asyncio
import kaleido
asyncio.run(kaleido.write_fig(fig, path="./", n=4))
# this will spin the kaleido process for you with 4 processors
```

If you're not using async/await, wrap it all in an async function and:
```
asyncio.run(my_async_wrapper())
```

#### Older Readme Below ####

# Kaleido

Kaleido is a cross-platform library for generating static images for [Plotly][plotly]'s
visualization library. After installing it, you can use `fig.write_image("filename.png")`
to save a plot to a file.

<div align="center">
  <a href="https://dash.plotly.com/project-maintenance">
    <img src="https://dash.plotly.com/assets/images/maintained-by-plotly.png"
    width="400px" alt="Maintained by Plotly">
  </a>
</div>

## How It Works

The original version of kaleido included a custom build of the Chrome web browser,
which made it very large (hundreds of megabytes) and proved very difficult to maintain.
In contrast, this version depends on [choreographer][choreographer],
a lightweight library that enables remote control of browsers from Python.
When you ask kaleido to create an image, it uses choreographer to run a headless
instance of Chrome to render and save your figure. Please see choreographer's
ocumentation for details.

> The new version of kaleido is a work on progress;
> we would be grateful for help testing it and improving it.
> If you find a bug, please report it in [our GitHub repository][repo],
> and please include a minimal reproducible example if you can.
>
> It would also be very helpful to run the script `src/py/tests/manual.py`
> and attach its zipped output to your bug report.
> This will give us detailed information about the precise versions of software you
> are using and the platform you are running on,
> which will help us track down problems more quickly.

## Installation

You can install kaleido from [PyPI][pypi] using pip:

```
pip install kaleido
```

## Use

Versions 4.9 and above of the Plotly Python library will automatically use kaleido
for static image export when kaleido is installed.
For example:

```python
import plotly.express as px
fig = px.scatter(px.data.iris(), x="sepal_length", y="sepal_width", color="species")
fig.write_image("figure.png", engine="kaleido")
```

See the [Plotly static image export documentation][plotly-export] for more information.

[choreographer]: https://pypi.org/project/choreographer/
[plotly]: https://plotly.com/
[plotly-export]: https://plotly.com/python/static-image-export/
[pypi]: https://pypi.org/
[repo]: https://github.com/plotly/Kaleido
