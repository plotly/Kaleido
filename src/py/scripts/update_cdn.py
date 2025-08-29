import asyncio
import json
import os
import pathlib
import subprocess
import sys

import aiohttp
import jq
import semver
from kaleido._page_generator import DEFAULT_PLOTLY
from kaleido._page_generator import __file__ as FILE_PATH
import changelogtxt_parser as changelog

REPO = os.environ["REPO"]
GITHUB_WORKSPACE = os.environ["GITHUB_WORKSPACE"]


async def run(commands: list[str]) -> tuple[bytes, bytes, int | None]:
    p = await asyncio.create_subprocess_exec(
        *commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return (*(await p.communicate()), p.returncode)


async def verify_url(url: str) -> bool:
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            return response.status == 200


async def get_latest_version() -> str:
    out, err, _ = await run(["gh", "api", "repos/plotly/plotly.js/tags", "--paginate"])
    tags = jq.compile('map(.name | ltrimstr("v"))').input_value(json.loads(out)).first()
    versions = [semver.VersionInfo.parse(v) for v in tags]
    if err:
        print(err.decode())
        sys.exit(1)
    return str(max(versions))


async def create_pr(latest_version: str) -> None:
    branch = f"bot/update-cdn-{latest_version}"
    _, err, brc_eval = await run(
        ["gh", "api", f"repos/{REPO}/branches/{branch}", "--silent"]
    )

    if brc_eval:
        msg = err.decode()
        if "HTTP 404" not in msg:
            print(msg)  # unexpected errors
            sys.exit(1)
    else:
        print(f"The branch {branch} already exists")
        sys.exit(1)

    pr, _, _ = await run(
        ["gh", "pr", "list", "-R", REPO, "-H", branch, "--state", "all"]
    )

    if pr.decode():
        print(f"Pull request for '{branch}' already exists")  # err if is empty
        sys.exit(1)

    title = f"Update Plotly.js CDN to v{latest_version}"
    file_updated = changelog.update_version(latest_version, title, GITHUB_WORKSPACE)

    if not file_updated:
        print("Failed to update changelog")
        sys.exit(1)

    await run(["git", "checkout", "-b", branch])
    await run(["git", "add", "."])
    await run(
        [
            "git",
            "-c",
            "user.name='github-actions'",
            "-c",
            "user.email='github-actions@github.com'",
            "commit",
            "-m",
            f"chore: {title}",
        ]
    )
    _, push_err, push_eval = await run(["git", "push", "-u", "origin", branch])

    if push_eval:
        print(push_err.decode())
        sys.exit(1)

    body = f"This PR updates the CDN URL to v{latest_version}."
    new_pr, pr_err, pr_eval = await run(
        ["gh", "pr", "create", "-B", "master", "-H", branch, "-t", title, "-b", body]
    )
    if pr_eval:
        print(pr_err.decode())
        sys.exit(1)

    print("Pull request:", new_pr.decode().strip())
    sys.exit(0)


async def main() -> None:
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

        await create_pr(latest_version)
    else:
        title = f"CDN not reachable for Plotly.js v{latest_version}"
        body = f"URL: {new_cdn} - invalid url"
        brc, _, _ = await run(
            [
                "gh",
                "issue",
                "--json",
                "number,state",
                "list",
                "--search",
                title,
                "--state",
                "all",
            ]
        )
        issues = json.loads(brc.decode())
        if issues:
            for issue in issues:
                if issue.get("state") == "OPEN":
                    print(f"Issue '{title}' already exists in:")
                    print(f"https://github.com/{REPO}/issues/{issue.get('number')}")
                    sys.exit(1)
            print(f"Issue '{title}' is closed")
            sys.exit(0)

        new_issue, issue_err, _ = await run(
            ["gh", "issue", "create", "-R", REPO, "-t", title, "-b", body]
        )
        if issue_err:
            print(issue_err.decode())

        print(f"The issue '{title}' was created in {new_issue.decode().strip()}")
        sys.exit(1)


asyncio.run(main())
