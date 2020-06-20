# import subprocess
# import time

#
# # proc = subprocess.Popen(
# #     [kaleido_path,
# #      "plotly",
# #      "--mathjax=https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js",
# #      # "--plotlyjs=file:///home/jmmease/scratch/plotly-latest.min.js",
# #      # "--topojson=file:///home/jmmease/PyDev/repos/plotly.js/dist/topojson/",
# #      "--mapbox-access-token=" + mapbox_accesstoken
# #      ],
# #     stdin=subprocess.PIPE, stdout=subprocess.PIPE #, stderr=subprocess.PIPE
# # )
# #
# # def to_image(fig, format="png", width=700, height=500, scale=1, timeout=20):
# #     import json
# #     import base64
# #     export_spec = (pio.to_json({
# #         "figure": fig,
# #         "format": format,
# #         "width": width,
# #         "height": height,
# #         "scale": scale,
# #     }, validate=False) + "\n").encode()
# #
# #     # Write and flush spec
# #     proc.stdin.writelines([export_spec])
# #     proc.stdin.flush()
# #     response = proc.stdout.readline()
# #     print(response)
# #     response = json.loads(response.decode('utf-8'))
# #     img_string = response.pop('result')
# #
# #     # # Debuggin PDFs
# #     # with open('../tmp.html', 'w') as f:
# #     #     f.write(response.pop('html'))
# #
# #     print(response)
# #
# #     if img_string is None:
# #         raise ValueError(response)
# #
# #     if format == 'svg':
# #         img = img_string.encode()
# #     else:
# #         img = base64.decodebytes(img_string.encode())
# #     return img

def build_mapbox_plot():
    import pandas as pd
    us_cities = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/us-cities-top-1k.csv")

    import plotly.express as px

    fig = px.scatter_mapbox(us_cities, lat="lat", lon="lon", hover_name="City", hover_data=["State", "Population"],
                            color_discrete_sequence=["fuchsia"], zoom=3, height=300)
    fig.update_layout(mapbox_style="dark")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

def build_topojson_plot():
    import plotly.express as px
    df = px.data.gapminder().query("year==2007")
    return px.choropleth(df, locations="iso_alpha",
                        color="lifeExp", # lifeExp is a column of gapminder
                        hover_name="country", # column to add to hover information
                        color_continuous_scale=px.colors.sequential.Plasma)

def bulid_mathjax_plot():
    return go.Figure(
        {
            "data":[{"y":[1,3,2], "name":"asdf another", "type": "scatter"}],
            "layout": {"title": {"text": r"$\pi^2$"}}
        }
    )

def bulid_simple_plot():
    return go.Figure(
        {
            "data":[{"y":[1,3,2], "name":"asdf another", "type": "scattergl"}],
            "layout": {"title": {"text": "Title"}}
        }
    )


if __name__ == "__main__":
    from kaleido.scopes.plotly import PlotlyScope
    import plotly.graph_objects as go
    import plotly.io as pio
    pio.templates.default = "plotly_dark"

    # Constants
    mapbox_access_token = "pk.eyJ1Ijoiam1tZWFzZSIsImEiOiJjamljeWkwN3IwNjEyM3FtYTNweXV4YmV0In0.2zbgGCjbPTK7CToIg81kMw"
    plotlyjs = "file:///home/jmmease/scratch/plotly-latest.min.js"
    topojson = "file:///home/jmmease/PyDev/repos/plotly.js/dist/topojson/"
    mathjax = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js"

    scope = PlotlyScope(
        plotlyjs=plotlyjs, mathjax=mathjax, mapbox_access_token=mapbox_access_token
    )
    # time.sleep(4)
    #
    # fig = build_mapbox_plot()
    # with open('../fig1.pdf', 'wb') as f:
    #     f.write(scope.to_image(fig, format='png', width=700))

    fig = bulid_mathjax_plot()
    with open('../scratch/fig2.png', 'wb') as f:
        f.write(scope.to_image(fig, format='png', width=700))
    # #
    # # fig = build_topojson_plot()
    # # with open('../fig3.pdf', 'wb') as f:
    # #     f.write(to_image(fig.to_dict(), format='pdf', width=300))
    #
    # # fig = build_topojson_plot()
    # # fig = bulid_mathjax_plot()
    # # fig = bulid_simple_plot()
    # # fig_json = fig.to_dict()
    #
    # # fig_json = {"data":[{"y":[1,3,2], "name": "asdf another"}]}
    #
    import time
    t0 = time.time()
    imgs = []
    # fig = bulid_mathjax_plot()
    fig = bulid_simple_plot()
    # fig = build_mapbox_plot()
    for i, format in enumerate(['pdf'] * 100): #['png', 'svg', 'jpeg']:
        # fig.update_layout(yaxis_title_text=str(i))
        fig.update_layout(title_text=str(i))
        img = scope.to_image(fig, format=format)
        # print(img)
        imgs.append(img)
        # print(format)
        # print(img)
        with open(f'../scratch/fig-{i}.{format}', 'wb') as f:
            f.write(img)

    t1 = time.time()
    print(f"time: {t1 - t0}")
    print(len(imgs))
    print(imgs[0])
