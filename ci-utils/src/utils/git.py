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
        map(parse_refs, (ref.split('\t')[1] for ref in self.repo.git.ls_remote().split('\n')))
        return self.remote_refs

    def delete_branch(self, branch: str):
       self.ctx.fail("GIT DELETE BRANCH not implemented yet") 
