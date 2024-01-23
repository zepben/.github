import re


class PyUtils():

    ctx: str

    def __init__(self, ctx):
        self.ctx = ctx

    def updateSnapshotVersion(self, version: str, project_file: str):
        v = re.search(r"(?P<base>.*)b(?P<beta>\d+)", version)
        if not v:
            self.ctx.fail(
                f"Couldn't parse the version {version} in {project_file}")

        base = v.group("base")
        beta = (int(v.group("beta")) + 1)
        self.writeNewVersion(
            self.ctx, project_file, version, f"${base}b{beta}")

    def writeNewVersion(self, project_file: str, old: str, new: str):
        if old != new:
            text: str
            self.ctx.info(f"Writing new version {new}")
            with open(project_file, "r") as p:
                text = p.readall()
                text.replace(fr"version\s*=\s*{old}", fr"version\s*=\s*{new}")

            # now all lines are updated, so write it up to the file
            with open(project_file, "w") as p:
                p.write(text)

    def parseProjectVersion(self, project_file: str) -> (str, str):
        with open(project_file, "r") as f:
            text = f.readall().split('\n')
            for line in text:
                found_version = re.search(
                    r".*version\s*=\s*\"(?P<sem_version>(?P<version>[0-9]+\.[0-9]+\.[0-9]+)b[0-9]+)\"", line)
                if not found_version:
                    self.ctx.fail("ERRRRR")

                return (found_version.group('version'), found_version('sem_version'))
