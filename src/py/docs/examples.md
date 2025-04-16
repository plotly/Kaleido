# Kaleido Code Snippets

## Basic

```python
import plotly.express as px
import kaleido

### SAMPLE DATA ###

fig = px.scatter(
        px.data.iris(),
        x="sepal_length",
        y="sepal_width",
        color="species"
        )

fig2 = px.line(
        px.data.gapminder().query("country=='Canada'"),
        x="year",
        y="lifeExp",
        title='Life expectancy in Canada'
        )

figures = [fig, fig2]

### WRITE FIGURES ###

## Simple one image synchronous write

kaleido.write_fig_sync(fig, path="./output/")

## Multiple image write with error collection

error_log = []

kaleido.write_fig_sync(
  figures,
  path="./output/",
  opts={"format":"jpg"},
  error_log = error_log
  )

# Dump the error_log

if error_log:
  for e in error_log:
    print(str(e))
  raise RuntimeError("{len(error_log)} images failed.")

## async/await style of above

await kaleido.write_fig(
  figures,
  path="./output/",
  opts={"format":"jpg"},
  error_log = error_log
  )
```

## Generator (for batch processing)

Generating all of the plotly figures can take too much memory depending on the
number of figures, so use a generator:

```python
import plotly.express as px
import kaleido

### Make a figure generator

def generate_figures(): # can be async as well
  data = px.data.gapminder()
  for country in data["country"].unique(): # list all countries in dataset
    # yield unique plot for each country
    yield px.line(
        data.query(f'country=="{country}"'),
        x="year",
        y="lifeExp",
        title=f"Life expectancy in {country}"
        )

# four processors
kaleido.write_fig_sync(generate_figures(), path="./output/", n=4)
# file names will be taken from figure title

### If you need more control, use an object

def generate_figure_objects():
  data = px.data.gapminder()
  for country in data["country"].unique(): # list all countries in dataset
    fig = px.line(
        data.query(f'country=="{country}"'),
        x="year",
        y="lifeExp",
        title=f"Life expectancy in {country}"
        )
    yield {"fig": fig, "path": f"./output/{country}.jpg"}
    # customize file name

# four processors
kaleido.write_fig_from_object_sync(generate_figure_objects(), n=4)
```
