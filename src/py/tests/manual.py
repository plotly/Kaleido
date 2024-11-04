import os
import sys
import shutil
_all_formats = ("png", "jpg", "jpeg", "webp", "svg", "pdf", "json")
dirname="./test-results/"
os.makedirs(dirname, exist_ok=True)
os.environ["KALEIDO-DEBUG"] = "true"

total = len(_all_formats) * 5
failures = []
x = 0
def count():
    global x
    x = x + 1
    print(f"\r{x}/{total}", end = "\r")

with open(dirname+"log.log", 'w') as sys.stderr:
    print("scope-old".center(50, "&"), file=sys.stderr)
    debug=True
    import plotly.graph_objects as go
    fig = go.Figure(data=[go.Scatter(y=[1, 3, 2])], layout=dict(title="$$\\text{Test} \\pi$$")) # whole thing needs to be mathjax?
    figgl = go.Figure(data=[go.Scattergl(y=[1, 3, 2])], layout=dict(title="$$\\text{Test} \\pi$$")) # whole thing needs to be mathjax?

    from kaleido.scopes.plotly import PlotlyScope
    scope = PlotlyScope(debug=debug,
        # plotlyjs="https://cdn.plot.ly/plotly-latest.min.js",
        # plotlyjs="/path/to/local/plotly.js",
    )
    for extension in _all_formats:
        try:
            print(f"Trying non-gl: {extension} w/ transform".center(40, "*"), file=sys.stderr)
            with open(dirname+"figure-scope-old."+extension, "wb") as f:
                f.write(scope.transform(fig, format=extension))
                count()
            print(f"Trying gl: {extension} w/ transform".center(40, "*"), file=sys.stderr)
            with open(dirname+"figure-scope-old-gl."+extension, "wb") as f:
                f.write(scope.transform(figgl, format=extension))
                count()

        except Exception as e:
            print(e, file=sys.stderr)
            failures.append(e)

    import asyncio
    print("ASYNC w/ PRETEND BLOCKING".center(50, "&"), file=sys.stderr)

    async def test_with_blocking_in_async():
        for extension in _all_formats:
            try:
                print(f"Trying: {extension} w/ transform".center(40, "*"), file=sys.stderr)
                with open(dirname+"figure-async-block."+extension, "wb") as f:
                    f.write(scope.transform(fig, format=extension))
                    count()
            except Exception as e:
                print(e, file=sys.stderr)
                failures.append(e)

    asyncio.run(test_with_blocking_in_async())
    print("ASYNC w/ ASYNC NATIVE".center(50, "&"), file=sys.stderr)


    import kaleido
    from kaleido.scopes.plotly import PlotlyScope
    async def test_with_async():
        for extension in _all_formats:
            try:
                print(f"Trying: {extension} w/ transform async".center(40, "*"), file=sys.stderr)
                spec = scope.make_spec(fig, format=extension)
                with open(dirname+"figure-async-native."+extension, "wb") as f:
                    f.write(await kaleido.to_image(spec, debug=debug))
                    count()
            except Exception as e:
                print(e, file=sys.stderr)
                failures.append(e)
    asyncio.run(test_with_async())
    ## Other

    print("express-write".center(50, "&"), file=sys.stderr)

    import plotly.express as px
    fig = px.scatter(px.data.iris(), x="sepal_length", y="sepal_width", color="species")
    fig.update_layout(dict(title="$$\\text{Test} \\pi$$"))
    for extension in _all_formats:
        try:
            print(f"Trying: {extension} w/ write_image".center(40, "*"), file=sys.stderr)
            fig.write_image(dirname+"figure-express." + extension, engine="kaleido")
            count()
        except Exception as e:
            print(e, file=sys.stderr)
            failures.append(e)
shutil.make_archive("test-results", 'zip', dirname)
print("Done!")
print(f"Successes: {x}/{total}")
print("Please send over test-results.zip")
print(f"Logs and images in {dirname}")

