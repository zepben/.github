from src.cli import pass_environment

import click
import os
import re
from git import Repo


@click.command("create-branch",
               short_help="Creates a branch from a list of (lts, hotfix, release)")
@click.option("--btype", required=True, type=click.Choice(["lts", "hotfix", "release"]))
@click.option("--version", required=False, type=str)
@pass_environment
def cli(ctx, btype, version):
    """Creates a branch from a list of (lts, hotfix, release)"""

    if btype != "release" and version is None:
        ctx.err("Err")
    else:
        ctx.log(f"Creating branch of type {btype} for version {version}")

    # Do the repo init via the ctx object
    repo = init_git()

    # Definitions
    tag: str = None
    version_array: list[str] = None
    commit: str = None
    branch: str = None

    # tag list matching the provided version
    if btype == "release":
        commit = "main"
    elif version:
        tags = [t.name for t in repo.tags
                if re.match(f"{version}\\.[0-9]+", t.name)]

        # if found tags, pick the last one
        if len(tags) > 0:
            tag = tags[-1]
            ctx.log(f"Found {tag}")
        else:
            ctx.err(f"Couldn't find the tag for the version {version}")
            return

        version = tag.replace('v', '')
        commit = repo.rev_parse(tag)

        # Check that version has the correct pattern
        validate_version(ctx, version)
        version_array = version.split('.')

        ctx.log(f"commit={commit}")

    match btype:
        case "lts":
            lts_branch_name = f"LTS/{version_array[0]}.{version_array[1]}.X"
            if lts_branch_name in ls_remotes(repo)["heads"]:
                ctx.err(
                    "There is already a LTS branch named {lts_branch_name}.")
                exit
            branch = lts_branch_name
        case "hotfix":

            # figure out the next version
            next_version = f"{version_array[0]}.{version_array[1]}.{int(version_array[2]) + 1}"
            if f"v{next_version}" in ls_remotes(repo)["tags"]:
                ctx.err(
                    f"{version} is not the latest tag for {version_array[0]}.{version_array[1]}.")
                exit

            ctx.log(next_version)
            hotfix_branch_name = f"hotfix/{next_version}"
            if hotfix_branch_name in ls_remotes(repo)["heads"]:
                ctx.err(
                    "There is already a hotfix branch named {hotfix_branch_name}.")
                exit

            branch = hotfix_branch_name

        case "release":
            if "release" in ls_remotes(repo)["heads"]:
                ctx.err("There is already a branch named 'release'.")
                exit

            branch = "release"

    # info "Creating the branch and checkout"

    ctx.log(f"Checking out {branch} off {commit}")
    try:
        repo.head.ref = repo.create_head(branch, commit)
        repo.head.ref.checkout()
        # TODO:
        # click.run(
        #     f"/ci-utils/slack-notification.sh \"Created branch {branch}.\"")
        # ctx.success("Branch {branch} created successfully")
    except Exception as err:
        ctx.err(f"Couldn't checkout branch {branch}: {err}")


# this will go to the utils package
def init_git() -> Repo:
    return Repo(os.getcwd())


def validate_version(ctx, version: str):
    if not re.match("[0-9]+.[0-9]+.[0-9]+", version):
        ctx.err(
            f"Could not proceed due to the tag {version} not having #.#.# format.")
        exit

    version_array = version.split('.')
    if len(version_array) > 3:
        ctx.err(
            f"Version {version} had more than 3 parts and is not a valid version. Did you enter the correct minor version?")
        exit


def ls_remotes(repo: Repo) -> iter:
    # git ls-remote is not wrapped yet
    refs = {"heads": [], "tags": []}

    def parse_refs(ref: str) -> dict[str: list[str]]:
        found_ref = re.search(".*(heads|tags).*", ref)
        if found_ref:
            ref_type = found_ref.group(1)
            # only keep the actual tag or reference (branch) name
            refs[ref_type].append(found_ref.group(0).split('/')[2])

    # Now filter out heads/tags
    map(parse_refs, (ref.split('\t')[1] for ref in repo.git.ls_remote().split('\n')))
    return refs
