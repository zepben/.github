"""Add upgrade notes from merged pull requests to a news file, under the version just published.

Runs in a snapshot workflow's update-snapshot-version job, before update-version.sh, in
repositories that have a NEWS.md; the action skips the others. Adding the file, which can
be empty, is how a repository turns news on. The file is staged, so the bump commit
("Update snapshot 1.18.0b26 to 1.18.0b27 [skip ci]") carries it to the branch.

Which pull requests: those merged since the last "Update snapshot" commit, the last time
this file was written. One snapshot can cover several pull requests (a run was skipped
because the branch moved, a build failed, or a pull request was merged with [skip ci]);
all of them land under the first version that contains them.

The file and the bump commit reach the branch together or not at all. So a pull request
merged since the last bump is never already in the file, and the version being written
never already has a section: every run adds one new section at the top.

What each entry holds: the pull request's "# Upgrade notes" and each "### " category of
its "# Change log entries" that is not None. The pull request template pre-fills both with
None and keeps its instructions in HTML comments, which are dropped. A pull request that
leaves everything at None gets no entry.

    ## 1.18.0b26

    ### [DEV-10974] Expand candidate info for tap optimization ([#255](https://github.com/...))

    <upgrade notes>

    #### Breaking Changes

    <entries>

    #### Fixes

    <entries>

Parsing and rendering are pure functions; git and GitHub calls are confined to main().
"""

import argparse
import json
import os
import re
import subprocess
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from functools import partial
from itertools import takewhile
from pathlib import Path
from typing import Any

NEWS_FILE = Path("NEWS.md")
NOTES_HEADING = "Upgrade notes"
CHANGELOG_HEADING = "Change log entries"
BUMP_SUBJECT = "Update snapshot "
# A safety bound when no bump commit is found (a repository's first run).
MAX_COMMITS = 100
HEADER = (
    "# News\n\n"
    "Upgrade notes and change log entries for developers using this repository, newest first.\n"
    "CI writes this file from each merged pull request; edit the pull request description, not this file.\n"
)

FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
HEADING = re.compile(r"^(#{1,6})(?=\s)")
MARKDOWN_PUNCTUATION = re.compile(r"([\\`*_\[\]<>])")


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    body: str
    url: str


# Choosing pull requests


def unwritten_commits(log: Iterable[tuple[str, str]]) -> list[str]:
    """Commits (newest first) up to, not including, the last bump commit.

    `log` is the first-parent history as (sha, subject), newest first.
    """
    return [sha for sha, _ in takewhile(lambda commit: not commit[1].startswith(BUMP_SUBJECT), log)]


def merged_pull_request(pulls: list[dict[str, Any]], sha: str) -> PullRequest | None:
    """The pull request whose merge produced `sha`; None for a direct push."""
    for pull in pulls:
        if pull.get("merged_at") and pull.get("merge_commit_sha") == sha:
            return PullRequest(
                number=pull["number"],
                title=pull["title"],
                body=pull.get("body") or "",
                url=pull["html_url"],
            )
    return None


# Parsing the pull request body


def fenced_lines(text: str) -> Iterator[tuple[str, bool]]:
    """Each line with whether it belongs to a fenced code block.

    A fence closes on a line holding only the same character, at least as many times, so a
    longer fence can wrap a shorter one: https://spec.commonmark.org/0.31.2/#fenced-code-blocks
    A fence the author left open is closed after the last line, so it cannot swallow
    whatever is written below the text.
    """
    fence = ""
    for line in text.splitlines():
        match = FENCE.match(line)
        marker, info = match.groups() if match else ("", "")
        if fence:
            yield line, True
            if marker.startswith(fence) and not info.strip():
                fence = ""
        else:
            # Backticks after the opening backticks make the line inline code, not a fence.
            fence = "" if marker.startswith("`") and "`" in info else marker
            yield line, bool(fence)
    if fence:
        yield fence, True


def sections(text: str, prefix: str) -> dict[str, str]:
    """Split markdown at the headings starting with `prefix` (e.g. "# "), ignoring those inside code fences."""
    found: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line, fenced in fenced_lines(text):
        if not fenced and line.startswith(prefix):
            current = found.setdefault(line.removeprefix(prefix).strip(), [])
        elif current is not None:
            current.append(line)
    return {heading: "\n".join(lines).strip() for heading, lines in found.items()}


def is_none(text: str) -> bool:
    """Whether a part of the template was left as it came, or emptied."""
    return text.strip().rstrip(".").lower() in ("", "none", "* none", "- none")


def published(body: str) -> tuple[str, dict[str, str]]:
    """The upgrade notes ("" when None) and the change log categories that are not None."""
    top = sections(COMMENT.sub("", body), "# ")
    notes = top.get(NOTES_HEADING, "")
    categories = sections(top.get(CHANGELOG_HEADING, ""), "### ")
    return ("" if is_none(notes) else notes), {name: text for name, text in categories.items() if not is_none(text)}


# Rendering


def entry_text(text: str) -> str:
    """Author text with its headings pushed below the version (`##`) and entry (`###`) headings."""
    return "\n".join(
        line if fenced else HEADING.sub(lambda match: "#" * min(len(match.group(1)) + 2, 6), line)
        for line, fenced in fenced_lines(text)
    )


def escape(text: str) -> str:
    """Keep a pull request title literal: no links, emphasis, code or HTML tags."""
    return MARKDOWN_PUNCTUATION.sub(r"\\\1", text)


def render_entry(pull_request: PullRequest) -> str:
    """The news entry for a pull request; "" when it has nothing to say."""
    notes, categories = published(pull_request.body)
    parts = [entry_text(notes)] if notes else []
    parts += [f"#### {name}\n\n{entry_text(text)}" for name, text in categories.items()]
    if not parts:
        return ""
    return "\n\n".join([f"### {escape(pull_request.title)} ([#{pull_request.number}]({pull_request.url}))", *parts])


def add_version(news: str, version: str, entries: list[str]) -> str:
    """Put a new version section above the older ones, below the file's introduction."""
    introduction, heading, older = (news if news.strip() else HEADER).partition("\n## ")
    section = "\n\n".join([f"## {version}", *entries])
    return f"{introduction.rstrip()}\n\n{section}\n{heading}{older}"


# Collecting


def collect(commits: list[str], pulls_for: Callable[[str], list[dict[str, Any]]]) -> tuple[list[str], list[str]]:
    """Entries to add (newest first) and a reason for each commit that adds nothing."""
    entries: list[str] = []
    skipped: list[str] = []
    for sha in commits:
        pull_request = merged_pull_request(pulls_for(sha), sha)
        if pull_request is None:
            skipped.append(f"{sha[:7]}: no pull request was merged as this commit")
        elif entry := render_entry(pull_request):
            entries.append(entry)
        else:
            skipped.append(f"#{pull_request.number}: no upgrade notes or change log entries")
    return entries, skipped


# git and GitHub I/O


def run(*command: str) -> str:
    """The command's stdout. Its stderr goes to the job log; a failure stops the run."""
    return subprocess.run(command, check=True, stdout=subprocess.PIPE, text=True).stdout


def first_parent_log(limit: int) -> list[tuple[str, str]]:
    output = run("git", "log", "--first-parent", f"--max-count={limit}", "--format=%H%x1f%s", "HEAD")
    return [(sha, subject) for sha, _, subject in (line.partition("\x1f") for line in output.splitlines())]


def github_pulls(repository: str, sha: str) -> list[dict[str, Any]]:
    """Pull requests associated with a commit. `gh` reads the token from GH_TOKEN or GITHUB_TOKEN.

    https://docs.github.com/en/rest/commits/commits#list-pull-requests-associated-with-a-commit
    """
    return json.loads(run("gh", "api", f"repos/{repository}/commits/{sha}/pulls"))


def write_summary(markdown: str) -> None:
    print(markdown)
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(path, "a", encoding="utf-8") as summary:
            summary.write(markdown + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", required=True, help="Version just published, e.g. 1.18.0b26.")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"), help="owner/name.")
    parser.add_argument("--dry-run", action="store_true", help="Print the file instead of writing and staging it.")
    args = parser.parse_args()
    if not args.repository:
        parser.error("--repository or GITHUB_REPOSITORY is required.")
    return args


def main() -> None:
    args = parse_args()

    commits = unwritten_commits(first_parent_log(MAX_COMMITS + 1))
    warnings = []
    if len(commits) > MAX_COMMITS:
        commits = commits[:MAX_COMMITS]
        warnings.append(f"No `{BUMP_SUBJECT}` commit in the last {MAX_COMMITS} commits; only those were read.")

    entries, skipped = collect(commits, partial(github_pulls, args.repository))
    news = NEWS_FILE.read_text(encoding="utf-8")
    updated = add_version(news, args.version, entries) if entries else news

    if args.dry_run:
        print(updated, end="")
    elif entries:
        NEWS_FILE.write_text(updated, encoding="utf-8")
        run("git", "add", "--", str(NEWS_FILE))

    summary = [f"News for {args.version}: {len(entries)} added from {len(commits)} commits."]
    summary += warnings
    summary += [f"- skipped {reason}" for reason in skipped]
    write_summary("\n".join(summary))


if __name__ == "__main__":
    main()
