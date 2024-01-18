import os
import re

from git import Repo


def init_git() -> Repo:
    return Repo(os.getcwd())


def ls_remotes(repo: Repo) -> iter:
    # git ls-remote is not wrapped yet
    refs = {"heads": [], "tags": []}

    def parse_refs(ref: str) -> dict[str: list[str]]:
        found_ref = re.search(".*(?P<ref_type>heads|tags).*", ref)
        if found_ref:
            ref_type = found_ref.group("ref_type")
            # only keep the actual tag or reference (branch) name
            refs[ref_type].append(found_ref.group(0).split('/')[-1])

    # Now filter out heads/tags
    map(parse_refs, (ref.split('\t')[1] for ref in repo.git.ls_remote().split('\n')))
    return refs
