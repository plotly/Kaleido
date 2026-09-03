"""Test Kaleido v1 pre-render serialization for Plotly-compatible values.

Technical specification
=======================

Purpose
-------
This module is intended for the current ``plotly/Kaleido`` Python test suite,
where Kaleido v1 serializes the Plotly figure spec inside the Python process
before sending it to the browser/JavaScript render boundary. It is designed to
catch regressions where Kaleido's pre-render serializer is narrower than
Plotly's own JSON serialization contract.

The compatibility contract tested here is deliberately narrow and reproducible:
for every parametrized value/location pair, ``fig.to_dict()`` may contain a
non-JSON-native Python object, but ``json.dumps(fig.to_dict(),
cls=PlotlyJSONEncoder)`` must succeed and must decode to a JSON-compatible
representation at the same figure-spec path. If Plotly's encoder accepts that
raw figure spec, Kaleido's pre-render static-export path should not fail while
serializing the same spec.

Why this module does not perform real image export
-------------------------------------------------
The test matrix is intentionally broad and covers many figure-spec locations:
2D trace ``x``/``y`` data, 3D trace ``x``/``y``/``z`` data, matrix trace
``z`` data, ``customdata``, trace and layout ``meta``, 2D annotations,
3D scene annotations, individual shape coordinates, axis ranges, and
representative axis tick values. Rendering all combinations through a real
browser would be slow and would also mix serialization failures with unrelated
Plotly.js rendering semantics. For example, some serialized annotation
coordinates can be valid JSON but not meaningful visual coordinates for the
constructed trace, which can fail later in SVG generation for reasons unrelated
to Python-side JSON serialization.

Instead, these tests mock the JavaScript/devtools call made by
``_KaleidoTab._calc_fig``. The mocked tests still execute the Python-side
pre-render serialization code used by image export, including Kaleido's
``orjson.dumps(..., default=_orjson_default, option=OPT_SERIALIZE_NUMPY)`` call,
but they do not launch Chrome and do not require an actual SVG render. This is
aligned with Kaleido's existing testing guidance that large parametrized real
renders are burdensome and that mocked integration tests provide the most useful
coverage for substantial internal behavior.

Case matrix
-----------
The shared matrix in ``_plotly_json_compat_cases.py`` covers scalar values and
containers commonly produced by pandas, NumPy, datetime, and Decimal workflows.
It includes currently supported Plotly JSON cases such as ``decimal.Decimal``,
``pandas.Timestamp``, ``pandas.NaT``, ``pandas.NA``, ``pandas.Timedelta``, NumPy
scalar values, non-finite floats, Python datetime/date/time values, pandas
``Series`` and ``DatetimeIndex`` containers, NumPy datetime/object arrays,
nullable pandas extension dtypes, and ``pandas.Categorical``. Text fields are
not part of the broad matrix because Plotly graph objects often coerce them to
strings before JSON serialization, so they do not reliably exercise Kaleido's
non-native-value serializer.

The helper matrix also records common scientific-Python values that do not yet
have an established Plotly JSON compatibility contract, including
``numpy.timedelta64``, ``datetime.timedelta``, ``pandas.Period``,
``pandas.Interval``, and complex values. Those are kept in explicit xfail tests
so maintainers can see the boundary between restoring historical Plotly-compatible
behavior and defining new behavior.

Assertions
----------
Each supported case is checked at three scopes:

1. Plotly baseline: the raw figure spec contains the value at the intended path,
   allowing for Plotly's version-specific normalization of containers, and
   ``PlotlyJSONEncoder`` converts it to an expected JSON-compatible value.
2. Cleaning proof: the Plotly-cleaned spec serializes with Kaleido's v1 orjson
   configuration. This verifies that successful cleaning is enough to satisfy
   Kaleido's lower-level serializer.
3. Mocked Kaleido integration: ``_KaleidoTab._calc_fig`` is called with the raw
   ``fig.to_dict()`` spec while only the browser/JavaScript call is mocked. This
   is the regression check: before the serialization fix, cases such as
   ``decimal.Decimal`` and ``pandas.Timestamp`` fail before reaching the mocked
   JavaScript boundary; after the fix, they should pass.

What this module is not
-----------------------
This module is not a Plotly 5 / Kaleido 0.x compatibility test. Kaleido 0.x used
``kaleido.scopes.plotly.PlotlyScope`` and delegated serialization to
``plotly.io.to_json``; Kaleido v1 removed that public package layout and now has
a different pre-render path. A separate historical demonstration module can be
used to show the old behavior, but this file should target the current Kaleido
main branch.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from _plotly_json_compat_cases import (
    _MISSING,
    SUPPORTED_CONTAINER_CASES,
    SUPPORTED_SCALAR_CASES,
    UNSUPPORTED_CASES,
    SerializationCase,
    UnsupportedCase,
    assert_plotly_encoder_accepts_case,
    get_path,
    plotly_cleaned_spec,
)
from plotly.utils import PlotlyJSONEncoder

kaleido_tab = pytest.importorskip(
    "kaleido._kaleido_tab._tab",
    reason="Kaleido v1 _KaleidoTab serialization path is required.",
)

_DUMMY_SVG = "<svg xmlns='http://www.w3.org/2000/svg'></svg>"


class DummyProfileLog:
    """Small profile-log replacement used by mocked ``_calc_fig`` tests."""

    def __init__(self) -> None:
        """Initialize an empty list of observed profiling ticks."""
        self.ticks: list[str] = []

    def tick(self, message: str) -> None:
        """Record a profile tick message.

        Args:
            message: Profile event message emitted by Kaleido internals.
        """
        self.ticks.append(message)


class DummyRenderProfile:
    """Small render-profile replacement used by mocked ``_calc_fig`` tests."""

    def __init__(self) -> None:
        """Initialize fields mutated by Kaleido's private ``_calc_fig`` method."""
        self.profile_log = DummyProfileLog()
        self.data_out_size = 0
        self.js_log: list[str] = []


class DummyJsLogger:
    """Small JavaScript logger replacement used by mocked ``_calc_fig`` tests."""

    def __init__(self) -> None:
        """Initialize an empty JavaScript log field."""
        self.log: list[str] = []


class DummyKaleidoTab:
    """Object carrying the attributes needed by ``_KaleidoTab._calc_fig``."""

    def __init__(self) -> None:
        """Initialize the minimal attributes read by the private method."""
        self.tab = object()
        self._current_js_id = "mocked-js-id"
        self.js_logger = DummyJsLogger()


async def _fake_exec_js_fn(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    """Return a minimal successful Kaleido JavaScript response.

    Args:
        *_args: Positional arguments accepted by the real devtools helper.
        **_kwargs: Keyword arguments accepted by the real devtools helper.

    Returns:
        Nested response dictionary consumed by ``check_kaleido_js_response``.
    """
    value = json.dumps({"code": 0, "format": "svg", "result": _DUMMY_SVG})
    return {"result": {"result": {"value": value}}}


def kaleido_prerender_serialize(spec: dict[str, Any]) -> bytes:
    """Serialize a spec the same way Kaleido v1 serializes before rendering.

    Args:
        spec: Plotly figure spec passed to Kaleido's browser/render boundary.

    Returns:
        UTF-8 JSON bytes produced by Kaleido's ``orjson`` configuration.
    """
    return kaleido_tab.orjson.dumps(
        spec,
        default=kaleido_tab._orjson_default,  # noqa: SLF001
        option=kaleido_tab.orjson.OPT_SERIALIZE_NUMPY,
    )


def _mock_browser_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the JavaScript/devtools boundary with a deterministic response.

    Args:
        monkeypatch: Pytest fixture used to replace the browser call.
    """
    monkeypatch.setattr(
        kaleido_tab._dtools,  # noqa: SLF001
        "exec_js_fn",
        _fake_exec_js_fn,
    )


def _calc_fig_without_browser(case: SerializationCase) -> bytes:
    """Run Kaleido's v1 pre-render path with the browser boundary mocked.

    Args:
        case: Supported value/location pair under test.

    Returns:
        Bytes returned by ``_KaleidoTab._calc_fig`` after the mocked boundary.
    """
    return asyncio.run(
        kaleido_tab._KaleidoTab._calc_fig(  # noqa: SLF001
            DummyKaleidoTab(),
            case.location.build(case.value.make()).to_dict(),
            topojson=None,
            render_prof=DummyRenderProfile(),
            stepper=None,
        ),
    )


@pytest.mark.parametrize("case", SUPPORTED_SCALAR_CASES, ids=lambda case: case.id)
class TestPlotlyCompatibleScalarValues:
    """Regression tests for Plotly-serializable scalar values."""

    def test_plotly_json_encoder_baseline_accepts_scalar_case(
        self,
        case: SerializationCase,
    ) -> None:
        """Verify Plotly's encoder accepts this scalar/location pair.

        Args:
            case: Supported scalar value and figure-spec location under test.
        """
        assert_plotly_encoder_accepts_case(case)

    def test_plotly_cleaned_scalar_case_serializes_with_kaleido_orjson(
        self,
        case: SerializationCase,
    ) -> None:
        """Verify Plotly-cleaned scalar specs are serializable by Kaleido.

        Args:
            case: Supported scalar value and figure-spec location under test.
        """
        fig = case.location.build(case.value.make())
        cleaned_spec = plotly_cleaned_spec(fig)
        encoded = kaleido_prerender_serialize(cleaned_spec)

        assert isinstance(encoded, bytes)
        assert json.loads(encoded)

    def test_kaleido_mocked_calc_fig_accepts_scalar_case(
        self,
        case: SerializationCase,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify Kaleido's pre-render path serializes this scalar case.

        Args:
            case: Supported scalar value and figure-spec location under test.
            monkeypatch: Pytest fixture used to replace the browser call.
        """
        _mock_browser_boundary(monkeypatch)

        result = _calc_fig_without_browser(case)

        assert result == _DUMMY_SVG.encode()


@pytest.mark.parametrize("case", SUPPORTED_CONTAINER_CASES, ids=lambda case: case.id)
class TestPlotlyCompatibleContainerValues:
    """Regression tests for pandas and NumPy containers in figure specs."""

    def test_plotly_json_encoder_baseline_accepts_container_case(
        self,
        case: SerializationCase,
    ) -> None:
        """Verify Plotly's encoder accepts this container/location pair.

        Args:
            case: Supported pandas/NumPy container and figure-spec location.
        """
        assert_plotly_encoder_accepts_case(case)

    def test_plotly_cleaned_container_case_serializes_with_kaleido_orjson(
        self,
        case: SerializationCase,
    ) -> None:
        """Verify Plotly-cleaned container specs are serializable by Kaleido.

        Args:
            case: Supported pandas/NumPy container and figure-spec location.
        """
        fig = case.location.build(case.value.make())
        cleaned_spec = plotly_cleaned_spec(fig)
        encoded = kaleido_prerender_serialize(cleaned_spec)

        assert isinstance(encoded, bytes)
        assert json.loads(encoded)

    def test_kaleido_mocked_calc_fig_accepts_container_case(
        self,
        case: SerializationCase,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify Kaleido's pre-render path serializes this container case.

        Args:
            case: Supported pandas/NumPy container and figure-spec location.
            monkeypatch: Pytest fixture used to replace the browser call.
        """
        _mock_browser_boundary(monkeypatch)

        result = _calc_fig_without_browser(case)

        assert result == _DUMMY_SVG.encode()


@pytest.mark.parametrize("unsupported", UNSUPPORTED_CASES, ids=lambda case: case.name)
class TestCurrentlyUnsupportedScientificPythonValues:
    """Document common values outside Plotly's current JSON contract."""

    def test_plotly_json_encoder_does_not_currently_support_value(
        self,
        unsupported: UnsupportedCase,
    ) -> None:
        """Verify unsupported values are not silently treated as supported.

        Args:
            unsupported: Common but currently unsupported scientific-Python value.
        """
        import plotly.graph_objects as go  # noqa: PLC0415

        fig = go.Figure(
            go.Scatter(x=[1], y=[1], meta={"special": unsupported.make()}),
        )
        raw_value = get_path(fig.to_dict(), ("data", 0, "meta", "special"))

        assert raw_value is not _MISSING
        with pytest.raises(TypeError, match=r"not JSON serializable|JSON"):
            json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)

    @pytest.mark.xfail(
        reason=(
            "No established Plotly JSON compatibility contract for this common "
            "scientific-Python value."
        ),
        strict=True,
    )
    def test_kaleido_mocked_calc_fig_for_currently_unsupported_value(
        self,
        unsupported: UnsupportedCase,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Document Kaleido behavior for currently unsupported value types.

        Args:
            unsupported: Common but currently unsupported scientific-Python value.
            monkeypatch: Pytest fixture used to replace the browser call.
        """
        import plotly.graph_objects as go  # noqa: PLC0415

        _mock_browser_boundary(monkeypatch)
        fig = go.Figure(
            go.Scatter(x=[1], y=[1], meta={"special": unsupported.make()}),
        )
        result = asyncio.run(
            kaleido_tab._KaleidoTab._calc_fig(  # noqa: SLF001
                DummyKaleidoTab(),
                fig.to_dict(),
                topojson=None,
                render_prof=DummyRenderProfile(),
                stepper=None,
            ),
        )

        assert result == _DUMMY_SVG.encode()
