from src.cli import pass_environment
from src.utils.git import Git
from src.utils.version import VersionUtils
from src.utils.slack import Slack

import click
import os
import re


@click.command("update-version",
               help="",
               short_help="")
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
              type=str,
              default=False,
              show_default=True,
              help="Only update the project file without committing")
@click.option("--snapshot",
              is_flag=True,
              required=False, 
              type=str, default=False,
              show_default=True,
              help="Increments the snapshot version. Only useful for C# and Python, ie 1.0.0-pre1, 1.0.0b1. Java doesn't have this concept.")
@click.option("--release",
              is_flag=True,
              required=False,
              type=str,
              default=False,
              show_default=True,
              help="Use this option on create release step")
@click.option("--grow-changelog",
              is_flag=True,
              required=False,
              type=str,
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

    # Do the repo init via the ctx object
    git = Git()

    # Fetch just in case
    if no_commit:
        git.repo.remotes.origin.fetch(refspec="+refs/heads/*:refs/remotes/origin/*")

    # if --release, drop the current branch and release branch
    branch = os.getenv('GITHUB_REF_NAME', None)
    if branch:
        ctx.info(f"Running on branch: {branch}")
        if release and re.match(".*hotfix/.*", branch):
            git.delete_branch(branch)
            if "remotes/origin/release" in git.repo.refs:
                git.delete_branch("release")
            os.exit(0)
    else:
        ctx.fail("Cannot detect branch name!")
    #
    # BRANCH=${BITBUCKET_BRANCH:=${GITHUB_REF:?'Branch ref was missing, was this run in github or bitbucket?'}}
    # BRANCH=${BRANCH/refs\/heads\//}
    # info "Branch: $BRANCH"
    # if [[ " ${options[@]} " =~ " --release " && $BRANCH = *"hotfix/"* ]]; then
    #     run git push origin -d $BRANCH
    #     if [[ ! -z $(git branch -a | grep remotes/origin/release) ]]; then
    #         run git push origin -d release
    #     fi
    #     exit 0
    # fi
    #
    # file=${args[0]:?'File variable missing.'}
    #

    if not os.path.exists(project_file):
        ctx.fail(f"The provided {project_file} doesn't seem to exist!")

    # -----
    # optional variables

    # Update project version
    ctx.log("Updating version...")

    utils = VersionUtils(ctx)
    if snapshot:
        # build_lang ${options[@]}
        utils.update_snapshot_version(lang, project_file)
    # else


#     # Checkout release branch
#     if [[ ! " ${options[@]} " =~ " --no-commit " ]]; then
#         if [[ " ${options[@]} " =~ " --release " ]]; then
#             if [[ -z $(git branch -a | grep remotes/origin/release) ]]; then
#                 run git checkout -b release
#             else
#                 run git checkout release
#             fi
#         else
#             run git checkout $BRANCH
#         fi
#     fi
#     build_lang ${options[@]}
#
#     # Determine which version to update
#     if [[ $BRANCH = "LTS/"* || $BRANCH = "hotfix/"* ]]; then
#         version_type="patch"
#     else
#         version_type="minor"
#     fi
#
#     update_version
# fi

