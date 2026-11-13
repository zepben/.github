"""Tests for announce.py. Run: python3 -m unittest discover -s .github/actions/merge-announcement"""

import unittest

from announce import (
    ChangeNotes,
    PullRequest,
    breaking_changes,
    create_merge_task,
    parse,
    release_of,
    render_announcement,
    render_breaking_announcement,
    render_task_body,
    task_line,
    ticket_name,
)

CHANGELOG = """### Breaking Changes
* None.

### New Features
* None.

### Enhancements
* Voltage line upgrade interventions now use `sizingLookaheadYears` to limit the number of years considered.

### Fixes
* None.

### Notes
* None."""

# The commons pull request template, filled in as for DEV-11313 (1.18.0b24).
BODY = f"""> [!IMPORTANT]
> Until automation is in place, it is up to the person merging to ensure the ticket is updated.

# Description

> [!IMPORTANT]
> This description will be used to populate clickup tickets, so don't just use "as per title" or the like.

Adds `sizingLookaheadYears` to `VoltageLineUpgrade` candidate generation method config.

- EAS will need to populate `sizingLookaheadYears` for `VoltageLineUpgrade`.

# Application change log updates

This is a modified copy of the change log.

```markdown
{CHANGELOG}
```

# Associated tasks

None.

# Breaking Changes
- [x] I have considered if this is a breaking change.
"""

PULL_REQUEST = PullRequest(
    number=256,
    title="[DEV-10978] align voltage line candidate info with PRRP",
    body=BODY,
    author="Lax125",
    url="https://github.com/zepben/commons/pull/256",
)


class ParsingChangeNotes(unittest.TestCase):
    def test_change_notes_are_the_description_and_the_change_log_block(self):
        notes = parse(BODY)
        self.assertEqual(
            notes.description,
            "Adds `sizingLookaheadYears` to `VoltageLineUpgrade` candidate generation method config.\n\n"
            "- EAS will need to populate `sizingLookaheadYears` for `VoltageLineUpgrade`.",
        )
        self.assertEqual(notes.changelog, CHANGELOG)

    def test_template_alerts_are_not_part_of_the_description(self):
        self.assertNotIn("[!IMPORTANT]", parse(BODY).description)

    def test_bodies_with_windows_line_endings_parse_the_same(self):
        self.assertEqual(parse(BODY.replace("\n", "\r\n")), parse(BODY))

    def test_headings_inside_code_fences_do_not_end_a_section(self):
        body = BODY.replace("- EAS will", "```bash\n# not a heading\n```\n- EAS will")
        self.assertIn("# not a heading", parse(body).description)

    def test_a_body_without_a_change_log_block_has_no_change_notes(self):
        self.assertIsNone(parse("# Description\n\nSomething.\n\n# Test Steps\n\nNone."))
        self.assertIsNone(parse("# Application change log updates\n\nNo block here."))


class BreakingChanges(unittest.TestCase):
    def test_none_means_no_breaking_changes(self):
        self.assertEqual(breaking_changes(CHANGELOG), "")
        self.assertEqual(breaking_changes(CHANGELOG.replace("* None.", "* None", 1)), "")

    def test_breaking_change_entries_are_returned(self):
        changelog = CHANGELOG.replace("* None.", "* `phase` is now nullable.\n  * Callers must handle null.", 1)
        self.assertEqual(breaking_changes(changelog), "* `phase` is now nullable.\n  * Callers must handle null.")


class Versions(unittest.TestCase):
    def test_a_snapshot_belongs_to_its_release(self):
        self.assertEqual(release_of("1.18.0b24"), "1.18.0")

    def test_a_release_version_is_not_a_snapshot(self):
        with self.assertRaises(ValueError):
            release_of("1.18.0")


class Rendering(unittest.TestCase):
    def test_task_is_the_name_of_the_first_clickup_ticket_in_the_pull_request_title_linking_to_it(self):
        pull_request = PullRequest(1, "[DEV-1] [DEV-2] Thing", "", "a", "https://pr")
        self.assertEqual(
            task_line(pull_request, "6929263", "Ticket [name]"),
            "[Ticket \\[name\\]](https://app.clickup.com/t/6929263/DEV-1)",
        )

    def test_task_is_the_linked_pull_request_title_when_the_title_names_no_ticket(self):
        pull_request = PullRequest(289, "Add tie points", "", "a", "https://github.com/zepben/x/pull/289")
        self.assertEqual(
            task_line(pull_request, "6929263", None),
            "PR: [Add tie points](https://github.com/zepben/x/pull/289)",
        )

    def test_task_says_when_the_ticket_name_is_unavailable_and_shows_the_pull_request_title(self):
        pull_request = PullRequest(1, "[DEV-1] Thing", "", "a", "https://pr")
        self.assertEqual(
            task_line(pull_request, "6929263", None),
            "[\\[DEV-1\\] Thing](https://app.clickup.com/t/6929263/DEV-1) "
            "(ticket name unavailable; this is the pull request title)",
        )

    def test_task_body_follows_the_maintenance_backlog_format(self):
        notes = ChangeNotes(description="Notes.", changelog=CHANGELOG)
        self.assertEqual(
            render_task_body(PULL_REQUEST, notes, "6929263", "Align voltage line candidate info"),
            "#### Task: [Align voltage line candidate info]"
            "(https://app.clickup.com/t/6929263/DEV-10978)\n\n"
            "#### Pull request: https://github.com/zepben/commons/pull/256\n\n"
            "#### Action/dev notes:\nNotes.\n\n"
            f"#### Change log updates:\n\n```markdown\n{CHANGELOG}\n```\n",
        )

    def test_announcement_matches_the_maintenance_backlog_format(self):
        self.assertEqual(
            render_announcement("COMMONS", "1.18.0b24", PULL_REQUEST, "https://app.clickup.com/t/6929263/DEV-11313"),
            "App: COMMONS\n"
            "Version: 1.18.0b24\n"
            "Description: [DEV-10978] align voltage line candidate info with PRRP (#256)\n"
            "Author: Lax125\n"
            "Task: https://app.clickup.com/t/6929263/DEV-11313",
        )

    def test_slack_control_characters_in_pull_request_text_are_escaped(self):
        pull_request = PullRequest(1, "Use List<T> & friends", "", "a", "https://pr")
        announcement = render_announcement("APP", "1.0.0b1", pull_request, "https://task")
        self.assertIn("Description: Use List&lt;T&gt; &amp; friends (#1)", announcement)
        self.assertTrue(render_breaking_announcement("x", "* a -> b").endswith("* a -&gt; b"))


class FakeClickUp:
    """Serves the backlog task with the given subtasks; each created task's ID is derived from its name."""

    def __init__(self, subtasks):
        self.calls = []
        self._subtasks = subtasks

    def request(self, method, path, body=None, **query):
        self.calls.append((method, path, body))
        if method == "GET":
            return {"id": "backlog", "list": {"id": "list"}, "subtasks": self._subtasks}
        return {"id": f"created-{body['name']}", "custom_id": "DEV-11313"}


class TicketName(unittest.TestCase):
    class Tickets:
        def __init__(self, response):
            self.calls = []
            self._response = response

        def request(self, method, path, body=None, **query):
            self.calls.append((method, path, query))
            if isinstance(self._response, Exception):
                raise self._response
            return self._response

    def test_the_ticket_name_is_read_from_clickup(self):
        clickup = self.Tickets({"name": "Trace per AUP"})
        self.assertEqual(ticket_name(clickup, "6929263", PULL_REQUEST), "Trace per AUP")
        self.assertEqual(
            clickup.calls, [("GET", "/task/DEV-10978", {"custom_task_ids": "true", "team_id": "6929263"})]
        )

    def test_a_title_without_a_ticket_has_no_ticket_name_and_calls_nothing(self):
        clickup = self.Tickets({"name": "unused"})
        pull_request = PullRequest(289, "Add tie points", "", "a", "https://pr")
        self.assertIsNone(ticket_name(clickup, "6929263", pull_request))
        self.assertEqual(clickup.calls, [])

    def test_an_unreadable_ticket_has_no_ticket_name(self):
        clickup = self.Tickets(RuntimeError("ClickUp GET failed: HTTP 404"))
        self.assertIsNone(ticket_name(clickup, "6929263", PULL_REQUEST))


class CreatingTheMergeTask(unittest.TestCase):
    def test_the_task_is_created_under_the_existing_release_subtask(self):
        clickup = FakeClickUp([{"id": "older", "name": "1.17.0"}, {"id": "release", "name": "1.18.0"}])
        task_url = create_merge_task(clickup, "DEV-3959", "6929263", "1.18.0b24", "body")
        self.assertEqual(task_url, "https://app.clickup.com/t/6929263/DEV-11313")
        self.assertEqual(
            clickup.calls[1:],
            [("POST", "/list/list/task", {"name": "1.18.0b24", "parent": "release", "markdown_content": "body"})],
        )

    def test_a_missing_release_subtask_is_created_first(self):
        clickup = FakeClickUp([{"id": "older", "name": "1.17.0"}])
        create_merge_task(clickup, "DEV-3959", "6929263", "1.18.0b1", "body")
        self.assertEqual(
            clickup.calls[1:],
            [
                ("POST", "/list/list/task", {"name": "1.18.0", "parent": "backlog"}),
                (
                    "POST",
                    "/list/list/task",
                    {"name": "1.18.0b1", "parent": "created-1.18.0", "markdown_content": "body"},
                ),
            ],
        )

    def test_a_release_version_is_rejected_before_clickup_is_called(self):
        clickup = FakeClickUp([])
        with self.assertRaises(ValueError):
            create_merge_task(clickup, "DEV-3959", "6929263", "1.18.0", "body")
        self.assertEqual(clickup.calls, [])


if __name__ == "__main__":
    unittest.main()
