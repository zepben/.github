import json
import re


class JsUtils():

    ctx: str

    def __init__(self, ctx):
        self.ctx = ctx

    def updateSnapshotVersion(self, version: str, project_file: str):
        v = re.search(r"(?P<base>.*)-next(?P<beta>\d+)", version)
        if not v:
            self.ctx.fail(
                f"Couldn't parse the version {version} in {project_file}")

        base = v.group("base")
        beta = (int(v.group("beta")) + 1)
        self.writeNewVersion(
            self.ctx, project_file, version, f"{base}-next{beta}")

    def writeNewVersion(self, project_file: str, old: str, new: str):
        if old != new:
            self.ctx.info(f"Writing new version {new}")
            self.ctx.fail("JS writing not implemented")
            if not re.match(r".*[\.csproj|\.nuspec|AssemblyInfo\.cs]$", project_file):
                self.ctx.fail(
                    f"Project file must be be a csproj, nuspec or AssemblyInfo.cs file")
            # run jq --arg VERSION $new_ver '.version = $VERSION' $file
            # run cp -f $output_file $file

    def parseProjectVersion(self, project_file: str) -> (str, str):
        with open(project_file) as f:
            project = json.load(f)
            project_version = project.get("version", None)
            if not project_version:
                self.ctx.fail("Err in JS parsing version")

            return (project_version, project_version.split("-")[0])
