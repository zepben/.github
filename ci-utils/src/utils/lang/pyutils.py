import re


class PyUtils():

    def __init__(self, ctx):
        self.ctx = ctx

    def updateSnapshotVersion(self, version: str, project_file: str):
        v = re.search(r"(?P<base>.*)b(?P<beta>\d+)", version)
        if v is None:
            self.ctx.fail(
                f"Couldn't parse the version {version} in {project_file}")

        base = v.group("base")
        beta = (int(v.group("beta")) + 1)
        self.writeNewVersion(
            project_file, version, f"{base}b{beta}")

    def writeNewVersion(self, project_file: str, old: str, new: str):
        if old != new:
            text: str
            self.ctx.info(f"Updating old version '{old}' to new version '{new}'")
            with open(project_file, "r") as p:
                text = re.sub(rf"version\s*=\s*\"{old}\"", f"version=\"{new}\"", p.read())

            # write it up to the file
            with open(project_file, "w") as p:
                p.write(text)

    def parseProjectVersion(self, project_file: str) -> tuple[str, str]:
        with open(project_file, "r") as f:
            text = f.read().split('\n')
            for line in text:
                found_version = re.search(r".*version\s*=\s*\"(?P<version>(?P<sem_version>[0-9]+\.[0-9]+\.[0-9]+)b[0-9]+)\"", line)
                if found_version is not None:
                    return (found_version.group('version'), found_version.group('sem_version'))

        # TODO: handle the fact that no version was parsed
        return ("", "")
