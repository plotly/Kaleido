from kaleido.scopes.base import BaseScope
from _plotly_utils.utils import PlotlyJSONEncoder
import base64


class PlotlyScope(BaseScope):
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

    def transform(self, data, format=None, width=None, height=None, scale=None):
        # TODO: validate args

        # Apply defualts
        format = format if format is not None else self.default_format
        width = width if width is not None else self.default_width
        height = height if height is not None else self.default_height
        scale = scale if scale is not None else self.default_scale

        img = super(PlotlyScope, self).transform(
            data, format=format, width=width, height=height, scale=scale
        )

        if format not in self._text_formats:
            img = base64.decodebytes(img)

        return img

    # Flag property methods
    @property
    def plotlyjs(self):
        return self._plotlyjs

    @plotlyjs.setter
    def plotlyjs(self, val):
        self._plotlyjs = val
        self._shutdown_kaleido()

    @property
    def mathjax(self):
        return self._mathjax

    @mathjax.setter
    def mathjax(self, val):
        self._mathjax = val
        self._shutdown_kaleido()

    @property
    def topojson(self):
        return self._topojson

    @topojson.setter
    def topojson(self, val):
        self._topojson = val
        self._shutdown_kaleido()

    @property
    def mapbox_access_token(self):
        return self._mapbox_access_token

    @mapbox_access_token.setter
    def mapbox_access_token(self, val):
        self._mapbox_access_token = val
        self._shutdown_kaleido()
