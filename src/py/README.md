# Pre-Launch Kaleido v1.0.0

<div align="center">
  <a href="https://dash.plotly.com/project-maintenance">
    <img src="https://dash.plotly.com/assets/images/maintained-by-plotly.png"
    width="400px" alt="Maintained by Plotly">
  </a>
</div>

Kaleido allows you to convert plotly figures to images.

It is now **much faster** and **memory efficient**: but Google Chrome is no longer
included.

```
$ pip install kaleido
# or
$ pip install --pre kaleido # for pre-release versions
# v1.0.0 is available as a release candidate (v1.0.0rc2).
```


Kaleido will try to use your own platform's `chrome`, but we recommend:

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
from kaleido import Kaleido

async with kaleido.Kaleido() as k:
  await k.write_fig(fig, path="./", opts={"format":"jpg"})

# or, there's a shortcut function:

await kaleido.write_fig(fig, path="./", opts={"format":"jpg"})
```

#### But I'm not running a async/await loop :-(

```python
import asyncio

asyncio.run(kaleido.write_fig(fig, path="./", opts={"format":"jpg"}))
```

## PageGenerators

`Kaleido(page=???)` takes a `kaleido.PageGenerator()` to customize versions.

```
custom_page = kaleido.PageGenerator(
                plotly  = "file://my.url.to.my.plotly.js",
                mathjax = False,
                others  = ["https://another.link"],
                )
# mathjax can also be a link

async with kaleido.Kaleido(page=custom_page) as k:
  ... # do stuff
```

## Full Reference

Coming Soon! For now, the source code has docstrings.

[`class Kaleido()`](https://github.com/plotly/Kaleido/blob/f0a26a5d75e4d1c2fd59d08d1179cadaaa693ca4/src/py/kaleido/kaleido.py#L460)

[`Kaleido.write_fig()`](https://github.com/plotly/Kaleido/blob/f0a26a5d75e4d1c2fd59d08d1179cadaaa693ca4/src/py/kaleido/kaleido.py#L668)

[`Kaleido.write_fig_from_object()`](https://github.com/plotly/Kaleido/blob/f0a26a5d75e4d1c2fd59d08d1179cadaaa693ca4/src/py/kaleido/kaleido.py#L761)


## More info

See the [Plotly static image export documentation][plotly-export] for more information.

[choreographer]: https://pypi.org/project/choreographer/
[plotly]: https://plotly.com/
[plotly-export]: https://plotly.com/python/static-image-export/
[pypi]: https://pypi.org/
[repo]: https://github.com/plotly/Kaleido
