from src.cli import pass_environment
from src.utils.git import Git
from src.utils.version import VersionUtils
from src.utils.slack import Slack

import click
import re


@click.command("create-branch",
               short_help="Creates a branch from a list of (lts, hotfix, release)")
@click.option("--type", "btype", required=True, type=click.Choice(["lts", "hotfix", "release"]))
@click.option("--version", required=False, type=str)
@pass_environment
def cli(ctx, btype, version):
    """Creates a branch from a list of (lts, hotfix, release)"""

    if btype != "release" and version is None:
        ctx.err("Err")
    else:
        ctx.log(f"Creating branch of type {btype} for version {version}")

    git = Git()

    # Definitions
    tag: str = None
    version_array: list[str] = None
    commit: str = None
    branch: str = None

    # tag list matching the provided version
    if btype == "release":
        commit = "main"
    elif version:
        tags = [t.name for t in git.repo.tags
                if re.match(rf"{version}\.[0-9]+", t.name)]

        # if found tags, pick the last one
        if len(tags) > 0:
            tag = tags[-1]
            ctx.log(f"Found {tag}")
        else:
            ctx.err(f"Couldn't find the tag for the version {version}")
            return

        version = tag.replace('v', '')
        commit = git.repo.rev_parse(tag)

        # Check that version has the correct pattern
        version_utils = VersionUtils(ctx)
        version_utils.validate_version(version)
        version_array = version.split('.')

        ctx.log(f"commit={commit}")

    match btype:
        case "lts":
            branch = f"LTS/{version_array[0]}.{version_array[1]}.X"
            if branch in git.ls_remotes()["heads"]:
                ctx.fail(
                    "There is already a LTS branch named {branch}.")

        case "hotfix":
            # figure out the next version
            next_version = f"{version_array[0]}.{version_array[1]}.{int(version_array[2]) + 1}"
            if f"v{next_version}" in git.ls_remotes()["tags"]:
                ctx.fail(
                    f"{version} is not the latest tag for {version_array[0]}.{version_array[1]}.")

            ctx.log(next_version)
            branch = f"hotfix/{next_version}"
            if branch in git.ls_remotes()["heads"]:
                ctx.fail(f"There is already a hotfix branch named {branch}.")

        case "release":
            if "release" in git.ls_remotes()["heads"]:
                ctx.fail("There is already a branch named 'release'.")

            branch = "release"

    # info "Creating the branch and checkout"

    ctx.log(f"Checking out {branch} off {commit}")
    try:
        git.repo.head.ref = git.repo.create_head(branch, commit)
        git.repo.head.ref.checkout()
        # TODO: make it static or nest in the ctx
        Slack().send_message(f"/ci-utils/slack-notification.sh \"Created branch {branch}.\"")
        ctx.success("Branch {branch} created successfully")
    except Exception as err:
        ctx.fail(f"Failed to checkout branch {branch}: {err}")
