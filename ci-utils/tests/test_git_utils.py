from src.cli import Environment
from src.utils.git import Git
from tests.test_utils.repo import create_repos


ctx = Environment()


branch = "test-branch"
repo_path = create_repos("repo1", branch)
git = Git(ctx, repo_path)


# Delete branch from remote and check it's gone
def test_delete_remote_branch():
    git.delete_remote_branch(branch)
    git.repo.remotes.origin.fetch()
    assert branch not in git.repo.remotes.origin.refs


# This checks the existence of a tag in a remote repo
# Negative test
#    check that some random tag doesn't exist (UUID?)
# Positive test.
#    check that tag1 and tag2 are present
# Check it exists
def test_tag_exists():
    assert git.tag_exists("aklsdfjlasjdlkfjalsdflk") is False
    assert git.tag_exists("tag1") is True
    assert git.tag_exists("tag2") is True


def test_checkout():
    git.checkout("good_branch")
    assert git.repo.head.ref.name == "good_branch"
