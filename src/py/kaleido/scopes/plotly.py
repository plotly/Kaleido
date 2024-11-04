from __future__ import absolute_import
import os
from pathlib import Path
import tempfile
import sys

from plotly.graph_objects import Figure

import kaleido # kaleido __init__.py, dislike

# The original kaleido provided a global lock (instead of supporting concurrency)
# So kaleido 2.0 will as well if it's used from scopes (old api)
from threading import Lock
_proc_lock = Lock()

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

class PlotlyScope():
    """
    Scope for transforming Plotly figures to static images
    """
    _all_formats = kaleido._all_formats_
    _text_formats = kaleido._text_formats_

    _scope_flags = kaleido._scope_flags_


    def __init__(self, plotlyjs=None, mathjax=None, topojson=None, mapbox_access_token=None, debug=None, **kwargs):
        if debug is None:
            debug = "KALEIDO-DEBUG" in os.environ
        self.debug=debug
        # TODO: #2 This is deprecated, this whole FILE is deprecated
        self._plotlyjs = plotlyjs
        self._topojson = topojson
        self._mapbox_access_token = mapbox_access_token

        # Try to find local MathJax, but never fail if something goes wrong
        try:
            self._initialize_mathax(mathjax)
        except: # noqa TODO what would the actual error be
            self._mathjax = None

        # to_image-level default values
        self.default_format = "png"
        self.default_width = 700
        self.default_height = 500
        self.default_scale = 1

        self._plotlyfier = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'vendor',
            'kaleido_scopes.js'
            )

        self._tempdir = tempfile.TemporaryDirectory(dir=Path.home(), prefix=".kaleido-")
        if self.debug: print(f"Tempdir: {self._tempdir.name}", file=sys.stderr)
        self._tempfile = open(f"{self._tempdir.name}/index.html", "w")
        self._tempfile.write(self.make_page_string())
        self._tempfile.close()

    def _initialize_mathax(self, mathjax=None):
        if mathjax is not None:
            self._mathjax = mathjax
            return

        vendored_mathjax_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'vendor',
            'mathjax',
            'MathJax.js'
            )
        # There is something wild going on w/ mathjax, I think plotly is injecting it?
        mathjax_path = None
        if os.path.exists(vendored_mathjax_path):
            # MathJax is vendored under kaleido/executable.
            # It was probably install as a PyPI wheel
            mathjax_path = vendored_mathjax_path

        if mathjax_path:
            mathjax_uri = Path(mathjax_path).absolute().as_uri()
            self._mathjax = mathjax_uri
        else:
            self._mathjax = None

    def make_page_string(self):
        page = \
"""<!DOCTYPE html>
<html>
  <head>
    <style id=\"head-style\"></style>
    <title>Kaleido-fier</title>
    <script>
        window.KaleidoReport = ["start"];
        function logError(e) {
            window.KaleidoReport.push("error");
            window.KaleidoReport.push(e);
            if (!navigator.onLine) {
                window.KaleidoReport.push("offline");
            }
        }
    </script>
    <script>
      window.PlotlyConfig = {MathJaxConfig: 'local'}
    </script>
"""
        pjs = self._plotlyjs
        if not pjs:
            pjs = "https://cdn.plot.ly/plotly-2.35.2.min.js"
        elif not pjs.startswith("http") and not pjs.startswith("file"):
            pjs = Path(pjs).absolute().as_uri()
        page += f" <script src=\"{pjs}\" charset=\"utf-8\" onerror=\"logError('plotly')\"></script>\n"

        if self._mathjax:
            page += f" <script type=\"text/javascript\" id=\"MathJax-script\" src=\"{self._mathjax}?config=TeX-AMS-MML_SVG\" onerror=\"logError('mathjax')\"></script>\n"
        page+= \
f"""    <script src="{Path(self._plotlyfier).absolute().as_uri()}" onerror=\"logError('scoper')\"></script>"""+\
"""  </head>
  <body style=\"{margin: 0; padding: 0;}\"><img id=\"kaleido-image\"><img></body>
</html>"""
        if self.debug:
            print("Displaying generated HTML".center(50, "*"), file=sys.stderr)
            print(page, file=sys.stderr)
            print("end".center(50, "*"), file=sys.stderr)
        return page

    @property
    def scope_name(self):
        # TODO: #2 This is deprecated
        return "plotly"

    def make_spec(self, figure, format=None, width=None, height=None, scale=None):
        # TODO: validate args
        if isinstance(figure, Figure):
            figure = figure.to_dict()

        # Apply default format and scale
        format = format if format is not None else self.default_format
        scale = scale if scale is not None else self.default_scale

        # Get figure layout
        layout = figure.get("layout", {})

        # Compute image width / height
        width = (
                width
                or layout.get("width", None)
                or layout.get("template", {}).get("layout", {}).get("width", None)
                or self.default_width
        )
        height = (
                height
                or layout.get("height", None)
                or layout.get("template", {}).get("layout", {}).get("height", None)
                or self.default_height
        )

        # Normalize format
        original_format = format
        format = format.lower()
        if format == 'jpg':
            format = 'jpeg'

        if format not in self._all_formats:
            supported_formats_str = repr(list(self._all_formats))
            raise ValueError(
                "Invalid format '{original_format}'.\n"
                "    Supported formats: {supported_formats_str}"
                .format(
                    original_format=original_format,
                    supported_formats_str=supported_formats_str
                )
            )


        js_args = dict(format=format, width=width, height=height, scale=scale)
        return dict(js_args, data = figure)

    def transform(self, figure, format=None, width=None, height=None, scale=None, debug=None):
        """
        Convert a Plotly figure into a static image

        :param figure: Plotly figure or figure dictionary
        :param format: The desired image format. One of
           'png', 'jpg', 'jpeg', 'webp', 'svg', 'pdf', or 'json'.

           If 'json', the following arguments are ignored and a full
           JSON representation of the figure is returned.

           If not specified, will default to the `scope.default_format` property
        :param width: The width of the exported image in layout pixels.
            If the `scale` property is 1.0, this will also be the width
            of the exported image in physical pixels.

            If not specified, will default to the `scope.default_width` property
        :param height: The height of the exported image in layout pixels.
            If the `scale` property is 1.0, this will also be the height
            of the exported image in physical pixels.

            If not specified, will default to the `scope.default_height` property
        :param scale: The scale factor to use when exporting the figure.
            A scale factor larger than 1.0 will increase the image resolution
            with respect to the figure's layout pixel dimensions. Whereas as
            scale factor of less than 1.0 will decrease the image resolution.

            If not specified, will default to the `scope.default_scale` property
        :return: image bytes
        """
        if not debug:
            debug=self.debug
        spec = self.make_spec(figure, format=format, width=width, height=height, scale=scale)

        # Write to process and read result within a lock so that can be
        # sure we're reading the response to our request
        with _proc_lock:
            img = kaleido.to_image_block(spec, Path(self._tempfile.name).absolute(), self._topojson, self._mapbox_access_token, debug=debug)

        return img

    # Flag property methods
    @property
    def plotlyjs(self):
        """
        URL or local file path to plotly.js bundle to use for image export.
        If not specified, will default to CDN location.
        """
        return self._plotlyjs

    @plotlyjs.setter
    def plotlyjs(self, val):
        self._plotlyjs = val
        self._shutdown_kaleido()

    @property
    def mathjax(self):
        """
        URL to MathJax bundle needed for LaTeX rendering.
        If not specified, LaTeX rendering support will be disabled.
        """
        return self._mathjax

    @mathjax.setter
    def mathjax(self, val):
        self._mathjax = val
        self._shutdown_kaleido()

    @property
    def topojson(self):
        """
        URL to the topojson files needed to render choropleth traces.
        If not specified, will default to CDN location.
        """
        return self._topojson

    @topojson.setter
    def topojson(self, val):
        self._topojson = val
        self._shutdown_kaleido()

    @property
    def mapbox_access_token(self):
        """
        Mapbox access token required to render mapbox layers.
        If not specified, mapbox layers will only be rendered
        if a valid token is specified inline in the figure specification
        """
        return self._mapbox_access_token

    @mapbox_access_token.setter
    def mapbox_access_token(self, val):
        self._mapbox_access_token = val
        self._shutdown_kaleido()

    def _shutdown_kaleido(self):
        self._tempfile = open(f"{self._tempdir.name}/index.html", "w")
        self._tempfile.write(self.make_page_string())
        self._tempfile.close()

    def __del__(self):
        try:
            if os.path.exists(self._tempfile.name):
                try:
                    os.remove(self._tempfile.name)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if os.path.exists(self._tempdir.name):
                try:
                    self._tempdir.cleanup()
                except Exception:
                    pass
                try:
                    os.rmdir(self._tempdir.name)
                except Exception:
                    pass
        except Exception:
            pass
