import plotly.express as px
import time as dt
import pandas as pd
import numpy as np

start = dt.time()
# df = px.data.iris()

# Number of rows you want for the DataFrame
num_rows = 1000

# Create a DataFrame with the same columns as the Iris dataset
df = pd.DataFrame({
    'sepal_length': np.random.uniform(4.0, 7.0, num_rows),
    'sepal_width': np.random.uniform(2.0, 4.5, num_rows),
    'petal_length': np.random.uniform(1.0, 6.9, num_rows),
    'petal_width': np.random.uniform(0.1, 2.5, num_rows),
    'species': np.random.choice(['setosa', 'versicolor', 'virginica'], num_rows)
})

fig = px.scatter(
        df, x="petal_length", y="sepal_length", color="species"
)

data = fig.to_image(format="svg", engine="kaleido")
end = dt.time()

print(data)

print(f"Time taken: {end - start}")

# start = dt.time()
# from kaleido.scopes.plotly import PlotlyScope
# import plotly.graph_objects as go

# scope = PlotlyScope(
#     plotlyjs="https://cdn.plot.ly/plotly-latest.min.js",
#     # plotlyjs="/path/to/local/plotly.js",
# )

# fig = go.Figure(data=[go.Scatter(y=[1, 3, 2])])
# with open("figure.png", "wb") as f:
# 	scope = scope.transform(fig, format="png");
# 	f.write(scope)

# end = dt.time()

# print(f"Time taken: {end - start}")