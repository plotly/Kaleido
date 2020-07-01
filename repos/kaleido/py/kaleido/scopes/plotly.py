from kaleido.scopes.base import BaseScope
from _plotly_utils.utils import PlotlyJSONEncoder


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

        super(PlotlyScope, self).__init__(**kwargs)

    @property
    def scope_name(self):
        return "plotly"

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
