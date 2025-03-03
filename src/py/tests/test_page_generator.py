import re
import sys
from importlib.util import find_spec

import logistro
import pytest

from kaleido import PageGenerator

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")

_logger = logistro.getLogger(__name__)

no_imports_result_re = re.compile(r"""
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

        <script src="https://cdn\.plot\.ly/plotly-2\.35\.2\.js" charset="utf-8"></script>
        <script src="https://cdn\.jsdelivr\.net/npm/mathjax@3\.2\.2/es5/tex-svg\.js"></script>
        <script src="\S[^\n]*/kaleido_scopes\.js"></script>
    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido-image"><img></body>
</html>
""")  # noqa: E501 line too long

all_defaults_re = re.compile(r"""
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

        <script src="\S[^\n]*/package_data/plotly\.min\.js" charset="utf-8"></script>
        <script src="https://cdn\.jsdelivr\.net/npm/mathjax@3\.2\.2/es5/tex-svg\.js"></script>
        <script src="\S[^\n]*/kaleido_scopes\.js"></script>
    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido-image"><img></body>
</html>
""")

with_plot_result_re = re.compile(r"""
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

        <script src="file:///with_plot" charset="utf-8"></script>
        <script src="https://cdn\.jsdelivr\.net/npm/mathjax@3\.2\.2/es5/tex-svg\.js"></script>
        <script src="\S[^\n]*/kaleido_scopes\.js"></script>
    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido-image"><img></body>
</html>
""")

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

        <script src="file:///with_plot" charset="utf-8"></script>
        <script src="\S[^\n]*/kaleido_scopes\.js"></script>
    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido-image"><img></body>
</html>
""")

with_others_result_re = re.compile(r"""
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

        <script src="file:///with_plot" charset="utf-8"></script>
        <script src="file:///with_mathjax"></script>
        <script src="1"></script>
        <script src="2"></script>
        <script src="\S[^\n]*/kaleido_scopes\.js"></script>
    </head>
    <body style="{margin: 0; padding: 0;}"><img id="kaleido-image"><img></body>
</html>
""")


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
    assert no_imports_result_re.findall(no_imports)
    sys.path = old_path

    # this imports plotly so above test must have already been done
    all_defaults = PageGenerator().generate_index()
    assert all_defaults_re.findall(all_defaults)

    with_plot = PageGenerator(plotly="file:///with_plot").generate_index()
    assert with_plot_result_re.findall(with_plot)

    without_math = PageGenerator(
        plotly="file:///with_plot",
        mathjax=False,
    ).generate_index()
    assert without_math_result_re.findall(without_math)

    with_others = PageGenerator(
        plotly="file:///with_plot",
        mathjax="file:///with_mathjax",
        others=["1", "2"],
    ).generate_index()
    assert with_others_result_re.findall(with_others)


# test others
