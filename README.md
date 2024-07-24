# Overview
Kaleido is a cross-platform library for generating static images (e.g. png, svg, pdf, etc.) for web-based visualization libraries. 

In short: If you `pip install kaleido` you can use `fig.write_image("filename.png")`.

It is designed to be relatively straight-forward to extend to other web-based visualization libraries (and other programming languages)- see [BUILD_AND_RELEASE.md](BUILD_AND_RELEASE.md) for that and other developer questions.

[Here is the historical readme](README-HISTORICAL.md)

<div align="center">
  <a href="https://dash.plotly.com/project-maintenance">
    <img src="https://dash.plotly.com/assets/images/maintained-by-plotly.png" width="400px" alt="Maintained by Plotly">
  </a>
</div>


# Installing Kaleido

The kaleido package can be installed from [PyPI](https://pypi.org/) using pip...

```
$ pip install kaleido
```

or from [conda-forge](https://conda-forge.org/) using conda.

```
$ conda install -c conda-forge python-kaleido
```

Releases of the core kaleido C++ executable are attached as assets to GitHub releases at https://github.com/plotly/Kaleido/releases.

# Use Kaleido to export plotly.py figures as static images

Versions 4.9 and above of the Plotly Python library will automatically use kaleido for static image export when kaleido is installed. For example:

```python
import plotly.express as px
fig = px.scatter(px.data.iris(), x="sepal_length", y="sepal_width", color="species")
fig.write_image("figure.png", engine="kaleido")
```

Then, open `figure.png` in the current working directory.

![fig](https://user-images.githubusercontent.com/15064365/101241780-3590b580-36c7-11eb-8eba-eb1fae256ad0.png)


See the plotly static image export documentation for more information: https://plotly.com/python/static-image-export/.

# Low-level Kaleido Scope Developer API

The kaleido Python package provides a low-level Python API that is designed to be used by high-level plotting libraries like Plotly.  Here is an example of exporting a Plotly figure using the low-level Kaleido API:

> Note: This particular example uses an online copy of the plotly JavaScript library from a CDN location, so it will not work without an internet connection.  When the plotly Python library uses Kaleido (as in the example above), it provides the path to its own local offline copy of plotly.js and so no internet connection is required.

```python
from kaleido.scopes.plotly import PlotlyScope
import plotly.graph_objects as go
scope = PlotlyScope(
    plotlyjs="https://cdn.plot.ly/plotly-2.0.0.min.js",
    # plotlyjs="/path/to/local/plotly.js",
)

fig = go.Figure(data=[go.Scatter(y=[1, 3, 2])])
with open("figure.png", "wb") as f:
    f.write(scope.transform(fig, format="png"))
```

Then, open `figure.png` in the current working directory.

![figure](https://user-images.githubusercontent.com/15064365/86343448-f8f7f400-bc26-11ea-9191-6803748c2dc9.png)
