# ruff: noqa

import asyncio
import cProfile

import baile


async def print(kaleido):
    tab = await kaleido.get_kaleido_tab()
    await tab.console_print("Hi!")
    await asyncio.sleep(3)
    await tab.console_print("Bye!")
    await kaleido.return_kaleido_tab(tab)

async def main():
    tasks = set()
    async with baile.Kaleido(headless=False, n=5) as k:
        for _ in range(5):
            tasks.add(asyncio.create_task(print(k)))

        for task in tasks:
          await task

cProfile.run("asyncio.run(main())")
