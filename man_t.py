# ruff: noqa

import asyncio
import random
import time

import baile

import plotly.express as px

def make_figs():
    sample_range = range(1, 101)
    for _ in range(1):
        yield px.bar(x=["a", "b", "c"], y=random.sample(sample_range, 3), title="test_title")


async def main():
    num = 12
    async with baile.Kaleido(n=num) as k:
        await k.write_fig(make_figs(), path="./hello/test.jpg")

start = time.perf_counter()
try:
    asyncio.run(main())
finally:
    end = time.perf_counter()
    elapsed = end - start
    print(f'Time taken: {elapsed:.6f} seconds')
