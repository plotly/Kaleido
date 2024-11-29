# Kaleido2

`kaleido2` is a cross-platform library for generating static images for [Plotly][plotly]'s visualization library.
Unlike its predecessor [`kaleido`][kaleido],
this package does not include a custom build of the Chrome browser.
Instead,
it relies on a separate browser binary,
which makes it much smaller and easier to maintain.

<div align="center">
  <a href="https://dash.plotly.com/project-maintenance">
    <img src="https://dash.plotly.com/assets/images/maintained-by-plotly.png" width="400px" alt="Maintained by Plotly">
  </a>
</div>

## Installation

You can install `kaleido2` from [PyPI][pypi] using `pip`:

```
$ pip install kaleido2
```

## Use

Once you have installed `kaleido2` you can generate and save an image of a chart
with just a single line of code:

```python
import plotly.express as px
fig = px.scatter(px.data.iris(), x="sepal_length", y="sepal_width", color="species")
fig.write_image("figure.png", engine="kaleido")
```

See the [Plotly static image export documentation][plotly-export] for more information.

## How It Works

The original [`kaleido`][kaleido] included a custom build of the Chrome web browser,
which made it very large and proved very difficult to maintain.
In contrast,
[`kaleido2`][kaleido2] depends on [choreographer][choreographer],
a lightweight library that enables Python programs to control browsers.
In order to create an image,
When you ask kaleido to create an image,
[`kaleido2`][kaleido2] uses [choreographer][choreographer] to run a headless instance of Chrome
to render and save your figure.

<img src="https://github.com/plotly/kaleio/blob/master/assets/architecture.svg?raw=true" alt="kaleido and kaleido2 architectures"/>

## Contributing

[`kaleido2`][kaleido2] is a work on progress;
we would be grateful for help testing it and improving it.
If you find a bug, please report it in [our GitHub repository][repo],
and please include a minimal reproducible example if you can.

[choreographer]: https://pypi.org/project/choreographer/
[kaleido]: https://pypi.org/project/kaleido2/
[plotly]: https://plotly.com/
[plotly-export]: https://plotly.com/python/static-image-export/
[pypi]: https://pypi.org/
[repo]: https://github.com/plotly/Kaleido
