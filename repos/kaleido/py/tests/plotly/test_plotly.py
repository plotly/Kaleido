import os
from os.path import join
from .. import baseline_root
from kaleido.scopes.plotly import PlotlyScope
import plotly.io as pio
pio.templates.default = None

import pytest
from .fixtures import all_figures, all_formats


scope = PlotlyScope()

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
