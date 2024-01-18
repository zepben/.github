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
        branch/ref: {branch}
    """)

    # This seems to be just sourcing stuff...
    # build_lang ${options[@]}

    # Do the repo init via the ctx object
    repo = init_git()

    # Fetch just in case, hopefully this fetches all including tags
    repo.remotes.origin.fetch(refspec="+refs/heads/*:refs/remotes/origin/*")

    current_commit_id = repo.rev_parse("HEAD")
    ctx.info(f"Checking to make sure commit {current_commit_id} has not been already released.")

    for tag in repo.tags:
        if current_commit_id == repo.rev_parse(tag):
            ctx.fail(f"Can't run release pipeline. This commit {current_commit_id} is part of the {tag} release.")
        elif re.match(f"[v]?{get_sem_version(ctx, lang, project_file)}"):
            ctx.fail(f"Can't run release pipeline. There is already a tag for {tag}.")

    ctx.run(f"slack-notification.sh \"Release has been triggered for {branch} by *{actor}*\"")


# this will go to the utils package
def init_git() -> Repo:
    return Repo(os.getcwd())


def validate_version(ctx, version: str):
    if not re.match("[0-9]+.[0-9]+.[0-9]+", version):
        ctx.fail(
            f"Could not proceed due to the tag {version} not having #.#.# format.")

    version_array = version.split('.')
    if len(version_array) > 3:
        ctx.fail(
            f"Version {version} had more than 3 parts and is not a valid version. Did you enter the correct minor version?")


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


def get_sem_version(ctx, lang: str, project_file: str) -> str:

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

        case "jvm":
            # POM
            if project_file.endswith(".xml"):
                project: str = None
                tree = ET.parse(project_file)
                for v in tree.getroot().attrib.values():
                    for p in v.split():
                        if re.match(".*apache.*POM.*", p):
                            project = "{" + p + "}"

                if project:
                    v = tree.getroot().findall(f"{project}version")
                    if len(v) == 1:
                        # v[0].text is the value of the version field
                        # we split by '-' (-SNAPSHOT) and take the first part
                        version = v[0].text.split('-')[0]
                    else:
                        ctx.fail(f"Error parsing version in {project_file}, either none found or too many")
                else:
                    ctx.fail(f"Couldn't find project in {project_file}. Project is XML namespace, and for POM it's expected to be something like 'http://maven.apache.org/POM/4.0.0'")
            else:
                ctx.fail("Project file for java projects should be in POM XML format")

        case "python": 
            with open(project_file, "r") as f:
                text = f.read().split('\n')
                for line in text:
                    found_version = re.search(r".*version\s*=\s*\"(?P<version>[0-9]+\.[0-9]+\.[0-9]+)b[0-9]+\"", line)
                    if found_version:
                        version = found_version.group('version')

        case "csharp":
            if project_file.endswith(".csproj"):
                try:
                    tree = ET.parse(project_file)
                    project_version = tree.root.find("Project").find("PropertyGroup").find("Version").text
                    if project_version:
                        version = project_version.split("-")[0]
                except Exception as err:
                    ctx.fail(f"Couldn't find the project version in the /Project/PropertyGroup/Version field in the {project_file}: {err}")
            elif project_file.endswith(".nuspec"):
                try:
                    tree = ET.parse(project_file)
                    project_version = tree.root.find("package").find("metadata").find("version").text
                    if project_version:
                        version = project_version.split("-")[0]
                except Exception as err:
                    ctx.fail(f"Couldn't find the project version in the /project/metadata/version field in the {project_file}: {err}")
            elif project_file.endswith("AssemblyInfo.cs"):
                with open(project_file, "r") as f:
                    lines = f.readall().split('\n')
                    for line in lines:
                        found_ver = re.search(r".*AssemblyVersion\(\"(?P<version>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\"\)", line) 
                        if found_ver:
                            version = found_ver.group('version')
                            break

    if not version:
        # If version not found
        ctx.fail(f"Error parsing {project_file}. Check that {lang} is matching and the format of the file is correct.")

    return version
