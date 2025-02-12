# Pre-Launch Kaleido v1.0.0

<div align="center">
  <a href="https://dash.plotly.com/project-maintenance">
    <img src="https://dash.plotly.com/assets/images/maintained-by-plotly.png"
    width="400px" alt="Maintained by Plotly">
  </a>
</div>

Kaleido allows you to convert plotly figures to images.

```
$ pip install kaleido # use --pre for release candidates
```

Right now, Kaledio v1.0.0 is available as a release candidate:

* download `v1.0.0rc2` explicitly **or**
* enable whatever installer you use (`pip --pre`?) to use release candidates

Kaleido's strategy has changed: `chrome` is no longer included. On the other hand,
it's *much* faster and supports parallel processing and memory-saving techniques.

Kaleido will try to use your own platform's `chrome`, but we recommend the following:

```
$ kaleido_get_chrome
```

or

```python

import kaleido
await kaleido.get_chrome()
# or
# kaleido.get_chrome_sync()
```

## Quickstart

```python
import kaleido

# fig is a plotly figure(s)

# 4 processes, 90 seconds, "png" are defaults
async with kaleido.Kaleido(n=4, timeout=90) as k:
  await k.write_fig(fig, path="./", opts={"format":"jpg"})

# Kaleido arguments:
# - n:       Set number of processors to use.
# - timeout: Set a timeout on any single image write.
# - page:    Customize the version of mathjax/plotly used.

# `Kaleido.write_fig` arguments:
# - fig:       A single plotly figure or an iterable.
# - path:      A directory (names based on fig title) or a single file.
# - opts:      A dictionary with image options:
#              {"scale":..., "format":..., "width":..., "height":...}
# - error_log: If you pass a list here, image-generation errors will be appended
#              to the list and generation continues. If left as None, the first error
#              will cause failure.

# Or use `Kaleido.write_fig_from_object`:
  await k.write_fig_from_object(fig_objects, error_log)
# where `fig_objects` is an iterable of dictionaries that have
# {"fig":, "path":, "opts":} keys corresponding `write_fig`'s arguments.
```

There are shortcut functions if just want dont want to create a `Kaleido()`.

```
import asyncio
import kaleido
asyncio.run(
          kaleido.write_fig(
                    fig,
                    path="./",
                    n=4
          )
)
```

If you want to set timeout or custom page, use a `Kaleido()`.

## PageGenerators

`Kaleido(page=???)` takes a `kaleido.PageGenerator()` to customize versions.

```
my_page = kaleido.PageGenerator(
                      plotly="A fully qualified link to plotly (https:// or file://)",
                      mathjax=False # no mathjax, or another fully quality link
                      others=["a list of other script links to include"]
                      )
async with kaleido.Kaleido(n=4, page=my_page) as k:
  ...
```

## More info

See the [Plotly static image export documentation][plotly-export] for more information.

[choreographer]: https://pypi.org/project/choreographer/
[plotly]: https://plotly.com/
[plotly-export]: https://plotly.com/python/static-image-export/
[pypi]: https://pypi.org/
[repo]: https://github.com/plotly/Kaleido
