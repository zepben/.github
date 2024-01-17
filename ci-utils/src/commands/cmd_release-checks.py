from src.cli import pass_environment

import click
import os
import re
import json
import xml.etree.ElementTree as ET
from git import Repo


@click.command("release-checks",
               help="Make sure commit has not been released, last build was successful and notify team via Slack that release pipeline has been triggered",
               short_help="Perform release checks(commit not released, last build was successful, etc.)")
@click.option("--lang", required=True, type=click.Choice(["jvm", "csharp", "python", "js"]))
@click.option("--project-file", required=True, type=str)
@pass_environment
def cli(ctx, lang, project_file):

    actor = os.getenv('GITHUB_ACTOR')
    branch = os.getenv('GITHUB_REF')

    ctx.info(f"""Running with following parameters:
        language: {lang}
        actor: {actor}
        project file: {project_file}
        branch/ref: {branch}"
    """)

    # This seems to be just sourcing stuff...
    # build_lang ${options[@]}

    # Fetch just in case
    repo.remotes.origin.fetch(t="tags", "+refs/heads/*:refs/remotes/origin/*")

    current_commit_id = repo.rev_parse("HEAD")
    ctx.info("Checking to make sure commit {current_commit_id} has not been already released.")

    for tag in repo.tags:
        if current_commit_id == repo.rev_parse(tag):
            ctx.fail(f"Can't run release pipeline. This commit {current_commit_id} is part of the {tag} release.")

        elif [[ $tag =~ [v]?${sem_version()} ]]; then
            fail "Can't run release pipeline. There is already a tag for ${tag}."
        fi
    done



    # Do the repo init via the ctx object
    # repo = init_git()

    # match lang:
    #     case "js":
    #         lts_branch_name = f"LTS/{version_array[0]}.{version_array[1]}.X"
    #         if lts_branch_name in ls_remotes(repo)["heads"]:
    #             ctx.err(
    #                 "There is already a LTS branch named {lts_branch_name}.")
    #             exit
    #         branch = lts_branch_name
    #     case "csharp":
    #
    #         # figure out the next version
    #         next_version = f"{version_array[0]}.{version_array[1]}.{int(version_array[2]) + 1}"
    #         if f"v{next_version}" in ls_remotes(repo)["tags"]:
    #             ctx.err(
    #                 f"{version} is not the latest tag for {version_array[0]}.{version_array[1]}.")
    #             exit
    #
    #         ctx.log(next_version)
    #         hotfix_branch_name = f"hotfix/{next_version}"
    #         if hotfix_branch_name in ls_remotes(repo)["heads"]:
    #             ctx.err(
    #                 "There is already a hotfix branch named {hotfix_branch_name}.")
    #             exit
    #
    #         branch = hotfix_branch_name
    #
    #     case "jvm":
    #         if "release" in ls_remotes(repo)["heads"]:
    #             ctx.err("There is already a branch named 'release'.")
    #             exit
    #
    #         branch = "release"
    #
    #     case "python":
    #         click.echo("python not implemented yet")


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


def sem_version(lang: str, project_file: str) -> str:

    # Check that file exists

    version: str = None

    match lang:
        case "js":
            # we expect the file to be json
            with open(project_file) as f:
                project = json.load(f)
                project_version = project.get("version", None)
                if project_version:
                    version = project_version.split("-")[0]

        case "jvm": pass
        case "python": pass
        case "csharp":
            if project_file.endswith(".csproj"):
                try:
                    tree = ET.parse(project_file)
                    project_version = tree.root.find("Project").find("PropertyGroup").find("Version").text
                    if project_version:
                        version = project_version.split("-")[0]
                except Exception as err:
                    ctx.err(f"Couldn't find the project version in the /Project/PropertyGroup/Version field in the {project_file}: {err}")
            elif project_file.endswith(".nuspec"):
                try:
                    tree = ET.parse(project_file)
                    project_version = tree.root.find("package").find("metadata").find("version").text
                    if project_version:
                        version = project_version.split("-")[0]
                except Exception as err:
                    ctx.err(f"Couldn't find the project version in the /project/metadata/version field in the {project_file}: {err}")
            elif project_file.endswith("AssemblyInfo.cs"):
                with open(project_file, "r") as f:
                    lines = f.readall().split('\n')
                    for line in lines:
                        found_ver = re.search(".*AssemblyVersion\((\"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\")\)", line) 
                        if found_ver:
                            version = found_ver.group(1)
                            break

    return version
