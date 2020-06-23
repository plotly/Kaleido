import os
# from os.path import join
import pathlib
from .. import baseline_root, tests_root
from kaleido.scopes.plotly import PlotlyScope
import pytest
from .fixtures import all_figures, all_formats, mapbox_figure, simple_figure
import plotly.io as pio
pio.templates.default = None


# Constants
mapbox_access_token = os.environ.get("MAPBOX_TOKEN")
local_plotlyjs_path = tests_root / "plotly" / "resources" / "plotly.min.js"
local_plotlyjs_url = local_plotlyjs_path.as_uri()

mathjax = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js"

# Initialize a global scope, this way we test multiple uses
scope = PlotlyScope(
    mathjax=mathjax, mapbox_access_token=mapbox_access_token
)


def load_baseline(name, format):
    baseline_path = baseline_root / 'plotly' / (name + '.' + format)
    with baseline_path.open('rb') as f:
        expected = f.read()
    return expected


def write_baseline(data, name, format):
    baseline_path = baseline_root / 'plotly' / (name + '.' + format)
    with baseline_path.open('wb') as f:
        f.write(data)


@pytest.mark.parametrize('fig,name', all_figures())
@pytest.mark.parametrize('format', all_formats)
def test_simple_figure(fig, name, format):
    result = scope.to_image(fig, format=format, width=700, height=500, scale=1)
    expected = load_baseline(name, format)

    # # Uncomment to create new baselines
    # write_baseline(data, name, format)

    if format == "svg":
        # SVG not yet reprodicible
        assert result.startswith(b'<svg')
    elif format == "pdf":
        # PDF not yet reprodicible
        assert result.startswith(b'%PDF')
    else:
        assert result == expected


def test_missing_mapbox_token():
    fig = mapbox_figure()
    local_scope = PlotlyScope(mapbox_access_token=None)
    with pytest.raises(ValueError) as e:
        local_scope.to_image(fig)

    e.match("access token")


def test_plotlyjs_file_url():
    fig = simple_figure()
    plotlyjs_url = local_plotlyjs_url
    local_scope = PlotlyScope(plotlyjs=plotlyjs_url)

    result = local_scope.to_image(fig, format='png', width=700, height=500, scale=1)
    expected = load_baseline('simple', 'png')
    assert result == expected


def test_plotlyjs_local_file():
    fig = simple_figure()
    plotlyjs_path = local_plotlyjs_path
    local_scope = PlotlyScope(plotlyjs=plotlyjs_path)

    result = local_scope.to_image(fig, format='png', width=700, height=500, scale=1)
    expected = load_baseline('simple', 'png')
    assert result == expected


def test_plotlyjs_bad_local_file():
    plotlyjs_path = str(local_plotlyjs_path) + ".bogus"
    with pytest.raises(ValueError) as e:
        PlotlyScope(plotlyjs=plotlyjs_path).to_image(simple_figure())

    e.match("plotlyjs argument is not a valid URL")


def test_bad_format_file():
    fig = simple_figure()
    local_scope = PlotlyScope()
    with pytest.raises(ValueError) as e:
        local_scope.to_image(fig, format='bogus')

    e.match("wrong format")
