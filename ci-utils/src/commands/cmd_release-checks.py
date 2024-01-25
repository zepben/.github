from src.cli import pass_environment
from src.utils.git import Git
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
    branch = os.getenv('GITHUB_REF_NAME')

    ctx.info(f"""Running with following parameters:
        language: {lang}
        actor: {actor}
        project file: {project_file}
        branch/ref: {branch}
    """)

    # Do the repo init via the ctx object
    git = Git()

    # Fetch just in case
    git.repo.remotes.origin.fetch(refspec="+refs/heads/*:refs/remotes/origin/*")

    current_commit_id = git.repo.rev_parse("HEAD")
    ctx.info(f"Checking to make sure commit {current_commit_id} has not been already released.")

    # Versions util
    version_utils = VersionUtils(ctx, lang, project_file)
    for tag in git.repo.tags:
        if current_commit_id == git.repo.rev_parse(tag):
            ctx.fail(f"Can't run release pipeline. This commit {current_commit_id} is part of the {tag} release.")
        else:
            version_utils.get_versions()
            if re.match(f"[v]?{version_utils.sem_version}"):
                ctx.fail(f"Can't run release pipeline. There is already a tag for {tag}.")

    Slack(ctx).send_message(f"Release has been triggered for {branch} by *{actor}*")
