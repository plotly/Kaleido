from choreographer.errors import DevtoolsProtocolError


class JavascriptError(RuntimeError):  # TODO(AJP): process better
    """Used to report errors from javascript."""


### Error definitions ###
class KaleidoError(Exception):
    """
    An error to interpret errors from Kaleido's JS side.

    This is not for all js errors, just kaleido_scopes.js errors.
    """

    def __init__(self, code, message):
        """
        Construct an error object.

        Args:
            code: the number code of the error.
            message: the message of the error.

        """
        super().__init__(message)
        self._code = code
        self._message = message

    def __str__(self):
        """Display the KaleidoError nicely."""
        return f"Error {self._code}: {self._message}"


def _get_error(result):
    """Check browser response for errors. Helper function."""
    if "error" in result:
        return DevtoolsProtocolError(result)
    if result.get("result", {}).get("result", {}).get("subtype", None) == "error":
        return JavascriptError(str(result.get("result")))
    return None


def _raise_error(result):
    e = _get_error(result)
    if e:
        raise e
