import os
import pytest

from pathlib import Path

from src.commands.cmd_update_version import cli
from src.utils.version import VersionUtils
from click.testing import CliRunner
from tests.test_utils.repo import create_repos_with_tags_branches
from tests.test_utils.configs import configs, goodbranch

from src.cli import Environment
from src.utils.git import Git

# Create a couple of repos without any specific branches
runner = CliRunner()


@pytest.fixture
def local_path():
    yield Path().absolute()


@pytest.fixture
def local_repo_name(name: str = "local") -> str:
    yield name


@pytest.fixture
def repo_path(local_repo_name: str, local_path, request):
    yield create_repos_with_tags_branches(name=local_repo_name, include_project_files=True)
    os.chdir(local_path)


def test_update_snapshot_version(repo_path):
    ctx = Environment()
    for config in configs.values():
        # Test command: ci update_version --lang ... --project-file  --snapshot
        #   will test all languages and project files
        os.chdir(repo_path)

        # checkout a branch different from main
        git = Git(ctx)
        git.checkout(goodbranch)

        runner.invoke(cli, 
              ["--lang", config.lang, 
               "--project-file", config.project_file, 
               "--snapshot"])

        # now fetch it and check the version was updated
        utils = VersionUtils(ctx, config.lang, config.project_file)
        version, sem_version = utils.lang_utils.parseProjectVersion(config.project_file)
        assert version == f"{config.next_snapshot}"

        # now check it's been pushed to the origin
        for br in git.repo.remotes.origin.refs:
            if br.name.split("/")[-1] == "good-branch":
                assert git.repo.head.commit.hexsha == br.commit.hexsha

def test_update_version(repo_path):
    ctx = Environment()
    for config in configs.values():
        # Test command: ci update_version --lang ... --project-file  --snapshot
        #   will test all languages and project files
        os.chdir(repo_path)

        # checkout a branch different from main
        git = Git(ctx)
        git.checkout(goodbranch)

        runner.invoke(cli, 
              ["--lang", config.lang, 
               "--project-file", config.project_file, 
               "--snapshot"])

        # now fetch it and check the version was updated
        utils = VersionUtils(ctx, config.lang, config.project_file)
        version, sem_version = utils.lang_utils.parseProjectVersion(config.project_file)
        assert version == f"{config.next_snapshot}"

        # now check it's been pushed to the origin
        for br in git.repo.remotes.origin.refs:
            if br.name.split("/")[-1] == "good-branch":
                assert git.repo.head.commit.hexsha == br.commit.hexsha
