# Description

A summary of the changes and what they achieve. If there is a ClickUp task with decent detail associated with this change the summary can be brief, otherwise please add some motivation and context here.

If you have added new dependencies to the project please state why.

# Associated tasks

List any other tasks / PRs that are required to be merged alongside this one (e.g. front end task for back end change or vice versa). If a PR exists, add a link. If not, just add an appropriate note here so reviewers know there is a dependency and will hold off merging until all things are ready.

# Test Steps

Explain in detail how your reviewer can test the changes proposed in this PR. If it cannot be tested, leave an explanation on why.

# Checklist

If any of these are not applicable, strikethrough the line `~like this~`. **Do not delete it!**. Let the reviewer decide if you should have done it.

### Code
- [ ] I have performed a self review of my own code (including checking issues raised when creating the PR).
- [ ] I have added/updated unit tests for these changes, and if not I have explained why they are not necessary.
- [ ] I have commented my code in any hard-to-understand or hacky areas.
- [ ] I have handled all new warnings generated by the compiler or IDE.
- [ ] I have rebased onto the target branch (usually main).

### Security
When developing applications, use following guidelines for information security considerations:
* Access to applications should be protected with security keys/tokens or usernames and passwords;
* All sessions are encrypted if possible;
* All application input is sanitised before being acted on (ie SQL statements, etc);
* Log messages, and especially client-facing ones, must be handled securely and must not leak credentials information (internal URLs, passwords, tokens).

- [ ] I have considered if this change impacts information security and made sure those impacts are handled.

### Documentation
- [ ] I have updated the changelog.
- [ ] I have updated any documentation required for these changes.

# Breaking Changes
- [ ] I have considered if this is a breaking change and will communicate it with other team members by posting it on the Slack **breaking-changes** channel.

Please leave a summary of the breaking changes here and then post it on the Slack **breaking-changes** channel to notify the team about it.

# Screenshots

Remove this section if the change cannot be shown through screenshots. Frontend changes should mostly include this section.
Screenshots can be copy-pasted into Github textboxes and a link will automatically be generated.
Remove this text if you choose to use this section.

| Before | After |
| --- | --- |
| ![image](image-link-here) | ![image](image-link-here) |
