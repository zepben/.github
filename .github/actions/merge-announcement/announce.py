"""Create the ClickUp task for a merged pull request and render its Slack announcements.

The pull request comes from the GitHub event (GITHUB_EVENT_PATH); the version is the
project version at the merge commit. The task is created under the maintenance backlog
task, inside the release subtask for that version (created when missing):

    DEV-3959 Maintenance Backlog - Commons
    └── 1.18.0
        └── 1.18.0b24   <- one task per merged pull request

Parsing and rendering are pure functions; ClickUp calls are confined to ClickUp and
create_merge_task. Slack delivery is left to the workflow.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any

CLICKUP_API = "https://api.clickup.com/api/v2"
CHANGELOG_HEADING = "Application change log updates"
DESCRIPTION_HEADING = "Description"
TICKET = re.compile(r"\b(?:PROJ|EWB|EDNAR|BD|DEV|OPS|SUPPORT)-[0-9]{1,5}\b")
CODE_BLOCK = re.compile(r"^```[^\n]*\n(.*?)\n```", re.MULTILINE | re.DOTALL)
BREAKING_CHANGES = re.compile(r"^### Breaking Changes[ \t]*\n(.*?)(?=^### |\Z)", re.MULTILINE | re.DOTALL)
ALERT = re.compile(r">\s*\[!\w+\]")
RELEASE = re.compile(r"\d+\.\d+\.\d+")


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    body: str
    author: str
    url: str

    @classmethod
    def from_event(cls, event: dict[str, Any]) -> PullRequest:
        pull_request = event["pull_request"]
        return cls(
            number=pull_request["number"],
            title=pull_request["title"],
            body=pull_request.get("body") or "",
            author=pull_request["user"]["login"],
            url=pull_request["html_url"],
        )


@dataclass(frozen=True)
class ChangeNotes:
    description: str
    changelog: str


# Parsing


def h1_sections(body: str) -> dict[str, str]:
    """Split markdown into its top-level (`# `) sections, ignoring headings inside code fences."""
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    fenced = False
    for line in body.replace("\r\n", "\n").split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("# "):
            current = sections.setdefault(line[2:].strip(), [])
            continue
        if current is not None:
            current.append(line)
    return {heading: "\n".join(lines).strip() for heading, lines in sections.items()}


def without_alerts(text: str) -> str:
    """Drop GitHub alert blocks (`> [!IMPORTANT]` ...): the template's instructions to the author."""
    kept = []
    in_alert = False
    for line in text.split("\n"):
        if ALERT.match(line):
            in_alert = True
        elif not (in_alert and line.startswith(">")):
            in_alert = False
            kept.append(line)
    return "\n".join(kept).strip()


def parse(body: str) -> ChangeNotes | None:
    """Read the change notes from a pull request body; None when it has no change log block."""
    sections = h1_sections(body)
    block = CODE_BLOCK.search(sections.get(CHANGELOG_HEADING, ""))
    if block is None:
        return None
    return ChangeNotes(
        description=without_alerts(sections.get(DESCRIPTION_HEADING, "")),
        changelog=block.group(1).strip(),
    )


def breaking_changes(changelog: str) -> str:
    """The Breaking Changes entries, or "" when the section is absent or says none."""
    match = BREAKING_CHANGES.search(changelog)
    if match is None:
        return ""
    entries = match.group(1).strip()
    return "" if entries.rstrip(".").lower() in ("", "none", "* none", "- none") else entries


def release_of(version: str) -> str:
    """The release a snapshot version belongs to: 1.18.0b24 -> 1.18.0."""
    match = RELEASE.match(version)
    if match is None or match.group(0) == version:
        raise ValueError(f"Version {version!r} is not a snapshot of a release (expected e.g. 1.18.0b24).")
    return match.group(0)


# Rendering


def clickup_link(team_id: str, custom_id: str) -> str:
    return f"https://app.clickup.com/t/{team_id}/{custom_id}"


def task_links(pull_request: PullRequest, team_id: str) -> str:
    """Links to the ClickUp tickets named in the title, or to the pull request when it names none."""
    tickets = dict.fromkeys(TICKET.findall(pull_request.title))
    if not tickets:
        return f"[#{pull_request.number}]({pull_request.url})"
    return ", ".join(f"[{ticket}]({clickup_link(team_id, ticket)})" for ticket in tickets)


def render_task_body(pull_request: PullRequest, notes: ChangeNotes, team_id: str) -> str:
    return (
        f"#### Task: {task_links(pull_request, team_id)}\n\n"
        f"#### Action/dev notes:\n{notes.description or 'None.'}\n\n"
        f"#### Change log updates:\n\n```markdown\n{notes.changelog}\n```\n"
    )


def slack_escape(text: str) -> str:
    # https://docs.slack.dev/messaging/formatting-message-text#escaping
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_announcement(app: str, version: str, pull_request: PullRequest, task_url: str) -> str:
    return "\n".join(
        [
            f"App: {slack_escape(app)}",
            f"Version: {slack_escape(version)}",
            f"Description: {slack_escape(pull_request.title)} (#{pull_request.number})",
            f"Author: {slack_escape(pull_request.author)}",
            f"Task: {task_url}",
        ]
    )


def render_breaking_announcement(announcement: str, breaking: str) -> str:
    return f"{announcement}\nBreaking Changes:\n{slack_escape(breaking)}"


# ClickUp


class ClickUp:
    def __init__(self, token: str) -> None:
        self._token = token

    def request(self, method: str, path: str, body: dict[str, Any] | None = None, **query: str) -> dict[str, Any]:
        url = f"{CLICKUP_API}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        request = urllib.request.Request(
            url,
            data=None if body is None else json.dumps(body).encode(),
            method=method,
            headers={"Authorization": self._token, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")
            raise RuntimeError(f"ClickUp {method} {path} failed: HTTP {error.code} {detail}") from None


def create_merge_task(clickup: ClickUp, backlog_task: str, team_id: str, version: str, task_body: str) -> str:
    """Create the version's task under its release subtask (created when missing); returns its URL."""
    release = release_of(version)
    backlog = clickup.request(
        "GET", f"/task/{backlog_task}", custom_task_ids="true", team_id=team_id, include_subtasks="true"
    )
    list_id = backlog["list"]["id"]
    release_task = next((task for task in backlog.get("subtasks", []) if task["name"] == release), None)
    if release_task is None:
        release_task = clickup.request("POST", f"/list/{list_id}/task", {"name": release, "parent": backlog["id"]})
    task = clickup.request(
        "POST",
        f"/list/{list_id}/task",
        {"name": version, "parent": release_task["id"], "markdown_content": task_body},
    )
    return clickup_link(team_id, task["custom_id"]) if task.get("custom_id") else task["url"]


# GitHub Actions I/O


def write_outputs(values: dict[str, str]) -> None:
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as outputs:
        for name, value in values.items():
            delimiter = f"EOF_{uuid.uuid4().hex}"
            outputs.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def write_summary(markdown: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as summary:
            summary.write(markdown + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app", required=True)
    parser.add_argument("--backlog-task", required=True)
    parser.add_argument("--team-id", required=True)
    parser.add_argument("--version", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as event:
        pull_request = PullRequest.from_event(json.load(event))

    notes = parse(pull_request.body)
    if notes is None:
        # Unset outputs read as "", which skips the announcement jobs.
        write_summary(f"#{pull_request.number} has no `# {CHANGELOG_HEADING}` block; nothing was announced.")
        return 0

    # From the environment, not an argument, so the token never appears in process listings.
    token = os.environ.get("CLICKUP_TOKEN")
    if not token:
        raise RuntimeError("CLICKUP_TOKEN is not set.")

    task_body = render_task_body(pull_request, notes, args.team_id)
    task_url = create_merge_task(ClickUp(token), args.backlog_task, args.team_id, args.version, task_body)
    announcement = render_announcement(args.app, args.version, pull_request, task_url)
    breaking = breaking_changes(notes.changelog)
    breaking_announcement = render_breaking_announcement(announcement, breaking) if breaking else ""
    write_outputs({"task-url": task_url, "announcement": announcement, "breaking-announcement": breaking_announcement})

    summary = [
        f"Created [{args.version}]({task_url}).",
        f"````markdown\n{task_body}````",
        f"Announcement:\n```\n{announcement}\n```",
    ]
    if breaking_announcement:
        summary.append(f"Breaking changes announcement:\n```\n{breaking_announcement}\n```")
    write_summary("\n\n".join(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
