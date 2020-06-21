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

    # # Create baseline
    # with open(baseline_path, 'wb') as f:
    #     f.write(result)

    # Read baseline
    with open(baseline_path, 'rb') as f:
        expected = f.read()

    assert result == expected