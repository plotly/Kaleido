import numpy as np
import plotly.graph_objects as go
import pytest

import kaleido

TOTAL_POINTS = 5_000_000


@pytest.mark.parametrize(
    ("num_traces", "num_points"),
    [
        (1, TOTAL_POINTS),
        (1_000, TOTAL_POINTS / 1_000),
    ],
)
async def test_large_fig(num_traces, num_points):
    fig = go.Figure()
    for _ in range(num_traces):
        fig.add_trace(
            go.Scatter(
                x=np.arange(num_points, dtype=float),
                y=np.arange(num_points, dtype=float),
            )
        )
    assert isinstance(await kaleido.calc_fig(fig), bytes)
