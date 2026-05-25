from decimal import Decimal

import orjson
import plotly.graph_objects as go

from kaleido._kaleido_tab._tab import _orjson_default
from kaleido._utils import fig_tools


def test_orjson_default_handles_decimal():
    fig = go.Figure(data=[go.Bar(y=[Decimal("10.5"), Decimal(20), Decimal("-3.25")])])
    spec = fig_tools.coerce_for_js(fig, None, {"format": "json"})

    encoded = orjson.dumps(spec, default=_orjson_default)

    assert b'"y":[10.5,20.0,-3.25]' in encoded
