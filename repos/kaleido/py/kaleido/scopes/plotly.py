from __future__ import absolute_import
from kaleido.scopes.base import BaseScope
from _plotly_utils.utils import PlotlyJSONEncoder
import base64


class PlotlyScope(BaseScope):
    """
    Scope for transforming Plotly figures to static images
    """
    _json_encoder = PlotlyJSONEncoder
    _all_formats = ("png", "jpg", "jpeg", "webp", "svg", "pdf", "eps", "json")
    _text_formats = ("svg", "json", "eps")

    _scope_flags = ("plotlyjs", "mathjax", "topojson", "mapbox_access_token")

    def __init__(self, plotlyjs=None, mathjax=None, topojson=None, mapbox_access_token=None, **kwargs):
        # TODO: validate args
        # Save scope flags as internal properties
        self._plotlyjs = plotlyjs
        self._mathjax = mathjax
        self._topojson = topojson
        self._mapbox_access_token = mapbox_access_token

        # to_image-level default values
        self.default_format = "png"
        self.default_width = 700
        self.default_height = 500
        self.default_scale = 1

        super(PlotlyScope, self).__init__(**kwargs)

    @property
    def scope_name(self):
        return "plotly"

    def transform(self, figure, format=None, width=None, height=None, scale=None):
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
        # TODO: validate args
        from plotly.graph_objects import Figure
        if isinstance(figure, Figure):
            figure = figure.to_dict()

        # Apply default format and scale
        format = format if format is not None else self.default_format
        scale = scale if scale is not None else self.default_scale

        # Get figure layout
        layout = figure.get("layout", {})

        # Compute default width / height
        width = width or layout.get("width", None) or self.default_width
        height = height or layout.get("height", None) or self.default_height

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

        # Transform in using _perform_transform rather than superclass so we can access the full
        # response dict, including error codes.
        response = self._perform_transform(
            figure, format=format, width=width, height=height, scale=scale
        )

        # Check for export error, later can customize error messages for plotly Python users
        code = response.get("code", 0)
        if code != 0:
            message = response.get("message", None)
            raise ValueError(
                "Transform failed with error code {code}: {message}".format(
                    code=code, message=message
                )
            )

        img = response.get("result").encode("utf-8")

        # Base64 decode binary types
        if format not in self._text_formats:
            img = base64.b64decode(img)

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
