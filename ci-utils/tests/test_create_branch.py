import os

from src.commands.cmd_create_branch import cli
from click.testing import CliRunner
from tests.test_utils.repo import create_repos 

# Create a couple of repos without any specific branches
path = create_repos("repo1")

def test_create_branch_release():
    os.chdir(path)
    runner = CliRunner()
    result = runner.invoke(cli, ["--type", "lts", "--version", "0.9"])
    print(result.output)
    assert result.exit_code == 0
