import re
import sys
from html.parser import HTMLParser
from importlib.util import find_spec

import logistro
import pytest

from kaleido import PageGenerator
from kaleido._page_generator import DEFAULT_MATHJAX, DEFAULT_PLOTLY

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")

_logger = logistro.getLogger(__name__)


# Expected boilerplate HTML (without script tags with src)
EXPECTED_BOILERPLATE = """<!DOCTYPE html>
<html>
    <head>
        <style id="head-style"></style>
        <title>Kaleido-fier</title>
        <script>
          window.PlotlyConfig = {MathJaxConfig: 'local'}
        </script>
        <script type="text/x-mathjax-config">
          MathJax.Hub.Config({ "SVG": { blacker: 0 }})
        </script>

    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido-image" /></body>
</html>"""


# Claude, please review this for obvious errors.
class HTMLAnalyzer(HTMLParser):
    """Extract script tags with src attributes and return HTML without them."""

    def __init__(self):
        super().__init__()
        self.scripts = []
        self.boilerplate = []
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        if tag == "script" and "src" in (attr_dict := dict(attrs)):
            self._in_script = True
            self.scripts.append(attr_dict["src"])
            return
        self.boilerplate.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self._in_script and tag == "script":
            self._in_script = False
            return
        self.boilerplate.append(f"</{tag}>")

    def handle_data(self, data):
        if not self._in_script:
            self.boilerplate.append(data)


def normalize_whitespace(html):
    """Normalize whitespace by collapsing multiple newlines and extra spaces."""
    # Collapse multiple newlines to single newlines
    html = re.sub(r"\n\s*\n", "\n", html)
    # Remove extra whitespace between tags
    html = re.sub(r">\s*<", "><", html)
    return html.strip()


# Create boilerplate reference by parsing expected HTML
_reference_analyzer = HTMLAnalyzer()
_reference_analyzer.feed(EXPECTED_BOILERPLATE)
_REFERENCE_BOILERPLATE = normalize_whitespace("".join(_reference_analyzer.boilerplate))


def get_scripts_from_html(generated_html):
    """
    Parse generated HTML, assert boilerplate matches reference, and return script URLs.

    Returns:
        list: script src URLs found in generated HTML
    """
    analyzer = HTMLAnalyzer()
    analyzer.feed(generated_html)

    generated_boilerplate = normalize_whitespace("".join(analyzer.boilerplate))

    # Assert boilerplate matches with diff on failure
    assert generated_boilerplate == _REFERENCE_BOILERPLATE, (
        f"Boilerplate mismatch:\n"
        f"Expected:\n{_REFERENCE_BOILERPLATE}\n\n"
        f"Got:\n{generated_boilerplate}"
    )

    return analyzer.scripts


@pytest.mark.order(1)
async def test_page_generator():
    if not find_spec("plotly"):
        raise ImportError(
            "Tests must be run with plotly installed to function",
        )
    old_path = sys.path
    sys.path = sys.path[:1]
    if find_spec("plotly"):
        raise RuntimeError(
            "Plotly cannot be imported during this test, "
            "as this tests default behavior while trying to import plotly. "
            "The best solution is to make sure this test always runs first, "
            "or if you really need to, run it separately and then skip it "
            "in the main group.",
        )

    # Test no imports (plotly not available)
    no_imports = PageGenerator().generate_index()
    scripts = get_scripts_from_html(no_imports)

    # Should have mathjax, plotly default, and kaleido_scopes
    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == DEFAULT_MATHJAX
    assert scripts[1] == DEFAULT_PLOTLY
    assert scripts[2].endswith("kaleido_scopes.js")

    sys.path = old_path

    # Test all defaults (plotly available)
    all_defaults = PageGenerator().generate_index()
    scripts = get_scripts_from_html(all_defaults)

    # Should have mathjax, plotly package data, and kaleido_scopes
    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == DEFAULT_MATHJAX
    assert scripts[1].endswith("package_data/plotly.min.js")
    assert scripts[2].endswith("kaleido_scopes.js")

    # Test with custom plotly
    with_plot = PageGenerator(plotly="https://with_plot").generate_index()
    scripts = get_scripts_from_html(with_plot)

    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == DEFAULT_MATHJAX
    assert scripts[1] == "https://with_plot"
    assert scripts[2].endswith("kaleido_scopes.js")

    # Test without mathjax
    without_math = PageGenerator(
        plotly="https://with_plot",
        mathjax=False,
    ).generate_index()
    scripts = get_scripts_from_html(without_math)

    assert len(scripts) == 2  # noqa: PLR2004
    assert scripts[0] == "https://with_plot"
    assert scripts[1].endswith("kaleido_scopes.js")

    # Test with custom mathjax and others
    with_others = PageGenerator(
        plotly="https://with_plot",
        mathjax="https://with_mathjax",
        others=["https://1", "https://2"],
    ).generate_index()
    scripts = get_scripts_from_html(with_others)

    assert len(scripts) == 5  # noqa: PLR2004
    assert scripts[0] == "https://with_mathjax"
    assert scripts[1] == "https://with_plot"
    assert scripts[2] == "https://1"
    assert scripts[3] == "https://2"
    assert scripts[4].endswith("kaleido_scopes.js")
