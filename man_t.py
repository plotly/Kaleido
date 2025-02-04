# ruff: noqa

import asyncio
import time

import baile

import plotly.express as px
fig = px.bar(x=["a", "b", "c"], y=[1, 3, 2], title="test_title")


async def make_fig(kaleido):
    tab = await kaleido.get_kaleido_tab()
    await tab.write_fig(fig)
    await kaleido.return_kaleido_tab(tab)

async def main():
    num = 1
    async with baile.Kaleido(headless=False, n=num) as k:
        await k.write_fig(fig)

start = time.perf_counter()
try:
    asyncio.run(main())
finally:
    end = time.perf_counter()
    elapsed = end - start
    print(f'Time taken: {elapsed:.6f} seconds')
