import datetime
from decimal import Decimal

import numpy as np
import pandas as pd

import kaleido._json as kaleido_json
from kaleido._kaleido_tab._tab import _orjson_default
from kaleido._json import dumps as _json_dumps


def test_orjson_default_handles_datetime_like():
    # A pandas Timestamp has no ``.tolist()`` and used to raise TypeError (#458);
    # _orjson_default should fall back to an ISO string, like Plotly's encoder.
    ts = pd.Timestamp("2026-06-03 12:00:00")
    assert _orjson_default(ts) == ts.isoformat()

    a_date = datetime.date(2026, 1, 2)
    assert _orjson_default(a_date) == a_date.isoformat()

    # tz-aware Timestamps keep their offset (unlike plotly.py's cleaner, which
    # drops tz on scalars via .to_pydatetime()). Plotly.js parses either form.
    tz_ts = pd.Timestamp("2026-06-03 12:00:00", tz="UTC")
    assert _orjson_default(tz_ts) == tz_ts.isoformat()
    assert _orjson_default(tz_ts).endswith("+00:00")

    # A figure spec carrying a Timestamp now round-trips through the JSON backend.
    spec = {"x": [ts]}
    dumped = _json_dumps(spec)
    assert ts.isoformat() in dumped

    # Existing fallbacks are unaffected.
    decimal_value = Decimal("1.5")
    assert _orjson_default(decimal_value) == float(decimal_value)
    array_values = [1, 2, 3]
    assert _orjson_default(np.array(array_values)) == array_values


def test_json_backend_falls_back_without_orjson(monkeypatch):
    monkeypatch.setattr(kaleido_json, "orjson", None)

    dumped = _json_dumps(
        {
            "date": datetime.date(2026, 1, 2),
            "decimal": Decimal("1.5"),
            "array": np.array([1, 2, 3]),
        }
    )

    assert '"date":"2026-01-02"' in dumped
    assert '"decimal":1.5' in dumped
    assert '"array":[1,2,3]' in dumped
