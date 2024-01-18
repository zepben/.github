from src.cli import pass_environment
from src.utils.git import init_git
from src.utils.version import VersionUtils
from src.utils.slack import Slack

import click
import os
import re


@click.command("release-checks",
               help="Make sure commit has not been released, last build was successful and notify team via Slack that release pipeline has been triggered",
               short_help="Perform release checks (commit not released, last build was successful, etc.)")
@click.option("--lang", required=True, type=click.Choice(["jvm", "csharp", "python", "js"]), help="Language that's used for various project file parsing")
@click.option("--project-file", required=True, type=str, help="The project file path, i.e setup.py, pom.xml, etc")
@pass_environment
def cli(ctx, lang, project_file):

    actor = os.getenv('GITHUB_ACTOR')
    branch = os.getenv('GITHUB_REF')

    ctx.info(f"""Running with following parameters:
        language: {lang}
        actor: {actor}
        project file: {project_file}
        branch/ref: {branch}
    """)

    # Do the repo init via the ctx object
    repo = init_git()

    # Fetch just in case
    repo.remotes.origin.fetch(refspec="+refs/heads/*:refs/remotes/origin/*")

    current_commit_id = repo.rev_parse("HEAD")
    ctx.info(f"Checking to make sure commit {current_commit_id} has not been already released.")

    # Versions util
    version_utils = VersionUtils(ctx)
    for tag in repo.tags:
        if current_commit_id == repo.rev_parse(tag):
            ctx.fail(f"Can't run release pipeline. This commit {current_commit_id} is part of the {tag} release.")
        elif re.match(f"[v]?{version_utils.get_sem_version(lang, project_file)}"):
            ctx.fail(f"Can't run release pipeline. There is already a tag for {tag}.")

    Slack().send_message(f"slack-notification.sh \"Release has been triggered for {branch} by *{actor}*\"")
