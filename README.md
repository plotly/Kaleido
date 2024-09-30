# Overview
Kaleido is a cross-platform library for generating static images (e.g. png, svg, pdf, etc.) for web-based visualization libraries.

In short: If you `pip install kaleido` you can use `fig.write_image("filename.png")`.

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

# Previous Kaleido API

Kaleido was previously arcitectured to accept "scopes"- they are no longer necessary. The old API is demonstrated below but it is only supported to the extent needed as to not break previous implementations of kaleido for plotly. This API will likely emit a deprecation warning, and proceed to be unsupported.

```python
from kaleido.scopes.plotly import PlotlyScope
import plotly.graph_objects as go
scope = PlotlyScope(
    plotlyjs="https://cdn.plot.ly/plotly-latest.min.js",
    # plotlyjs="/path/to/local/plotly.js",
)

fig = go.Figure(data=[go.Scatter(y=[1, 3, 2])])
with open("figure.png", "wb") as f:
    f.write(scope.transform(fig, format="png"))
```

Then, open `figure.png` in the current working directory.

![figure](https://user-images.githubusercontent.com/15064365/86343448-f8f7f400-bc26-11ea-9191-6803748c2dc9.png)
