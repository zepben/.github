import os
import re

from git import Repo, Actor


class Git():

    def __init__(self, ctx):
        self.ctx = ctx
        self.remote_refs = {"heads": [], "tags": []}
        self.init_git()

    def init_git(self):
        self.repo = Repo(os.getcwd())
        self.ls_remotes()

    # TODO: consider renaming to fetch_remotes() and just use the object field
    # Also, obviously, test if we even need to use ls_remotes or local tags are ok
    def ls_remotes(self):
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

    # TODO: check what happens if we just create_head without the second param
    # if that works, then we only need to track the remote branch, everything
    # else should be the same
    def checkout(self, branch: str):
        if branch in self.repo.heads:
            self.repo.create_head(branch, self.repo.remotes.origin.refs[branch])
            self.repo.heads[branch].set_tracking_branch(self.repo.remotes.origin.refs[branch])
        else:
            self.repo.create_head(branch)
        self.repo.heads[branch].checkout()
        self.repo.head.reset(index=True, working_tree=True)

    def stage(self, files: list[str]):
        self.repo.index.add(files)

    def status(self):
        self.ctx.info(self.repo.git.status("-uno"))

    def commit(self, comment: str = ""):
        if len(comment) == 0:
            self.ctx.fail("Cannot commit code without comment!")

        self.repo.index.commit(comment, author=Actor("CI", "ci@zepben.com"))

    def pull(self, branch):
        self.repo.remotes.origin.pull(branch)

    def push(self, branch):
        self.repo.remotes.origin.push(
            refspec=(f"{branch}:{branch}")
        ).raise_if_error()

    def commit_update_version(self, branch: str = ""):
        if len(branch) == 0:
            branch = "release"

        self.ctx.info(f"Commiting changes to {branch}...")
        self.commit(comment="Update version to next snapshot [skip ci]")
        self.push(branch)
