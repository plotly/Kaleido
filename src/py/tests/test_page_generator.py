import re
import sys
from importlib.util import find_spec

import logistro
import pytest

from kaleido import PageGenerator
from kaleido._page_generator import DEFAULT_MATHJAX, DEFAULT_PLOTLY

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")

_logger = logistro.getLogger(__name__)

_re_default_mathjax = re.escape(DEFAULT_MATHJAX)
_re_default_plotly = re.escape(DEFAULT_PLOTLY)

no_imports_result_raw = (
    r'''
<!DOCTYPE html>
<html>
    <head>
        <style id="head-style"></style>
        <title>Kaleido-fier</title>
        <script>
          window\.PlotlyConfig = {MathJaxConfig: 'local'}
        </script>
        <script type="text/x-mathjax-config">
          MathJax\.Hub\.Config\({ "SVG": { blacker: 0 }}\)
        </script>

        <script src="'''
    + _re_default_mathjax
    + r'''"></script>
        <script src="'''
    + _re_default_plotly
    + r"""" charset="utf\-8"></script>
        <script src="\S[^\n]*/kaleido_scopes\.js"></script>
    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido\-image" /></body>
</html>
"""
)
no_imports_result_re = re.compile(no_imports_result_raw)

all_defaults_re = re.compile(
    r'''
<!DOCTYPE html>
<html>
    <head>
        <style id="head-style"></style>
        <title>Kaleido-fier</title>
        <script>
          window\.PlotlyConfig = {MathJaxConfig: 'local'}
        </script>
        <script type="text/x-mathjax-config">
          MathJax\.Hub\.Config\({ "SVG": { blacker: 0 }}\)
        </script>

        <script src="'''
    + _re_default_mathjax
    + r""""></script>
        <script src="\S[^\n]*/package_data/plotly\.min\.js" charset="utf-8"></script>
        <script src="\S[^\n]*/kaleido_scopes\.js"></script>
    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido-image" /></body>
</html>
""",
)

with_plot_result_re = re.compile(
    r'''
<!DOCTYPE html>
<html>
    <head>
        <style id="head-style"></style>
        <title>Kaleido-fier</title>
        <script>
          window\.PlotlyConfig = {MathJaxConfig: 'local'}
        </script>
        <script type="text/x-mathjax-config">
          MathJax\.Hub\.Config\({ "SVG": { blacker: 0 }}\)
        </script>

        <script src="'''
    + _re_default_mathjax
    + r""""></script>
        <script src="https://with_plot" charset="utf-8"></script>
        <script src="\S[^\n]*/kaleido_scopes\.js"></script>
    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido-image" /></body>
</html>
""",
)

without_math_result_re = re.compile(r"""
<!DOCTYPE html>
<html>
    <head>
        <style id="head-style"></style>
        <title>Kaleido-fier</title>
        <script>
          window\.PlotlyConfig = {MathJaxConfig: 'local'}
        </script>
        <script type="text/x-mathjax-config">
          MathJax\.Hub\.Config\({ "SVG": { blacker: 0 }}\)
        </script>

        <script src="https://with_plot" charset="utf-8"></script>
        <script src="\S[^\n]*/kaleido_scopes\.js"></script>
    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido-image" /></body>
</html>
""")

with_others_result_raw = r"""
<!DOCTYPE html>
<html>
    <head>
        <style id="head-style"></style>
        <title>Kaleido-fier</title>
        <script>
          window\.PlotlyConfig = {MathJaxConfig: 'local'}
        </script>
        <script type="text/x-mathjax-config">
          MathJax\.Hub\.Config\({ "SVG": { blacker: 0 }}\)
        </script>

        <script src="https://with_mathjax"></script>
        <script src="https://with_plot" charset="utf-8"></script>
        <script src="https://1"></script>
        <script src="https://2"></script>
        <script src="\S[^\n]*/kaleido_scopes\.js"></script>
    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido-image" /></body>
</html>
"""
with_others_result_re = re.compile(with_others_result_raw)


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
    no_imports = PageGenerator().generate_index()
    assert no_imports_result_re.findall(no_imports), (
        f"{len(no_imports_result_raw)}: {no_imports_result_raw}"
        "\n"
        f"{len(no_imports)}: {no_imports}"
    )
    sys.path = old_path

    # this imports plotly so above test must have already been done
    all_defaults = PageGenerator().generate_index()
    assert all_defaults_re.findall(all_defaults)

    with_plot = PageGenerator(plotly="https://with_plot").generate_index()
    assert with_plot_result_re.findall(with_plot)

    without_math = PageGenerator(
        plotly="https://with_plot",
        mathjax=False,
    ).generate_index()
    assert without_math_result_re.findall(without_math)

    with_others = PageGenerator(
        plotly="https://with_plot",
        mathjax="https://with_mathjax",
        others=["https://1", "https://2"],
    ).generate_index()
    assert with_others_result_re.findall(with_others), (
        f"{len(with_others_result_raw)}: {with_others_result_raw}"
        "\n"
        f"{len(with_others)}: {with_others}"
    )


# test others
