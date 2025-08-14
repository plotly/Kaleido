#!/usr/bin/env python3
import asyncio
import os
import pathlib
import subprocess
import sys

import jq
import orjson
from kaleido._page_generator import DEFAULT_PLOTLY, __file__ as FILE_PATH
import semver
import aiohttp

REPO = os.environ["REPO"]


async def command_call(commands: list[str]) -> tuple[bytes, bytes]:
    p = await asyncio.create_subprocess_exec(
        *commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return await p.communicate()


async def get_latest_version() -> str:
    out, err = await command_call(["gh", "api", "repos/plotly/plotly.js/tags", "--paginate"])
    tags = jq.compile("map(.name)").input_value(orjson.loads(out)).first()
    versions = [semver.VersionInfo.parse(v.lstrip("v")) for v in tags]
    return str(max(versions))


async def verify_url(url: str) -> bool:
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            return response.status == 200


async def main():
    latest_version = await get_latest_version()
    new_cdn = f"https://cdn.plot.ly/plotly-{latest_version}.js"

    if new_cdn == DEFAULT_PLOTLY:
        print("Already up to date")
        sys.exit(0)

    cdn_exists = await verify_url(new_cdn)
    if cdn_exists:
        p = pathlib.Path(FILE_PATH)
        s = p.read_text(encoding="utf-8").replace(DEFAULT_PLOTLY, new_cdn, 1)
        p.write_text(s, encoding="utf-8")
        print("PATH:", p)
        await command_call("ls")
        await command_call("cat", p)
        await command_call("git", "branch")
        await command_call("git", "status")
    else:
        title = f"'CDN not reachable for Plotly v{latest_version}'"
        body = f"URL: {new_cdn} - invalid url"
        out, err = await command_call(
            ["gh", "issue", "create", "-R", REPO, "-t", title, "-b", body]
        )
        print(
            f"The issue {title} was created in {out.decode().strip()}"
            if not err
            else err
        )


asyncio.run(main())
