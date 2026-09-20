from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Union

try:
    import orjson
except ImportError:  # pragma: no cover - exercised when orjson is unavailable
    orjson = None


def default(obj: Any) -> Any:
    """Fallback for types the active JSON backend can't handle natively."""
    if isinstance(obj, Decimal):
        return float(obj)
    if hasattr(obj, "isoformat"):  # datetime-like, e.g. pandas Timestamp (#458)
        return obj.isoformat()
    if hasattr(obj, "tolist"):
        return obj.tolist()
    raise TypeError(f"Type is not JSON serializable: {type(obj).__name__}")


def dumps(obj: Any) -> str:
    if orjson is not None:
        return orjson.dumps(
            obj,
            default=default,
            option=orjson.OPT_SERIALIZE_NUMPY,
        ).decode()
    return json.dumps(obj, default=default, separators=(",", ":"))


def loads(value: Union[str, bytes, bytearray]) -> Any:
    if orjson is not None:
        return orjson.loads(value)
    return json.loads(value)
