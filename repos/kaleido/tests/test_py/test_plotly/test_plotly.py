import os
import sys
from .. import baseline_root, tests_root
from kaleido.scopes.plotly import PlotlyScope
import pytest
from .fixtures import all_figures, all_formats, mapbox_figure, simple_figure
import plotly.graph_objects as go

import plotly.io as pio
pio.templates.default = None

if sys.version_info >= (3, 3):
    from unittest.mock import Mock
else:
    from mock import Mock

os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.environ['GALLIUM_DRIVER'] = 'softpipe'


# Constants
mapbox_access_token = os.environ.get("MAPBOX_TOKEN")
local_plotlyjs_path = tests_root / "test_plotly" / "resources" / "plotly.min.js"
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


def write_failed(data, name, format):
    failed_dir = baseline_root / 'plotly' / "failed"
    failed_dir.mkdir(parents=True, exist_ok=True)
    failed_path = failed_dir / (name + '.' + format)
    with failed_path.open('wb') as f:
        f.write(data)


@pytest.mark.parametrize('fig,name', all_figures())
@pytest.mark.parametrize('format', all_formats)
def test_simple_figure(fig, name, format):
    result = scope.transform(fig, format=format, width=700, height=500, scale=1)

    # Uncomment to create new baselines
    write_baseline(result, name, format)

    expected = load_baseline(name, format)

    try:
        if format == "svg":
            # SVG not yet reproducible
            assert result.startswith(b'<svg')
        elif format == "pdf":
            # PDF not yet reproducible
            assert result.startswith(b'%PDF')
        elif format == "emf":
            # EMF not yet reproducible
            assert result.startswith(b"\x01\x00\x00")
        else:
            assert result == expected
    except AssertionError:
        write_failed(result, name, format)
        raise


def test_missing_mapbox_token():
    fig = mapbox_figure()
    local_scope = PlotlyScope(mapbox_access_token=None)
    with pytest.raises(ValueError) as e:
        local_scope.transform(fig)

    e.match("access token")


def test_plotlyjs_file_url():
    fig = simple_figure()
    plotlyjs_url = local_plotlyjs_url
    local_scope = PlotlyScope(plotlyjs=plotlyjs_url)

    result = local_scope.transform(fig, format='png', width=700, height=500, scale=1)
    expected = load_baseline('simple', 'png')
    assert result == expected


def test_plotlyjs_local_file():
    fig = simple_figure()
    plotlyjs_path = local_plotlyjs_path
    local_scope = PlotlyScope(plotlyjs=plotlyjs_path)

    result = local_scope.transform(fig, format='png', width=700, height=500, scale=1)
    expected = load_baseline('simple', 'png')
    assert result == expected


def test_plotlyjs_bad_local_file():
    plotlyjs_path = str(local_plotlyjs_path) + ".bogus"
    with pytest.raises(ValueError) as e:
        PlotlyScope(plotlyjs=plotlyjs_path).transform(simple_figure())

    e.match("plotlyjs argument is not a valid URL")


def test_bad_format_file():
    fig = simple_figure()
    local_scope = PlotlyScope()
    with pytest.raises(ValueError) as e:
        local_scope.transform(fig, format='bogus')

    e.match("Invalid format")


def test_figure_size():
    # Create mocked scope
    scope = PlotlyScope()
    transform_mock = Mock(return_value={"code": 0, "result": "image"})
    scope._perform_transform = transform_mock

    # Set defualt width / height
    scope.default_width = 543
    scope.default_height = 567
    scope.default_format = "svg"
    scope.default_scale = 2

    # Make sure default width/height is used when no figure
    # width/height specified
    transform_mock.reset_mock()
    fig = go.Figure()
    scope.transform(fig)
    transform_mock.assert_called_once_with(
        fig.to_dict(), format="svg", scale=2, width=543, height=567
    )

    # Make sure figure's width/height takes precedence over defaults
    transform_mock.reset_mock()
    fig = go.Figure().update_layout(width=123, height=234)
    scope.transform(fig)
    transform_mock.assert_called_once_with(
        fig.to_dict(), format="svg", scale=2, width=123, height=234
    )

    # Make sure kwargs take precedence over Figure layout values
    transform_mock.reset_mock()
    fig = go.Figure().update_layout(width=123, height=234)
    scope.transform(fig, width=987, height=876)
    transform_mock.assert_called_once_with(
        fig.to_dict(), format="svg", scale=2, width=987, height=876
    )


def test_gpu_arg():
    # --disable-gpu is a default
    assert "--disable-gpu" in PlotlyScope.default_chromium_args()

    # Check that --disable-gpu is in scope instance chromium_args
    scope = PlotlyScope()
    assert "--disable-gpu" in scope.chromium_args
    assert "--disable-gpu" in scope._build_proc_args()

    # Check that --disable-gpu is in scope instance chromium_args
    scope = PlotlyScope(disable_gpu=False)
    assert "--disable-gpu" not in scope.chromium_args
    assert "--disable-gpu" not in scope._build_proc_args()
    scope.disable_gpu = True
    assert "--disable-gpu" in scope.chromium_args
    assert "--disable-gpu" in scope._build_proc_args()


def test_custopm_chromium_arg():
    # Check that --disable-gpu is in scope instance chromium_args
    chromium_args = PlotlyScope.default_chromium_args() + ("--single-process",)
    scope = PlotlyScope(chromium_args=chromium_args)
    assert "--single-process" in scope._build_proc_args()
