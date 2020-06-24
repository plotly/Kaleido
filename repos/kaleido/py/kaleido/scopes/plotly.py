from kaleido.scopes.base import BaseScope
from _plotly_utils.utils import PlotlyJSONEncoder


class PlotlyScope(BaseScope):
    _json_encoder = PlotlyJSONEncoder

    def __init__(self, plotlyjs=None, mathjax=None, topojson=None, mapbox_access_token=None, **kwargs):
        # TODO: validate args
        super(PlotlyScope, self).__init__(
            plotlyjs=plotlyjs,
            mathjax=mathjax,
            topojson=topojson,
            mapbox_access_token=mapbox_access_token,
            **kwargs
        )

    @property
    def scope_name(self):
        return "plotly"


if __name__ == "__main__":
    print('here')
    import plotly
    print(plotly)