import json
import re


class JsUtils:

    def __init__(self, ctx):
        self.ctx = ctx

    def updateSnapshotVersion(self, version: str, project_file: str):
        v = re.search(r"(?P<base>.*)-next(?P<beta>\d+)", version)
        if not v:
            self.ctx.fail(
                f"Couldn't parse the version {version} in {project_file}")

        base = v.group("base")
        beta = (int(v.group("beta")) + 1)
        self.writeNewVersion(project_file, version, f"{base}-next{beta}")

    def writeNewVersion(self, project_file: str, old: str, new: str):
        if old != new:
            self.ctx.info(f"Updating old version '{old}' to new version '{new}'")
            project = ""
            with open(project_file) as f:
                project = json.load(f)
                project["version"] = new

            with open(project_file, "w") as f:
                json.dump(project, f, indent=2)

    def parseProjectVersion(self, project_file: str) -> tuple[str, str]:
        with open(project_file) as f:
            project = json.load(f)
            project_version = project.get("version", None)
            if not project_version:
                self.ctx.fail("Err in JS parsing version")

            return project_version, project_version.split("-")[0]
