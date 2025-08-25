import re
import sys
import tempfile
from html.parser import HTMLParser
from importlib.util import find_spec
from pathlib import Path

import logistro
import pytest
from hypothesis import given
from hypothesis import strategies as st

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


# Fixtures for user supplied input scenarios
@pytest.fixture
def temp_js_file():
    """Create a temporary JavaScript file that exists."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write("console.log('test');")
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


@pytest.fixture
def existing_file_path():
    """Return path to current test file (guaranteed to exist)."""
    return Path(__file__)


@pytest.fixture
def nonexistent_file_path():
    """Return path to file that doesn't exist."""
    return Path("/nonexistent/path/file.js")


@pytest.fixture
def user_input_scenarios():
    """Fixture for user supplied input scenarios using hypothesis strategies."""

    # Generate sample data using hypothesis strategies
    http_urls = st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "And")),
    ).map(lambda x: f"https://example.com/{x}.js")

    return {
        "custom_plotly_url": http_urls.example(),
        "custom_mathjax_url": http_urls.example(),
        "other_scripts": [
            http_urls.example(),
            http_urls.example(),
        ],
        "plotly_with_encoding": (http_urls.example(), "utf-8"),
        "mathjax_with_encoding": (http_urls.example(), "utf-16"),
    }


@pytest.fixture
def hypothesis_urls():
    """Generate hypothesis-based URL strategies."""
    return st.text(min_size=1, max_size=20).map(lambda x: f"https://example.com/{x}.js")


@pytest.fixture
def hypothesis_encodings():
    """Generate hypothesis-based encoding strategies."""
    return st.sampled_from(["utf-8", "utf-16", "ascii", "latin1"])


@pytest.fixture
def hypothesis_tuples(hypothesis_urls, hypothesis_encodings):
    """Generate hypothesis-based (url, encoding) tuples."""
    return st.tuples(hypothesis_urls, hypothesis_encodings)


# Test default combinations
@pytest.mark.order(1)
async def test_defaults_no_plotly_available():
    """Test defaults when plotly package is not available."""
    if not find_spec("plotly"):
        raise ImportError("Tests must be run with plotly installed to function")

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


async def test_defaults_with_plotly_available():
    """Test defaults when plotly package is available."""
    all_defaults = PageGenerator().generate_index()
    scripts = get_scripts_from_html(all_defaults)

    # Should have mathjax, plotly package data, and kaleido_scopes
    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == DEFAULT_MATHJAX
    assert scripts[1].endswith("package_data/plotly.min.js")
    assert scripts[2].endswith("kaleido_scopes.js")


async def test_force_cdn():
    """Test force_cdn=True forces use of CDN plotly even when plotly is available."""
    # Verify plotly is available first
    if not find_spec("plotly"):
        pytest.skip("Plotly not available - cannot test force_cdn override")

    forced_cdn = PageGenerator(force_cdn=True).generate_index()
    scripts = get_scripts_from_html(forced_cdn)

    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == DEFAULT_MATHJAX
    assert scripts[1] == DEFAULT_PLOTLY
    assert scripts[2].endswith("kaleido_scopes.js")


# Test boolean mathjax functionality
async def test_mathjax_false():
    """Test that mathjax=False disables mathjax."""
    without_mathjax = PageGenerator(mathjax=False).generate_index()
    scripts = get_scripts_from_html(without_mathjax)

    assert len(scripts) == 2  # noqa: PLR2004
    assert scripts[0].endswith("package_data/plotly.min.js")
    assert scripts[1].endswith("kaleido_scopes.js")


# Test user overrides
async def test_custom_plotly_url(user_input_scenarios):
    """Test custom plotly URL override."""
    custom_plotly = user_input_scenarios["custom_plotly_url"]
    with_custom = PageGenerator(plotly=custom_plotly).generate_index()
    scripts = get_scripts_from_html(with_custom)

    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == DEFAULT_MATHJAX
    assert scripts[1] == custom_plotly
    assert scripts[2].endswith("kaleido_scopes.js")


async def test_custom_mathjax_url(user_input_scenarios):
    """Test custom mathjax URL override."""
    custom_mathjax = user_input_scenarios["custom_mathjax_url"]
    with_custom = PageGenerator(mathjax=custom_mathjax).generate_index()
    scripts = get_scripts_from_html(with_custom)

    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == custom_mathjax
    assert scripts[1].endswith("package_data/plotly.min.js")
    assert scripts[2].endswith("kaleido_scopes.js")


async def test_other_scripts(user_input_scenarios):
    """Test adding other scripts."""
    other_scripts = user_input_scenarios["other_scripts"]
    with_others = PageGenerator(others=other_scripts).generate_index()
    scripts = get_scripts_from_html(with_others)

    assert len(scripts) == 5  # noqa: PLR2004
    assert scripts[0] == DEFAULT_MATHJAX
    assert scripts[1].endswith("package_data/plotly.min.js")
    assert scripts[2] == other_scripts[0]
    assert scripts[3] == other_scripts[1]
    assert scripts[4].endswith("kaleido_scopes.js")


async def test_combined_overrides(user_input_scenarios):
    """Test combination of multiple overrides."""
    custom_plotly = user_input_scenarios["custom_plotly_url"]
    custom_mathjax = user_input_scenarios["custom_mathjax_url"]
    other_scripts = user_input_scenarios["other_scripts"]

    combined = PageGenerator(
        plotly=custom_plotly,
        mathjax=custom_mathjax,
        others=other_scripts,
    ).generate_index()
    scripts = get_scripts_from_html(combined)

    assert len(scripts) == 5  # noqa: PLR2004
    assert scripts[0] == custom_mathjax
    assert scripts[1] == custom_plotly
    assert scripts[2] == other_scripts[0]
    assert scripts[3] == other_scripts[1]
    assert scripts[4].endswith("kaleido_scopes.js")


# Test file path validation
async def test_existing_file_path(temp_js_file):
    """Test that existing file paths work with and without file:/// protocol."""
    # Test with regular path
    generator = PageGenerator(plotly=str(temp_js_file))
    html = generator.generate_index()
    scripts = get_scripts_from_html(html)
    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == DEFAULT_MATHJAX
    assert scripts[1] == str(temp_js_file)
    assert scripts[2].endswith("kaleido_scopes.js")

    # Test with file:/// protocol
    generator_uri = PageGenerator(plotly=temp_js_file.as_uri())
    html_uri = generator_uri.generate_index()
    scripts_uri = get_scripts_from_html(html_uri)
    assert len(scripts_uri) == 3  # noqa: PLR2004
    assert scripts_uri[0] == DEFAULT_MATHJAX
    assert scripts_uri[1] == temp_js_file.as_uri()
    assert scripts_uri[2].endswith("kaleido_scopes.js")


async def test_nonexistent_file_path_raises_error(nonexistent_file_path):
    """Test that nonexistent file paths raise FileNotFoundError."""
    # Test with regular path
    with pytest.raises(FileNotFoundError):
        PageGenerator(plotly=str(nonexistent_file_path))

    # Test with file:/// protocol
    with pytest.raises(FileNotFoundError):
        PageGenerator(plotly=nonexistent_file_path.as_uri())


async def test_mathjax_nonexistent_file_raises_error(nonexistent_file_path):
    """Test that nonexistent mathjax file raises FileNotFoundError."""
    # Test with regular path
    with pytest.raises(FileNotFoundError):
        PageGenerator(mathjax=str(nonexistent_file_path))

    # Test with file:/// protocol
    with pytest.raises(FileNotFoundError):
        PageGenerator(mathjax=nonexistent_file_path.as_uri())


async def test_others_nonexistent_file_raises_error(nonexistent_file_path):
    """Test that nonexistent file in others list raises FileNotFoundError."""
    # Test with regular path
    with pytest.raises(FileNotFoundError):
        PageGenerator(others=[str(nonexistent_file_path)])

    # Test with file:/// protocol
    with pytest.raises(FileNotFoundError):
        PageGenerator(others=[nonexistent_file_path.as_uri()])


# Test HTTP URLs (should not raise FileNotFoundError)
async def test_http_urls_skip_file_validation():
    """Test that HTTP URLs skip file existence validation."""
    # These should not raise FileNotFoundError even if URLs don't exist
    generator = PageGenerator(
        plotly="https://nonexistent.example.com/plotly.js",
        mathjax="https://nonexistent.example.com/mathjax.js",
        others=["https://nonexistent.example.com/other.js"],
    )
    html = generator.generate_index()
    scripts = get_scripts_from_html(html)

    assert len(scripts) == 4  # noqa: PLR2004
    assert scripts[0] == "https://nonexistent.example.com/mathjax.js"
    assert scripts[1] == "https://nonexistent.example.com/plotly.js"
    assert scripts[2] == "https://nonexistent.example.com/other.js"
    assert scripts[3].endswith("kaleido_scopes.js")


# Test tuple (path, encoding) functionality
async def test_plotly_with_encoding_tuple(user_input_scenarios):
    """Test plotly parameter with (url, encoding) tuple."""
    plotly_tuple = user_input_scenarios["plotly_with_encoding"]
    generator = PageGenerator(plotly=plotly_tuple)
    html = generator.generate_index()
    scripts = get_scripts_from_html(html)

    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == DEFAULT_MATHJAX
    assert scripts[1] == plotly_tuple[0]  # Should be the URL from tuple
    assert scripts[2].endswith("kaleido_scopes.js")


async def test_mathjax_with_encoding_tuple(user_input_scenarios):
    """Test mathjax parameter with (url, encoding) tuple."""
    mathjax_tuple = user_input_scenarios["mathjax_with_encoding"]
    generator = PageGenerator(mathjax=mathjax_tuple)
    html = generator.generate_index()
    scripts = get_scripts_from_html(html)

    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == mathjax_tuple[0]  # Should be the URL from tuple
    assert scripts[1].endswith("package_data/plotly.min.js")
    assert scripts[2].endswith("kaleido_scopes.js")


async def test_others_tuple_error(user_input_scenarios):
    """Test that others parameter with tuples currently fails (documents bug)."""
    # Create a tuple for others list
    url_encoding_tuple = user_input_scenarios["plotly_with_encoding"]

    # This should fail until the others parameter properly handles tuples
    with pytest.raises((TypeError, AttributeError, ValueError)):
        PageGenerator(others=[url_encoding_tuple])


@given(st.text(min_size=1, max_size=10).map(lambda x: f"https://example.com/{x}.js"))
async def test_plotly_urls_hypothesis(url):
    """Test plotly with hypothesis-generated URLs."""
    generator = PageGenerator(plotly=url)
    html = generator.generate_index()
    scripts = get_scripts_from_html(html)

    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == DEFAULT_MATHJAX
    assert scripts[1] == url
    assert scripts[2].endswith("kaleido_scopes.js")


@given(
    st.tuples(
        st.text(min_size=1, max_size=10).map(lambda x: f"https://example.com/{x}.js"),
        st.sampled_from(["utf-8", "utf-16", "ascii"]),
    ),
)
async def test_encoding_tuples_hypothesis(url_encoding_tuple):
    """Test encoding tuples with hypothesis-generated data."""
    url, encoding = url_encoding_tuple

    # Test with plotly
    generator = PageGenerator(plotly=(url, encoding))
    html = generator.generate_index()
    scripts = get_scripts_from_html(html)

    assert len(scripts) == 3  # noqa: PLR2004
    assert scripts[0] == DEFAULT_MATHJAX
    assert scripts[1] == url
    assert scripts[2].endswith("kaleido_scopes.js")

    # Test with mathjax
    generator2 = PageGenerator(mathjax=(url, encoding))
    html2 = generator2.generate_index()
    scripts2 = get_scripts_from_html(html2)

    assert len(scripts2) == 3  # noqa: PLR2004
    assert scripts2[0] == url
    assert scripts2[1].endswith("package_data/plotly.min.js")
    assert scripts2[2].endswith("kaleido_scopes.js")
