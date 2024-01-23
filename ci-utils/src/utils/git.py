import os
import re

from git import Repo


class Git():

    def __init__(self, ctx):
        self.ctx = ctx
        self.remote_refs = {"heads": None, "tags": None}
        self.init_git()

    def init_git(self) -> Repo:
        self.repo = Repo(os.getcwd())

    # TODO: consider renaming to fetch_remotes() and just use the object field
    # Also, obviously, test if we even need to use ls_remotes or local tags are ok
    def ls_remotes(self) -> iter:
        # git ls-remote is not wrapped yet
        if self.remote_refs["heads"]:
            return self.remote_refs

        def parse_refs(ref: str) -> dict[str: list[str]]:
            found_ref = re.search(".*(?P<ref_type>heads|tags).*", ref)
            if found_ref:
                ref_type = found_ref.group("ref_type")
                # only keep the actual tag or reference (branch) name
                self.remote_refs[ref_type].append(found_ref.group(0).split('/')[-1])

        # Now filter out heads/tags
        map(parse_refs,
            (ref.split('\t')[1] for ref in self.repo.git.ls_remote().split('\n')))
        return self.remote_refs

    def delete_remote_branch(self, branch: str):
        self.ctx.fail("GIT DELETE BRANCH not implemented yet")

    def checkout(self, branch: str):
        self.ctx.fail("GIT CHECKOUT BRANCH not implemented yet")

    def stage(self):
        self.ctx.fail("GIT STAGE not implemented yet")

    def status(self):
        self.ctx.fail("GIT STATUS not implemented yet")

    def commit(self, comment: str = None):
        if not comment:
            self.ctx.fail("Cannot commit code without comment!")

        self.ctx.fail("GIT COMMIT is not yet implemented!")

    def push(self, remote, branch):
        self.ctx.fail("Push is not yet implemented!")

    def commit_update_version(self, branch: str = None):
        if not branch:
            branch = "release"

        self.ctx.info(f"Commiting changes to {branch}...")
        self.commit(comment="Update version to next snapshot [skip ci]")
        self.push("origin", branch)
