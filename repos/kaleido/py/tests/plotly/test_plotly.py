import os
from os.path import join
from .. import baseline_root
from kaleido.scopes.plotly import PlotlyScope
import plotly.io as pio
pio.templates.default = None

import pytest
from .fixtures import all_figures, all_formats

# Constants
mapbox_access_token = "pk.eyJ1Ijoiam1tZWFzZSIsImEiOiJjamljeWkwN3IwNjEyM3FtYTNweXV4YmV0In0.2zbgGCjbPTK7CToIg81kMw"
plotlyjs = "file:///home/jmmease/scratch/plotly-latest.min.js"
topojson = "file:///home/jmmease/PyDev/repos/plotly.js/dist/topojson/"
mathjax = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js"


# Initialize a global scope, this way we test multiple uses
scope = PlotlyScope(mathjax=mathjax)


@pytest.mark.parametrize('fig,name', all_figures())
@pytest.mark.parametrize('format', all_formats)
def test_simple_figure(fig, name, format):
    result = scope.to_image(fig, format=format)
    baseline_path = join(baseline_root, 'plotly', name + '.' + format)

    # # Uncomment to create new baselines
    # with open(baseline_path, 'wb') as f:
    #     f.write(result)

    with open(baseline_path, 'rb') as f:
        expected = f.read()

    # Read baseline
    if format == "svg":
        # SVG not yet reprodicible
        assert result.startswith(b'<svg')
    elif format == "pdf":
        # PDF not yet reprodicible
        assert result.startswith(b'%PDF')
    else:
        assert result == expected
