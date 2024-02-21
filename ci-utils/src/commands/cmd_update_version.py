from src.cli import pass_environment
from src.utils.git import Git
from src.utils.version import VersionUtils

import click
import os
import re


@click.command("update-version",
               help="Update the project version to the next one (patch version for LTS, minor version for all others).",
               short_help="Update the project version to the next one (patch version for LTS, minor version for all others)."
               )
@click.option("--lang",
              required=True,
              type=click.Choice(["jvm", "csharp", "python", "js"]),
              help="Language that's used for various project file parsing")
@click.option("--project-file",
              required=True,
              type=str,
              help="The project file path, i.e setup.py, pom.xml, etc")
@click.option("--changelog-file",
              required=False,
              type=str,
              default="changelog.md",
              show_default=True,
              help="The changelog file path, i.e changelog.md")
@click.option("--no-commit",
              is_flag=True,
              required=False,
              type=bool,
              default=False,
              show_default=True,
              help="Only update the project file without committing")
@click.option("--snapshot",
              is_flag=True,
              required=False,
              type=bool,
              default=False,
              show_default=True,
              help="Increments the snapshot version. Only useful for C# and Python, ie 1.0.0-pre1, 1.0.0b1. Java doesn't have this concept.")
@click.option("--release",
              is_flag=True,
              required=False,
              type=bool,
              default=False,
              show_default=True,
              help="Use this option on create release step")
@click.option("--grow-changelog",
              is_flag=True,
              required=False,
              type=bool,
              default=False,
              show_default=True,
              help="Updates changelog by inserting EDNAR-style template instead of resetting it to the regular one.")
@pass_environment
def cli(ctx, lang, project_file, changelog_file, no_commit, snapshot, release, grow_changelog):

    ctx.info(f"""Running with following parameters:
        language: {lang}
        project file: {project_file}
        changelog file: {changelog_file}
        no-commit: {no_commit}
        snapshot: {snapshot}
        release: {release}
        grow-changelog: {grow_changelog}
    """)

    # Do the repo init via the ctx object?
    git = Git(ctx)

    # Fetch just in case
    if no_commit:
        git.repo.remotes.origin.fetch(refspec="+refs/heads/*:refs/remotes/origin/*")

    branch = os.getenv('GITHUB_REF', git.repo.active_branch.name)
    if branch:
        ctx.info(f"Running on branch: {branch}")
        # if --release, drop the current branch and release branch and ...we're done??
        if release and re.match(".*hotfix/.*", branch):
            git.delete_remote_branch(branch)
            if "remotes/origin/release" in git.remote_refs['heads']:
                git.delete_remote_branch("release")
            os.exit(0)
        else:
            # checkout the branch
            ctx.info(f"Checking out {branch}")
            git.checkout(branch)
    else:
        ctx.fail("Cannot detect branch name!")

    if not os.path.exists(project_file):
        ctx.fail(f"The provided {project_file} doesn't seem to exist!")

    # Update project version
    ctx.info("Updating version...")

    utils = VersionUtils(ctx, lang=lang, project_file=project_file)

    if snapshot:
        utils.update_snapshot_version()
    else:
        # TODO: consider uniting both ifs
        if not no_commit:
            if release:
                # if remotes/origin/release exists, check it out.
                # else, create a new branch
                git.checkout("release")
            else:
                # what is this. We should be checked out already
                git.checkout(branch)

        version_type = "patch" if re.match(".*[LTS|hotfix]/.*", branch) else "minor"
        utils.update_version(version_type)

    # Update changelog
    if changelog_file:
        utils.update_changelog(grow_changelog, changelog_file)

    # stage updates
    git.stage([project_file, changelog_file])
    # show status for debugging
    git.status()

    # TODO: Double negative yay
    if not no_commit:
        if release:
            git.commit_update_version()
            git.checkout(branch)
            git.pull("release")
            git.push(branch)
            git.delete_remote_branch("release")
        else:
            git.commit_update_version(branch)
