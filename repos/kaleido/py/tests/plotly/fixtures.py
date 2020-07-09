import plotly.graph_objects as go
import plotly.express as px
from pytest import fixture
import pandas as pd

font = {"family": "Monospace"}

def simple_figure():
    return go.Figure(
        {
            "data": [{"y": [1, 3, 2], "type": "scatter"}],
            "layout": {"title": {"text": "Title"}, "font": font}
        }
    )


def gl_figure():
    return go.Figure(
        {
            "data": [{"y": [1, 3, 2], "type": "scattergl"}],
            "layout": {"title": {"text": "Title"}, "font": font}
        }
    )


def mathjax_figure():
    return go.Figure(
        {
            "data": [{"y": [1, 3, 2], "type": "scatter"}],
            "layout": {"title": {"text": r"$\pi^2$"}, "font": font}
        }
    )


def topojson_figure():
    df = px.data.gapminder().query("year==2007")
    return px.choropleth(
        df, locations="iso_alpha", color="lifeExp",
        hover_name="country", color_continuous_scale=px.colors.sequential.Plasma
    ).update_layout(font=font)


def mapbox_figure():
    us_cities = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/us-cities-top-1k.csv")

    import plotly.express as px

    fig = px.scatter_mapbox(
        us_cities, lat="lat", lon="lon", hover_name="City", hover_data=["State", "Population"],
        color_discrete_sequence=["fuchsia"], zoom=3, height=300
    )
    fig.update_layout(mapbox_style="dark")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, font=font)
    return fig


def all_figures():
    return [
        (simple_figure(), 'simple'),
        (gl_figure(), 'webgl'),
        (mathjax_figure(), 'mathjax'),
        (topojson_figure(), 'topojson'),
        # Comment until we get token worked out
        (mapbox_figure(), 'mapbox')
    ]

all_formats = ['png', 'jpeg', 'webp', 'svg', 'pdf', 'eps']
