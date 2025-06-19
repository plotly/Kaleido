from pathlib import Path

import logistro

_logger = logistro.getLogger(__name__)

DEFAULT_PLOTLY = "https://cdn.plot.ly/plotly-2.35.2.js"
DEFAULT_MATHJAX = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js"

KJS_PATH = Path(__file__).resolve().parent / "vendor" / "kaleido_scopes.js"


class PageGenerator:
    """
    A page generator can set the versions of the js libraries used to render.

    It does this by outputting the HTML used to render the plotly figures.
    """

    header = """
<!DOCTYPE html>
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
"""
    """The header is the HTML that always goes at the top. Rarely needs changing."""

    footer = f"""
        <script src="{KJS_PATH.as_uri()}"></script>
    </head>
    <body style="{{margin: 0; padding: 0;}}"><img id="kaleido-image"><img></body>
</html>
"""
    """The footer is the HTML that always goes on the bottom. Rarely needs changing."""

    def __init__(self, *, plotly=None, mathjax=None, others=None, force_cdn=False):
        """
        Create a PageGenerator.

        Args:
            plotly: the url to the plotly script to use. The default is the one
            plotly.py is using, if not installed, it uses the constant declared.
            mathjax: the url to the mathjax script. By default is constant above.
            Can be set to false to turn off.
            others: a list of other script urls to include. Usually strings, but can be
            (str, str) where its (url, encoding).
            force_cdn: (default False) Don't use plotly import, use CDN

        """
        self._scripts = []
        if force_cdn:
            plotly = (DEFAULT_PLOTLY, "utf-8")
        elif not plotly:
            try:
                # ruff: noqa: PLC0415
                import plotly as pltly  # type: ignore [import-not-found]

                plotly_path = (
                    Path(pltly.__file__).parent / "package_data" / "plotly.min.js"
                )
                plotly = (
                    plotly_path.as_uri(),
                    "utf-8",
                )
                if not plotly_path.is_file():
                    _logger.warning(
                        f"Found plotly but path to js is wrong? {plotly[0]}",
                    )
                    plotly = (DEFAULT_PLOTLY, "utf-8")
                else:
                    plotly[0]
            except ImportError:
                _logger.info("Plotly not installed. Using CDN.")
                plotly = (DEFAULT_PLOTLY, "utf-8")
        elif isinstance(plotly, str):
            plotly = (plotly, "utf-8")
        _logger.debug(f"Plotly script: {plotly}")
        self._scripts.append(plotly)
        if mathjax is not False:
            if not mathjax:
                mathjax = DEFAULT_MATHJAX
            self._scripts.append(mathjax)
        if others:
            self._scripts.extend(others)

    def generate_index(self, path=None):
        """
        Generate the page.

        Args:
            path: If specified, page is written to path. Otherwise it is returned.

        """
        page = self.header
        script_tag = '\n        <script src="%s"></script>'
        script_tag_charset = '\n        <script src="%s" charset="%s"></script>'
        for script in self._scripts:
            if isinstance(script, str):
                page += script_tag % script
            else:
                page += script_tag_charset % script
        page += self.footer
        _logger.debug2(page)
        if not path:
            return page
        with (path).open("w") as f:
            f.write(page)
        return path.as_uri()
