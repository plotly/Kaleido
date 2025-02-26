import warnings

import logistro
import pytest

import kaleido

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")

_logger = logistro.getLogger(__name__)


async def test_calc_fig():
    import plotly.express as px

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        fig = px.line(x=[1, 2, 3, 4], y=[1, 2, 3, 4])

    img = await kaleido.calc_fig(fig)
    assert isinstance(img, bytes)

    img = kaleido.calc_fig_sync(fig)
    assert isinstance(img, bytes)

    img = kaleido.calc_fig_sync(fig.to_dict())
    assert isinstance(img, bytes)

    with pytest.raises(TypeError):
        # can't accept iterables
        img = kaleido.calc_fig_sync([fig, fig])
