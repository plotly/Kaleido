# /// script
# requires-python = ">=3.12"
# dependencies = [
#  "aiohttp",
#  "changelogtxt_parser @ git+https://github.com/geopozo/changelogtxt-parser",
#  "jq",
#  "semver",
# ]
# ///

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import aiohttp
import changelogtxt_parser as changelog
import jq
import semver

from py.kaleido._page_generator import DEFAULT_PLOTLY
from py.kaleido._page_generator import __file__ as FILE_PATH

# ruff: noqa: T201 allow print in CLI

REPO = os.environ["REPO"]
GITHUB_WORKSPACE = os.environ["GITHUB_WORKSPACE"]


async def run_cmd(commands: list[str]) -> tuple[bytes, bytes, int | None]:
    proc = await asyncio.create_subprocess_exec(
        *commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout, stderr, proc.returncode


async def verify_url(url: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url) as response:
                return response.status == 200
    except aiohttp.ClientError:
        return False


async def get_latest_version() -> str:
    out, err, _ = await run_cmd(
        ["gh", "api", "repos/plotly/plotly.js/tags", "--paginate"]
    )
    if err:
        print(err.decode(), file=sys.stderr)
        sys.exit(1)

    data = json.loads(out)
    tags = jq.compile('map(.name | ltrimstr("v"))').input_value(data).first()
    versions = [semver.VersionInfo.parse(v) for v in tags]

    return str(max(versions))


async def create_pr(latest_version: str) -> None:
    branch = f"bot/update-cdn-{latest_version}"
    title = f"Update Plotly.js CDN to v{latest_version}"
    body = f"This PR updates the CDN URL to v{latest_version}."

    _, brc_err, brc_eval = await run_cmd(
        ["gh", "api", f"repos/{REPO}/branches/{branch}", "--silent"]
    )
    branch_exists = brc_eval == 0

    if branch_exists:
        print(f"The branch {branch} already exists", file=sys.stderr)
        sys.exit(1)
    else:
        msg = brc_err.decode()
        if "HTTP 404" not in msg:
            print(msg, file=sys.stderr)  # unexpected errors
            sys.exit(1)

    pr_exist, _, _ = await run_cmd(
        ["gh", "pr", "list", "-R", REPO, "-H", branch, "--state", "all"]
    )

    if pr_exist:
        print(f"Pull request for '{branch}' already exists", file=sys.stderr)
        sys.exit(1)

    try:
        changelog.update(f"v{latest_version}", title, GITHUB_WORKSPACE)
    except (ValueError, RuntimeError):
        print("Failed to update changelog", file=sys.stderr)
        sys.exit(1)

    await run_cmd(["git", "checkout", "-b", branch])
    await run_cmd(["git", "add", "."])
    await run_cmd(
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
    _, push_err, push_eval = await run_cmd(["git", "push", "-u", "origin", branch])
    push_failed = push_eval == 1

    if push_failed:
        print(push_err.decode(), file=sys.stderr)
        sys.exit(1)

    new_pr_out, pr_err, pr_eval = await run_cmd(
        ["gh", "pr", "create", "-B", "master", "-H", branch, "-t", title, "-b", body]
    )
    pr_failed = pr_eval == 1

    if pr_failed:
        print(pr_err.decode(), file=sys.stderr)
        sys.exit(1)

    print("Pull request:", new_pr_out.decode().strip())


async def verify_issue(title: str) -> None:
    issues_out, _, _ = await run_cmd(
        [
            "gh",
            "issue",
            "list",
            "-R",
            REPO,
            "--search",
            title,
            "--state",
            "all",
            "--json",
            "number,state",
        ]
    )
    issues = json.loads(issues_out.decode())

    if issues:
        print(f"Issue '{title}' already exists in:")
        print(f"https://github.com/{REPO}/issues/{issues[0].get('number')}")
        sys.exit(1)


async def create_issue(title: str, body: str) -> None:
    new_issue, issue_err, _ = await run_cmd(
        ["gh", "issue", "create", "-R", REPO, "-t", title, "-b", body]
    )
    if issue_err:
        print(issue_err.decode())
        sys.exit(1)

    print(f"The issue '{title}' was created in {new_issue.decode().strip()}")


async def main() -> None:
    latest_version = await get_latest_version()
    new_cdn = f"https://cdn.plot.ly/plotly-{latest_version}.js"

    if new_cdn == DEFAULT_PLOTLY:
        print("Already up to date")
        return

    cdn_exists = await verify_url(new_cdn)

    if cdn_exists:
        file_path = Path(FILE_PATH)
        content = file_path.read_text(encoding="utf-8")
        updated = content.replace(DEFAULT_PLOTLY, new_cdn, 1)
        
        file_path.write_text(updated, encoding="utf-8")

        await create_pr(latest_version)
    else:
        title = f"CDN not reachable for Plotly.js v{latest_version}"
        body = f"URL: {new_cdn} - invalid url"

        await verify_issue(title)
        await create_issue(title, body)


asyncio.run(main())
