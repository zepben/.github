import os
import re

from git import Repo


class Git():

    def __init__(self, ctx):
        self.ctx = ctx
        self.remote_refs = {"heads": [], "tags": []}
        self.init_git()

    def init_git(self):
        self.repo = Repo(os.getcwd())

    # TODO: consider renaming to fetch_remotes() and just use the object field
    # Also, obviously, test if we even need to use ls_remotes or local tags are ok
    def ls_remotes(self):
        # git ls-remote is not wrapped yet
        if self.remote_refs["heads"]:
            return self.remote_refs

        def parse_refs(ref: str):
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
        self.repo.remotes.origin.push(refspec=(f":{branch}"))

    def checkout(self, branch: str):
        ref = ""
        current = "main"
        if branch in self.repo.tags:
            ref = self.repo.commit(branch)
        else:
            ref = self.repo.create_head(branch, current)
        self.repo.head.reference = ref
        self.repo.head.reset(index=True, working_tree=True)
        self.ctx.fail("GIT CHECKOUT BRANCH not implemented yet")

    def stage(self):
        self.ctx.fail("GIT STAGE not implemented yet")

    def status(self):
        self.ctx.fail("GIT STATUS not implemented yet")

    def commit(self, comment: str = ""):
        if len(comment) == 0:
            self.ctx.fail("Cannot commit code without comment!")

        self.ctx.fail("GIT COMMIT is not yet implemented!")

    def push(self, remote, branch):
        self.ctx.fail("Push is not yet implemented!")

    def commit_update_version(self, branch: str = ""):
        if len(branch) == 0:
            branch = "release"

        self.ctx.info(f"Commiting changes to {branch}...")
        self.commit(comment="Update version to next snapshot [skip ci]")
        self.push("origin", branch)
