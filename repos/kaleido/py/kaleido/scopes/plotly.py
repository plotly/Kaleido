from kaleido.scopes.base import BaseScope
from _plotly_utils.utils import PlotlyJSONEncoder
import base64


class PlotlyScope(BaseScope):
    """
    Scope for transforming Plotly figures to static images
    """
    _json_encoder = PlotlyJSONEncoder
    _text_formats = ("svg", "json")
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

        # Apply defualts
        format = format if format is not None else self.default_format
        width = width if width is not None else self.default_width
        height = height if height is not None else self.default_height
        scale = scale if scale is not None else self.default_scale

        # Normalize format
        format = format.lower()
        if format == 'jpg':
            format = 'jpeg'

        # Transform in superclass
        img = super(PlotlyScope, self).transform(
            figure, format=format, width=width, height=height, scale=scale
        )

        # Base64 decode binary types
        if format not in self._text_formats:
            img = base64.decodebytes(img)

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
