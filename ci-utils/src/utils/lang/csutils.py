import re
import xml.etree.ElementTree as ET


class CsUtils():

    ctx: str

    def __init__(self, ctx):
        self.ctx = ctx

    def updateSnapshotVersion(self, version: str, project_file: str):
        if not project_file.endswith(".csproj"):
            self.ctx.fail(
                f"Project file must be a csproj file! Cannot update the snapshot version")

        v = re.search(r"(?P<base>.*)-pre(?P<beta>\d+)", version)
        if not v:
            self.ctx.fail(
                f"Couldn't parse the version {version} in {project_file}")

        base = v.group("base")
        beta = (int(v.group("beta")) + 1)
        self.writeNewVersion(
            self.lang, project_file, version, f"${base}-pre{beta}")

    def writeNewVersion(self, project_file: str, old: str, new: str):

        if old != new:
            self.ctx.info(f"Writing new version {new}")
            self.ctx.fail("CSHARP writing not implemented")

            # if project_file.endswith("csproj"):
            #     # run xmlstarlet ed -P -L -u "/Project/PropertyGroup/Version" -v $new_ver $file
            #     # pre=${new_ver#*"-pre"}
            #     # sem_version=${new_ver%-pre*}
            #     # if [[ $new_ver == *"-pre"* ]]; then
            #     #     run xmlstarlet ed -P -L -u "/Project/PropertyGroup/AssemblyVersion" -v "${sem_version}.${pre}" $file
            #     #     run xmlstarlet ed -P -L -u "/Project/PropertyGroup/FileVersion" -v "${sem_version}.${pre}" $file
            #     # fi
            # elif file.endswith(".nuspec"):
            #     # run xmlstarlet ed -P -L -u "/package/metadata/version" -v $new_ver $file
            # else:
            #     # sed -i "s/$old_ver/$new_ver/g" $file

    def parseProjectVersion(self, project_file: str) -> (str, str):
        version: str = None
        sem_version: str = None

        if project_file.endswith(".csproj"):
            try:
                tree = ET.parse(project_file)
                version = tree.root.find("Project").find(
                    "PropertyGroup").find("Version").text
                if version:
                    sem_version = version.split("-")[0]
            except Exception as err:
                self.ctx.fail(
                    f"Couldn't find the project version in the /Project/PropertyGroup/Version field in the {project_file}: {err}")

        elif project_file.endswith(".nuspec"):
            try:
                tree = ET.parse(project_file)
                version = tree.root.find("package").find(
                    "metadata").find("version").text
                if version:
                    sem_version = version.split("-")[0]
            except Exception as err:
                self.ctx.fail(
                    f"Couldn't find the project version in the /project/metadata/version field in the {project_file}: {err}")

        elif project_file.endswith("AssemblyInfo.cs"):
            with open(project_file, "r") as f:
                lines = f.readll().split('\n')
                for line in lines:
                    found_ver = re.search(
                        r".*AssemblyVersion\(\"(?P<version>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\"\)", line)
                    if found_ver:
                        version = found_ver.group('version')
                        sem_version = version
                        break

        return (version, sem_version)
