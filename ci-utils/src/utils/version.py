import os
import re
import json
import xml.etree.ElementTree as ET


class VersionUtils():

    def __init__(self, ctx):
        self.ctx = ctx

    def validate_version(self, version: str):
        if not re.match(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            self.ctx.fail(
                f"Could not proceed due to the tag {version} not having #.#.# format.")

        version_array = version.split('.')
        if len(version_array) > 3:
            self.ctx.fail(f"Version {version} had more than 3 parts and is not a valid version. Did you enter the correct minor version?")

    def get_sem_version(self, lang: str, project_file: str) -> str:

        # Check that file exists
        if not os.path.exists(project_file):
            self.ctx.fail(f"The provided file {project_file} doesn't exist!")

        version: str = None
        match lang:
            case "js":
                # we expect the file to be json
                version = self.parseVersionFromJS(project_file)

            case "jvm":
                # POM
                if project_file.endswith(".xml"):
                    version = self.parseVersionFromPom(project_file)
                else:
                    self.ctx.fail("Project file for java projects should be in POM XML format")

            case "python":
                version = self.parseVersionFromPy(project_file)

            case "csharp":
                version = self.parseVersionForCSharp(project_file)

        if not version:
            # If version not found
            self.ctx.fail(f"Error parsing {project_file}. Check that {lang} is matching and the format of the file is correct.")

        return version

    def parseVersionFromPom(self, project_file: str) -> str:
        project: str = None
        version: str = None
        tree = ET.parse(project_file)
        for v in tree.getroot().attrib.values():
            for p in v.split():
                if re.match(".*apache.*POM.*", p):
                    project = "{" + p + "}"

        if project:
            v = tree.getroot().findall(f"{project}version")
            if len(v) == 1:
                # v[0].text is the value of the version field
                # we split by '-' (-SNAPSHOT) and take the first part
                version = v[0].text.split('-')[0]
            else:
                self.ctx.fail(f"Error parsing version in {project_file}, either none found or too many")
        else:
            self.ctx.fail(f"Couldn't find project in {project_file}. Project is XML namespace, and for POM it's expected to be something like 'http://maven.apache.org/POM/4.0.0'")

        if not version:
            self.ctx.fail("ERRRRR")

        return version

    def parseVersionFromJS(self, project_file: str) -> str:
        with open(project_file) as f:
            project = json.load(f)
            project_version = project.get("version", None)
            if not project_version:
                self.ctx.fail("ERRRRR")

            return project_version.split("-")[0]

    def parseVersionFromPy(self, project_file: str) -> str:
        with open(project_file, "r") as f:
            text = f.read().split('\n')
            for line in text:
                found_version = re.search(r".*version\s*=\s*\"(?P<version>[0-9]+\.[0-9]+\.[0-9]+)b[0-9]+\"", line)
                if not found_version:
                    self.ctx.fail("ERRRRR")

                return found_version.group('version')

    def parseVersionForCSharp(self, project_file: str) -> str:
        version: str = None
        if project_file.endswith(".csproj"):
            try:
                tree = ET.parse(project_file)
                project_version = tree.root.find("Project").find("PropertyGroup").find("Version").text
                if project_version:
                    version = project_version.split("-")[0]
            except Exception as err:
                self.ctx.fail(f"Couldn't find the project version in the /Project/PropertyGroup/Version field in the {project_file}: {err}")

        elif project_file.endswith(".nuspec"):
            try:
                tree = ET.parse(project_file)
                project_version = tree.root.find("package").find("metadata").find("version").text
                if project_version:
                    version = project_version.split("-")[0]
            except Exception as err:
                self.ctx.fail(f"Couldn't find the project version in the /project/metadata/version field in the {project_file}: {err}")

        elif project_file.endswith("AssemblyInfo.cs"):
            with open(project_file, "r") as f:
                lines = f.readall().split('\n')
                for line in lines:
                    found_ver = re.search(r".*AssemblyVersion\(\"(?P<version>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\"\)", line)
                    if found_ver:
                        version = found_ver.group('version')
                        break

        return version
