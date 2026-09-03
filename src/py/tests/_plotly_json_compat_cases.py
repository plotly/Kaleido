"""Shared Plotly JSON-compatibility cases for Kaleido serialization tests.

This module defines the value/location matrix used by Kaleido regression tests
that compare Kaleido's pre-render serialization behavior with Plotly's JSON
compatibility contract.  It intentionally contains no Kaleido imports and does
not render figures; each case only constructs a Plotly figure, locates the raw
value in ``fig.to_dict()``, and checks how ``PlotlyJSONEncoder`` cleans that
value into decoded JSON.

Case summary
============

Supported scalar values
-----------------------
The supported scalar matrix covers values that are historically accepted by
Plotly's JSON compatibility layer and are common in pandas, NumPy, datetime, and
scientific-computing workflows:

* ``decimal.Decimal``.
* ``pandas.Timestamp`` with and without timezone information.
* pandas missing and duration sentinels: ``pandas.NaT``, ``pandas.NA``, and
  ``pandas.Timedelta``.
* Python non-finite floats: ``NaN`` and positive infinity, both expected to
  encode as JSON ``null``.
* Python ``datetime.datetime``, ``datetime.date``, and ``datetime.time``.
* NumPy scalar values: ``numpy.datetime64``, signed and unsigned integer
  scalars, floating scalars, and boolean scalars.

Supported container values
--------------------------
The supported container matrix covers pandas and NumPy containers that commonly
appear in Plotly figures created from data frames and scientific arrays:

* datetime containers: ``Series[datetime64]``, ``DatetimeIndex``, and
  ``ndarray[datetime64]``.
* object containers containing non-native scalar values, such as object arrays
  of ``pandas.Timestamp`` and ``Series`` of ``decimal.Decimal``.
* pandas nullable extension dtypes containing ``pandas.NA``:
  ``boolean``, ``string``, and ``Int64``.
* ``pandas.Categorical`` values containing both category labels and missing
  entries.

Figure locations
----------------
The location matrix places these values into several places where real Plotly
figures can carry data or metadata:

* 2D trace data: ``scatter.x`` and ``scatter.y``.
* 3D trace data: ``scatter3d.x``, ``scatter3d.y``, and ``scatter3d.z``.
* Matrix trace data: ``heatmap.z`` and ``surface.z``.
* Per-point payload fields that preserve arbitrary payload values, especially
  ``customdata``. Text fields are intentionally omitted because Plotly graph
  objects often coerce them to strings before JSON serialization.
* Trace and layout metadata: ``trace.meta`` and ``layout.meta``.
* 2D annotations and 3D scene annotations, including scene-annotation ``z``.
* 2D shapes, with separate cases for ``x0``, ``x1``, ``y0``, and ``y1``.
* 2D and 3D axis ranges, plus representative 2D ``tickvals``.

Unsupported boundary cases
--------------------------
The module also records common scientific-Python values that are deliberately
outside the current Plotly JSON compatibility contract: ``numpy.timedelta64``,
``datetime.timedelta``, ``pandas.Period``, ``pandas.Interval``, Python
``complex``, and ``numpy.complex128``.  Tests should mark these as expected
failures unless a PR intentionally defines conversion semantics for them.

Design notes
============

The raw figure-spec predicates are intentionally semantic rather than exact-type
checks for containers. Plotly versions normalize some inputs differently: for
example, datetime ``Series`` may become object arrays of Python datetimes,
nullable integer ``Series`` may become float arrays containing ``NaN``, and
metadata fields may preserve pandas containers directly. The tests therefore
assert that the intended information survived figure construction and that the
Plotly encoder produced the expected JSON-compatible representation, without
requiring one Plotly-version-specific intermediate shape.
"""

from __future__ import annotations

import datetime as dt
import decimal
import json
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

JsonPath = tuple[str | int, ...]
_MISSING = object()
_EXPECTED_INT = 42


@dataclass(frozen=True)
class ValueCase:
    """A value or container placed into a Plotly figure spec.

    Args:
        name: Human-readable pytest id for the value under test.
        make: Factory returning a fresh value for each test invocation.
        raw_predicate: Predicate proving that the raw ``fig.to_dict()`` value is
            the intended non-JSON-native value or a Plotly-normalized equivalent.
        encoded_predicate: Predicate proving that Plotly's JSON encoder cleaned
            the value into an expected JSON-compatible representation.
    """

    name: str
    make: Callable[[], Any]
    raw_predicate: Callable[[Any], bool]
    encoded_predicate: Callable[[Any], bool]


@dataclass(frozen=True)
class FigureLocationCase:
    """A specific location in a Plotly figure spec.

    Args:
        name: Human-readable pytest id for the location.
        build: Factory that places the provided value into the target location.
        path: Path to the target value inside ``fig.to_dict()``.
    """

    name: str
    build: Callable[[Any], go.Figure]
    path: JsonPath


@dataclass(frozen=True)
class SerializationCase:
    """A value/location pair used by parametrized regression tests.

    Args:
        value: Value or container case under test.
        location: Plotly figure location receiving the value.
    """

    value: ValueCase
    location: FigureLocationCase

    @property
    def id(self) -> str:
        """Return a stable pytest id for this value/location pair.

        Returns:
            Identifier containing both the special value and its figure path.
        """
        return f"{self.value.name} in {self.location.name}"


@dataclass(frozen=True)
class UnsupportedCase:
    """A common scientific-Python value without a Plotly JSON contract.

    Args:
        name: Human-readable pytest id for the unsupported value.
        make: Factory returning a fresh value for each test invocation.
    """

    name: str
    make: Callable[[], Any]


# ---------------------------------------------------------------------------
# Path, predicate, and serialization helpers
# ---------------------------------------------------------------------------


def get_path(obj: Any, path: JsonPath) -> Any:
    """Return a nested value from a dict/list/tuple structure.

    Args:
        obj: Nested object to inspect.
        path: Sequence of dictionary keys and sequence indexes.

    Returns:
        The nested value, or ``_MISSING`` if the path does not exist.
    """
    current = obj
    for part in path:
        if isinstance(current, dict):
            if part not in current:
                return _MISSING
            current = current[part]
        elif isinstance(current, (list, tuple)) and isinstance(part, int):
            if part >= len(current) or part < -len(current):
                return _MISSING
            current = current[part]
        else:
            return _MISSING
    return current


def plotly_cleaned_spec(fig: go.Figure) -> dict[str, Any]:
    """Return the Plotly-encoder-cleaned JSON-compatible figure spec.

    Args:
        fig: Figure whose raw spec may contain non-JSON-native values.

    Returns:
        Decoded JSON-compatible spec produced by ``PlotlyJSONEncoder``.
    """
    return json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder))


def assert_plotly_encoder_accepts_case(case: SerializationCase) -> None:
    """Assert that Plotly's JSON encoder accepts a value/location case.

    Args:
        case: Value/location pair under test.
    """
    fig = case.location.build(case.value.make())
    raw_spec = fig.to_dict()
    raw_value = get_path(raw_spec, case.location.path)

    assert raw_value is not _MISSING
    assert case.value.raw_predicate(raw_value), repr(raw_value)

    cleaned_spec = plotly_cleaned_spec(fig)
    encoded_value = get_path(cleaned_spec, case.location.path)

    assert encoded_value is not _MISSING
    assert case.value.encoded_predicate(encoded_value), repr(encoded_value)


def _flat_values(value: Any) -> list[Any]:
    """Return a best-effort flat list of scalar values from a container.

    Args:
        value: Scalar or container produced by Plotly figure construction.

    Returns:
        Flat list of items for predicate checks.
    """
    if isinstance(value, pd.Series):
        return list(value.array)
    if isinstance(value, pd.Categorical):
        return list(value)
    if isinstance(value, pd.Index):
        return list(value)
    if isinstance(value, np.ndarray):
        return list(value.ravel())
    if isinstance(value, (list, tuple)):
        items: list[Any] = []
        for item in value:
            if isinstance(
                item,
                (list, tuple, np.ndarray, pd.Series, pd.Index, pd.Categorical),
            ):
                items.extend(_flat_values(item))
            else:
                items.append(item)
        return items
    return [value]


def _is_nan(value: Any) -> bool:
    """Return whether a value behaves like floating NaN.

    Args:
        value: Value to inspect.

    Returns:
        True if ``math.isnan`` accepts the value and reports NaN.
    """
    try:
        return math.isnan(value)
    except TypeError:
        return False


def _is_non_finite_float(value: Any) -> bool:
    """Return whether a value is a non-finite float.

    Args:
        value: Value to inspect.

    Returns:
        True for NaN, positive infinity, and negative infinity.
    """
    return isinstance(value, float) and not math.isfinite(value)


def _is_iso_string_with(prefix: str) -> Callable[[Any], bool]:
    """Build a predicate that checks an encoded ISO-like string prefix.

    Args:
        prefix: Prefix expected in the encoded JSON value.

    Returns:
        Predicate accepting the decoded JSON value.
    """
    return lambda value: isinstance(value, str) and value.startswith(prefix)


def _is_number_close(expected: float) -> Callable[[Any], bool]:
    """Build a predicate that checks a decoded JSON number approximately.

    Args:
        expected: Expected numeric value.

    Returns:
        Predicate accepting the decoded JSON value.
    """
    return lambda value: isinstance(value, (int, float)) and math.isclose(
        value,
        expected,
    )


def _is_json_null(value: Any) -> bool:
    """Return whether a decoded JSON value is null.

    Args:
        value: Decoded JSON value.

    Returns:
        True if the decoded value is ``None``.
    """
    return value is None


def _is_datetime_container(value: Any) -> bool:
    """Return whether a value is a datetime-like container.

    Args:
        value: Value to inspect.

    Returns:
        True for Plotly 5 and Plotly 6 datetime-container representations.
    """
    if isinstance(value, pd.Series):
        return pd.api.types.is_datetime64_any_dtype(value.dtype)
    if isinstance(value, pd.DatetimeIndex):
        return True
    if isinstance(value, np.ndarray):
        if np.issubdtype(value.dtype, np.datetime64):
            return True
        if value.dtype == object:
            return any(isinstance(item, dt.datetime) for item in value.ravel())
    return False


def _container_has_type(*types_: type[Any]) -> Callable[[Any], bool]:
    """Build a predicate for containers containing requested item types.

    Args:
        *types_: Types expected to occur inside the container.

    Returns:
        Predicate accepting the raw figure-spec value.
    """

    def predicate(value: Any) -> bool:
        values = _flat_values(value)
        return all(any(isinstance(item, type_) for item in values) for type_ in types_)

    return predicate


def _is_nullable_int_container(value: Any) -> bool:
    """Return whether a value is a nullable-integer container or equivalent.

    Args:
        value: Value to inspect.

    Returns:
        True for pandas nullable integer containers and Plotly-normalized
        numeric-array equivalents, including float arrays containing NaN.
    """
    if isinstance(value, pd.Series) and str(value.dtype) == "Int64":
        return True
    if isinstance(value, dict) and {"dtype", "bdata"}.issubset(value):
        return True
    if isinstance(value, np.ndarray):
        return value.size > 0 and any(_is_nan(item) for item in value.ravel())
    values = _flat_values(value)
    return bool(values) and any(item is pd.NA or _is_nan(item) for item in values)


def _is_categorical_or_equivalent(value: Any) -> bool:
    """Return whether a value is a categorical container or equivalent.

    Args:
        value: Value to inspect.

    Returns:
        True for pandas ``Categorical`` values and Plotly-normalized category
        sequences preserving at least one string and one missing value.
    """
    if isinstance(value, pd.Categorical):
        return True
    values = _flat_values(value)
    return any(isinstance(item, str) for item in values) and any(
        item is None or _is_nan(item) for item in values
    )


def _is_decoded_list_with_prefix(prefix: str) -> Callable[[Any], bool]:
    """Build a predicate for decoded JSON lists of ISO-like strings.

    Args:
        prefix: Prefix expected in at least one decoded string value.

    Returns:
        Predicate accepting the decoded JSON value.
    """
    return lambda value: isinstance(value, list) and any(
        isinstance(item, str) and item.startswith(prefix) for item in value
    )


def _is_decoded_sequence_containing_null(value: Any) -> bool:
    """Return whether a decoded JSON sequence contains null.

    Args:
        value: Decoded JSON value.

    Returns:
        True if the value is a list and contains ``None``.
    """
    return isinstance(value, list) and any(item is None for item in value)


def _is_decoded_list_of_numbers(value: Any) -> bool:
    """Return whether a decoded JSON value is a list containing numbers.

    Args:
        value: Decoded JSON value.

    Returns:
        True if the value is a non-empty list of JSON numeric values.
    """
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, (int, float)) for item in value
    )


def _is_decoded_nullable_int(value: Any) -> bool:
    """Return whether a decoded value represents nullable integer data.

    Args:
        value: Decoded JSON value.

    Returns:
        True for list-with-null encodings and recent typed-array encodings.
    """
    return _is_decoded_sequence_containing_null(value) or (
        isinstance(value, dict) and {"dtype", "bdata"}.issubset(value)
    )


# ---------------------------------------------------------------------------
# Value cases
# ---------------------------------------------------------------------------


DECIMAL = ValueCase(
    "decimal.Decimal",
    lambda: decimal.Decimal("12.34"),
    lambda value: isinstance(value, decimal.Decimal),
    _is_number_close(12.34),
)
TIMESTAMP = ValueCase(
    "pandas.Timestamp",
    lambda: pd.Timestamp("2026-01-02 03:04:05"),
    lambda value: isinstance(value, pd.Timestamp),
    _is_iso_string_with("2026-01-02T03:04:05"),
)
TIMESTAMP_TZ = ValueCase(
    "pandas.Timestamp.tz_aware",
    lambda: pd.Timestamp("2026-01-02 03:04:05", tz="UTC"),
    lambda value: isinstance(value, pd.Timestamp),
    _is_iso_string_with("2026-01-02T03:04:05+00:00"),
)
PANDAS_NAT = ValueCase(
    "pandas.NaT",
    lambda: pd.NaT,
    lambda value: value is pd.NaT,
    _is_json_null,
)
PANDAS_NA = ValueCase(
    "pandas.NA",
    lambda: pd.NA,
    lambda value: value is pd.NA,
    _is_json_null,
)
PANDAS_TIMEDELTA = ValueCase(
    "pandas.Timedelta",
    lambda: pd.Timedelta("2 days 03:04:05"),
    lambda value: isinstance(value, pd.Timedelta),
    _is_iso_string_with("P2DT3H4M5S"),
)
NUMPY_DATETIME64 = ValueCase(
    "numpy.datetime64",
    lambda: np.datetime64("2026-01-02T03:04:05"),
    lambda value: isinstance(value, np.datetime64),
    _is_iso_string_with("2026-01-02T03:04:05"),
)
NUMPY_INT64 = ValueCase(
    "numpy.int64",
    lambda: np.int64(_EXPECTED_INT),
    lambda value: isinstance(value, np.integer),
    lambda value: value == _EXPECTED_INT,
)
NUMPY_UINT64 = ValueCase(
    "numpy.uint64",
    lambda: np.uint64(_EXPECTED_INT),
    lambda value: isinstance(value, np.unsignedinteger),
    lambda value: value == _EXPECTED_INT,
)
NUMPY_FLOAT32 = ValueCase(
    "numpy.float32",
    lambda: np.float32(12.5),
    lambda value: isinstance(value, np.floating),
    _is_number_close(12.5),
)
NUMPY_BOOL = ValueCase(
    "numpy.bool_",
    lambda: np.bool_(1),
    lambda value: isinstance(value, np.bool_),
    lambda value: value is True,
)
FLOAT_NAN = ValueCase("float.nan", lambda: float("nan"), _is_nan, _is_json_null)
FLOAT_INF = ValueCase(
    "float.inf",
    lambda: float("inf"),
    _is_non_finite_float,
    _is_json_null,
)
DATETIME = ValueCase(
    "datetime.datetime",
    lambda: dt.datetime(2026, 1, 2, 3, 4, 5),  # noqa: DTZ001
    lambda value: isinstance(value, dt.datetime),
    _is_iso_string_with("2026-01-02T03:04:05"),
)
DATE = ValueCase(
    "datetime.date",
    lambda: dt.date(2026, 1, 2),
    lambda value: isinstance(value, dt.date) and not isinstance(value, dt.datetime),
    _is_iso_string_with("2026-01-02"),
)
TIME = ValueCase(
    "datetime.time",
    lambda: dt.time(3, 4, 5),
    lambda value: isinstance(value, dt.time),
    _is_iso_string_with("03:04:05"),
)


# ---------------------------------------------------------------------------
# Figure locations
# ---------------------------------------------------------------------------


SCATTER_X = FigureLocationCase(
    "scatter.x[0]",
    lambda value: go.Figure(go.Scatter(x=[value, 2], y=[1, 2])),
    ("data", 0, "x", 0),
)
SCATTER_Y = FigureLocationCase(
    "scatter.y[0]",
    lambda value: go.Figure(go.Scatter(x=[1, 2], y=[value, 2])),
    ("data", 0, "y", 0),
)
SCATTER3D_X = FigureLocationCase(
    "scatter3d.x[0]",
    lambda value: go.Figure(go.Scatter3d(x=[value, 2], y=[1, 2], z=[1, 2])),
    ("data", 0, "x", 0),
)
SCATTER3D_Y = FigureLocationCase(
    "scatter3d.y[0]",
    lambda value: go.Figure(go.Scatter3d(x=[1, 2], y=[value, 2], z=[1, 2])),
    ("data", 0, "y", 0),
)
SCATTER3D_Z = FigureLocationCase(
    "scatter3d.z[0]",
    lambda value: go.Figure(go.Scatter3d(x=[1, 2], y=[1, 2], z=[value, 2])),
    ("data", 0, "z", 0),
)
HEATMAP_Z = FigureLocationCase(
    "heatmap.z[0][0]",
    lambda value: go.Figure(go.Heatmap(z=[[value, 2], [3, 4]])),
    ("data", 0, "z", 0, 0),
)
SURFACE_Z = FigureLocationCase(
    "surface.z[0][0]",
    lambda value: go.Figure(go.Surface(z=[[value, 2], [3, 4]])),
    ("data", 0, "z", 0, 0),
)
CUSTOMDATA = FigureLocationCase(
    "trace.customdata[0][0]",
    lambda value: go.Figure(go.Scatter(x=[1], y=[1], customdata=[[value]])),
    ("data", 0, "customdata", 0, 0),
)
TRACE_META = FigureLocationCase(
    "trace.meta.special",
    lambda value: go.Figure(go.Scatter(x=[1], y=[1], meta={"special": value})),
    ("data", 0, "meta", "special"),
)
LAYOUT_META = FigureLocationCase(
    "layout.meta.special",
    lambda value: go.Figure(go.Scatter(x=[1], y=[1])).update_layout(
        meta={"special": value},
    ),
    ("layout", "meta", "special"),
)
ANNOTATION_X = FigureLocationCase(
    "layout.annotation.x",
    lambda value: go.Figure(go.Scatter(x=[1], y=[1])).add_annotation(
        x=value,
        y=1,
        text="annotation",
    ),
    ("layout", "annotations", 0, "x"),
)
ANNOTATION_Y = FigureLocationCase(
    "layout.annotation.y",
    lambda value: go.Figure(go.Scatter(x=[1], y=[1])).add_annotation(
        x=1,
        y=value,
        text="annotation",
    ),
    ("layout", "annotations", 0, "y"),
)
SCENE_ANNOTATION_X = FigureLocationCase(
    "layout.scene.annotation.x",
    lambda value: go.Figure(go.Scatter3d(x=[1], y=[1], z=[1])).update_layout(
        scene={"annotations": [{"x": value, "y": 1, "z": 1, "text": "annotation"}]},
    ),
    ("layout", "scene", "annotations", 0, "x"),
)
SCENE_ANNOTATION_Y = FigureLocationCase(
    "layout.scene.annotation.y",
    lambda value: go.Figure(go.Scatter3d(x=[1], y=[1], z=[1])).update_layout(
        scene={"annotations": [{"x": 1, "y": value, "z": 1, "text": "annotation"}]},
    ),
    ("layout", "scene", "annotations", 0, "y"),
)
SCENE_ANNOTATION_Z = FigureLocationCase(
    "layout.scene.annotation.z",
    lambda value: go.Figure(go.Scatter3d(x=[1], y=[1], z=[1])).update_layout(
        scene={"annotations": [{"x": 1, "y": 1, "z": value, "text": "annotation"}]},
    ),
    ("layout", "scene", "annotations", 0, "z"),
)
SHAPE_X0 = FigureLocationCase(
    "layout.shape.x0",
    lambda value: go.Figure(go.Scatter(x=[1, 2], y=[1, 2])).add_shape(
        type="line",
        x0=value,
        x1=2,
        y0=0,
        y1=1,
    ),
    ("layout", "shapes", 0, "x0"),
)
SHAPE_X1 = FigureLocationCase(
    "layout.shape.x1",
    lambda value: go.Figure(go.Scatter(x=[1, 2], y=[1, 2])).add_shape(
        type="line",
        x0=1,
        x1=value,
        y0=0,
        y1=1,
    ),
    ("layout", "shapes", 0, "x1"),
)
SHAPE_Y0 = FigureLocationCase(
    "layout.shape.y0",
    lambda value: go.Figure(go.Scatter(x=[1, 2], y=[1, 2])).add_shape(
        type="line",
        x0=1,
        x1=2,
        y0=value,
        y1=1,
    ),
    ("layout", "shapes", 0, "y0"),
)
SHAPE_Y1 = FigureLocationCase(
    "layout.shape.y1",
    lambda value: go.Figure(go.Scatter(x=[1, 2], y=[1, 2])).add_shape(
        type="line",
        x0=1,
        x1=2,
        y0=0,
        y1=value,
    ),
    ("layout", "shapes", 0, "y1"),
)
XAXIS_RANGE = FigureLocationCase(
    "layout.xaxis.range[0]",
    lambda value: go.Figure(go.Scatter(x=[1, 2], y=[1, 2])).update_layout(
        xaxis_range=[value, value],
    ),
    ("layout", "xaxis", "range", 0),
)
YAXIS_RANGE = FigureLocationCase(
    "layout.yaxis.range[0]",
    lambda value: go.Figure(go.Scatter(x=[1, 2], y=[1, 2])).update_layout(
        yaxis_range=[value, value],
    ),
    ("layout", "yaxis", "range", 0),
)
XAXIS_TICKVAL = FigureLocationCase(
    "layout.xaxis.tickvals[0]",
    lambda value: go.Figure(go.Scatter(x=[1, 2], y=[1, 2])).update_layout(
        xaxis_tickvals=[value],
    ),
    ("layout", "xaxis", "tickvals", 0),
)
YAXIS_TICKVAL = FigureLocationCase(
    "layout.yaxis.tickvals[0]",
    lambda value: go.Figure(go.Scatter(x=[1, 2], y=[1, 2])).update_layout(
        yaxis_tickvals=[value],
    ),
    ("layout", "yaxis", "tickvals", 0),
)
SCENE_XAXIS_RANGE = FigureLocationCase(
    "layout.scene.xaxis.range[0]",
    lambda value: go.Figure(
        go.Scatter3d(x=[1, 2], y=[1, 2], z=[1, 2]),
    ).update_layout(scene={"xaxis": {"range": [value, value]}}),
    ("layout", "scene", "xaxis", "range", 0),
)
SCENE_YAXIS_RANGE = FigureLocationCase(
    "layout.scene.yaxis.range[0]",
    lambda value: go.Figure(
        go.Scatter3d(x=[1, 2], y=[1, 2], z=[1, 2]),
    ).update_layout(scene={"yaxis": {"range": [value, value]}}),
    ("layout", "scene", "yaxis", "range", 0),
)
SCENE_ZAXIS_RANGE = FigureLocationCase(
    "layout.scene.zaxis.range[0]",
    lambda value: go.Figure(
        go.Scatter3d(x=[1, 2], y=[1, 2], z=[1, 2]),
    ).update_layout(scene={"zaxis": {"range": [value, value]}}),
    ("layout", "scene", "zaxis", "range", 0),
)

DATA_AND_LAYOUT_LOCATIONS = [
    SCATTER_X,
    SCATTER_Y,
    SCATTER3D_X,
    SCATTER3D_Y,
    SCATTER3D_Z,
    HEATMAP_Z,
    SURFACE_Z,
    CUSTOMDATA,
    TRACE_META,
    LAYOUT_META,
    ANNOTATION_X,
    ANNOTATION_Y,
    SCENE_ANNOTATION_X,
    SCENE_ANNOTATION_Y,
    SCENE_ANNOTATION_Z,
    SHAPE_X0,
    SHAPE_X1,
    SHAPE_Y0,
    SHAPE_Y1,
]
METADATA_AND_ANNOTATION_LOCATIONS = [
    TRACE_META,
    LAYOUT_META,
    ANNOTATION_X,
    ANNOTATION_Y,
    SCENE_ANNOTATION_X,
    SCENE_ANNOTATION_Y,
    SCENE_ANNOTATION_Z,
]
RANGE_LOCATIONS = [
    XAXIS_RANGE,
    YAXIS_RANGE,
    XAXIS_TICKVAL,
    YAXIS_TICKVAL,
    SCENE_XAXIS_RANGE,
    SCENE_YAXIS_RANGE,
    SCENE_ZAXIS_RANGE,
]


def _make_cases(
    values: list[ValueCase],
    locations: list[FigureLocationCase],
) -> list[SerializationCase]:
    """Build value/location cases for pytest parametrization.

    Args:
        values: Values to combine with each provided location.
        locations: Figure-spec locations to combine with each provided value.

    Returns:
        List of value/location serialization cases.
    """
    return [
        SerializationCase(value=value, location=location)
        for value in values
        for location in locations
    ]


SUPPORTED_SCALAR_CASES = [
    *_make_cases(
        [
            DECIMAL,
            TIMESTAMP,
            TIMESTAMP_TZ,
            PANDAS_NAT,
            PANDAS_NA,
            PANDAS_TIMEDELTA,
            FLOAT_NAN,
            FLOAT_INF,
            DATETIME,
            DATE,
            TIME,
        ],
        DATA_AND_LAYOUT_LOCATIONS,
    ),
    *_make_cases(
        [NUMPY_DATETIME64, NUMPY_INT64, NUMPY_UINT64, NUMPY_FLOAT32, NUMPY_BOOL],
        METADATA_AND_ANNOTATION_LOCATIONS,
    ),
    *_make_cases([DECIMAL, TIMESTAMP, TIMESTAMP_TZ, DATETIME, DATE], RANGE_LOCATIONS),
]


# ---------------------------------------------------------------------------
# Container cases
# ---------------------------------------------------------------------------


DATETIME_SERIES = ValueCase(
    "Series[datetime64]",
    lambda: pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"])),
    _is_datetime_container,
    _is_decoded_list_with_prefix("2026-01-01"),
)
DATETIME_INDEX = ValueCase(
    "DatetimeIndex",
    lambda: pd.DatetimeIndex(["2026-01-01", "2026-01-02"]),
    _is_datetime_container,
    _is_decoded_list_with_prefix("2026-01-01"),
)
NDARRAY_DATETIME64 = ValueCase(
    "ndarray[datetime64]",
    lambda: np.array(["2026-01-01", "2026-01-02"], dtype="datetime64[ns]"),
    _is_datetime_container,
    _is_decoded_list_with_prefix("2026-01-01"),
)
OBJECT_ARRAY_TIMESTAMP = ValueCase(
    "ndarray[object_Timestamp]",
    lambda: np.array(
        [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02")],
        dtype=object,
    ),
    _container_has_type(pd.Timestamp),
    _is_decoded_list_with_prefix("2026-01-01"),
)
SERIES_DECIMAL = ValueCase(
    "Series[object_Decimal]",
    lambda: pd.Series([decimal.Decimal("1.1"), decimal.Decimal("2.2")]),
    _container_has_type(decimal.Decimal),
    _is_decoded_list_of_numbers,
)
SERIES_BOOLEAN_NA = ValueCase(
    "Series[boolean_with_NA]",
    lambda: pd.Series([True, pd.NA], dtype="boolean"),
    _container_has_type(type(pd.NA)),
    _is_decoded_sequence_containing_null,
)
SERIES_STRING_NA = ValueCase(
    "Series[string_with_NA]",
    lambda: pd.Series(["a", pd.NA], dtype="string"),
    _container_has_type(type(pd.NA)),
    _is_decoded_sequence_containing_null,
)
SERIES_INT64_NA = ValueCase(
    "Series[Int64_with_NA]",
    lambda: pd.Series([1, pd.NA], dtype="Int64"),
    _is_nullable_int_container,
    _is_decoded_nullable_int,
)
CATEGORICAL = ValueCase(
    "pandas.Categorical",
    lambda: pd.Categorical(["a", None, "b"]),
    _is_categorical_or_equivalent,
    _is_decoded_sequence_containing_null,
)

CONTAINER_X = FigureLocationCase(
    "scatter.x",
    lambda value: go.Figure(go.Scatter(x=value, y=[1, 2, 3][: len(value)])),
    ("data", 0, "x"),
)
CONTAINER_Y = FigureLocationCase(
    "scatter.y",
    lambda value: go.Figure(go.Scatter(x=list(range(1, len(value) + 1)), y=value)),
    ("data", 0, "y"),
)
CONTAINER_Z3D = FigureLocationCase(
    "scatter3d.z",
    lambda value: go.Figure(
        go.Scatter3d(x=list(range(1, len(value) + 1)), y=[1] * len(value), z=value),
    ),
    ("data", 0, "z"),
)
CONTAINER_CUSTOMDATA = FigureLocationCase(
    "trace.customdata",
    lambda value: go.Figure(
        go.Scatter(
            x=list(range(1, len(value) + 1)),
            y=[1] * len(value),
            customdata=value,
        ),
    ),
    ("data", 0, "customdata"),
)
CONTAINER_TRACE_META = FigureLocationCase(
    "trace.meta.special",
    lambda value: go.Figure(go.Scatter(x=[1], y=[1], meta={"special": value})),
    ("data", 0, "meta", "special"),
)
CONTAINER_LAYOUT_META = FigureLocationCase(
    "layout.meta.special",
    lambda value: go.Figure(go.Scatter(x=[1], y=[1])).update_layout(
        meta={"special": value},
    ),
    ("layout", "meta", "special"),
)

SUPPORTED_CONTAINER_CASES = _make_cases(
    [
        DATETIME_SERIES,
        DATETIME_INDEX,
        NDARRAY_DATETIME64,
        OBJECT_ARRAY_TIMESTAMP,
        SERIES_DECIMAL,
        SERIES_BOOLEAN_NA,
        SERIES_STRING_NA,
        SERIES_INT64_NA,
        CATEGORICAL,
    ],
    [
        CONTAINER_X,
        CONTAINER_Y,
        CONTAINER_Z3D,
        CONTAINER_CUSTOMDATA,
        CONTAINER_TRACE_META,
        CONTAINER_LAYOUT_META,
    ],
)

UNSUPPORTED_CASES = [
    UnsupportedCase("numpy.timedelta64", lambda: np.timedelta64(2, "D")),
    UnsupportedCase("datetime.timedelta", lambda: dt.timedelta(days=2, seconds=3)),
    UnsupportedCase("pandas.Period", lambda: pd.Period("2026-01", freq="M")),
    UnsupportedCase("pandas.Interval", lambda: pd.Interval(1, 2)),
    UnsupportedCase("python.complex", lambda: complex(1, 2)),
    UnsupportedCase("numpy.complex128", lambda: np.complex128(1 + 2j)),
]
