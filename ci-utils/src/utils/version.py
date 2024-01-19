import os
import re
import json
import xml.etree.ElementTree as ET


class VersionUtils():

    ctx: str
    version: str
    sem_version: str

    def __init__(self, ctx):
        self.ctx = ctx

    def validate_version(self, version: str):
        if not re.match(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            self.ctx.fail(
                f"Could not proceed due to the tag {version} not having #.#.# format.")

        version_array = version.split('.')
        if len(version_array) > 3:
            self.ctx.fail(f"Version {version} had more than 3 parts and is not a valid version. Did you enter the correct minor version?")

    def update_snapshot_version(self, lang: str, project_file: str):

        (version, _) = self.get_versions(lang, project_file)

        match lang:
            case "js":
                v = re.search(r"(?P<base>.*)-next(?P<beta>\d+)", version)
                if not v:
                    self.ctx.fail(f"Couldn't parse the version {version} in {project_file}")

                base = v.group("base")
                beta = (int(v.group("beta")) + 1)
                self.write_new_js_version(project_file, version, f"{base}-next{beta}")

            case "jvm":
                v = re.search(r"(?P<base>.*)-SNAPSHOT(?P<beta>\d+)", version)
                if not v:
                    self.ctx.fail(f"Couldn't parse the version {version} in {project_file}")

                base = v.group("base")
                beta = (int(v.group("beta")) + 1)
                self.write_new_jvm_version(project_file, version, f"${base}-SNAPSHOT{beta}")

            case "python":
                v = re.search(r"(?P<base>.*)b(?P<beta>\d+)", version)
                if not v:
                    self.ctx.fail(f"Couldn't parse the version {version} in {project_file}")

                base = v.group("base")
                beta = (int(v.group("beta")) + 1)
                self.write_new_py_version(project_file, version, f"${base}b{beta}")

            case "csharp":
                if not project_file.endswith(".csproj"):
                    self.ctx.fail(f"Project file must be a csproj file! Cannot update the snapshot version")

                v = re.search(r"(?P<base>.*)-pre(?P<beta>\d+)", version)
                if not v:
                    self.ctx.fail(f"Couldn't parse the version {version} in {project_file}")

                base = v.group("base")
                beta = (int(v.group("beta")) + 1)
                self.write_new_cs_version(lang, project_file, version, f"${base}-pre{beta}")

    def get_versions(self, lang: str, project_file: str) -> (str, str):

        # Check that file exists
        if not os.path.exists(project_file):
            self.ctx.fail(f"The provided file {project_file} doesn't exist!")

        version: str = None
        sem_version: str = None
        match lang:
            case "js":
                # we expect the file to be json
                version = self.parseVersionFromJS(project_file)

            case "jvm":
                # POM
                if project_file.endswith(".xml"):
                    (version, sem_version) = self.parseVersionFromPom(project_file)
                else:
                    self.ctx.fail("Project file for java projects should be in POM XML format")

            case "python":
                (version, sem_version) = self.parseVersionFromPy(project_file)

            case "csharp":
                (version, sem_version) = self.parseVersionForCSharp(project_file)

        if not version:
            # If version not found
            self.ctx.fail(f"Error parsing {project_file}. Check that {lang} is matching and the format of the file is correct.")

        return (version, sem_version)

    def parseVersionFromPom(self, project_file: str) -> (str, str):
        project: str = None
        version: str = None
        sem_version: str = None
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
                version = v[0].text
                sem_version = version.split('-')[0]
            else:
                self.ctx.fail(f"Error parsing version in {project_file}, either none found or too many")
        else:
            self.ctx.fail(f"Couldn't find project in {project_file}. Project is XML namespace, and for POM it's expected to be something like 'http://maven.apache.org/POM/4.0.0'")

        if not version:
            self.ctx.fail("ERRRRR")

        return (version, sem_version)

    def parseVersionFromJS(self, project_file: str) -> str:
        with open(project_file) as f:
            project = json.load(f)
            project_version = project.get("version", None)
            if not project_version:
                self.ctx.fail("ERRRRR")

            return project_version.split("-")[0]

    def parseVersionFromPy(self, project_file: str) -> (str, str):
        with open(project_file, "r") as f:
            text = f.read().split('\n')
            for line in text:
                found_version = re.search(r".*version\s*=\s*\"(?P<sem_version>(?P<version>[0-9]+\.[0-9]+\.[0-9]+)b[0-9]+)\"", line)
                if not found_version:
                    self.ctx.fail("ERRRRR")

                return (found_version.group('version'), found_version('sem_version'))

    def parseVersionForCSharp(self, project_file: str) -> (str, str):
        version: str = None
        sem_version: str = None

        if project_file.endswith(".csproj"):
            try:
                tree = ET.parse(project_file)
                version = tree.root.find("Project").find("PropertyGroup").find("Version").text
                if version:
                    sem_version = version.split("-")[0]
            except Exception as err:
                self.ctx.fail(f"Couldn't find the project version in the /Project/PropertyGroup/Version field in the {project_file}: {err}")

        elif project_file.endswith(".nuspec"):
            try:
                tree = ET.parse(project_file)
                version = tree.root.find("package").find("metadata").find("version").text
                if version:
                    sem_version = version.split("-")[0]
            except Exception as err:
                self.ctx.fail(f"Couldn't find the project version in the /project/metadata/version field in the {project_file}: {err}")

        elif project_file.endswith("AssemblyInfo.cs"):
            with open(project_file, "r") as f:
                lines = f.read().split('\n')
                for line in lines:
                    found_ver = re.search(r".*AssemblyVersion\(\"(?P<version>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\"\)", line)
                    if found_ver:
                        version = found_ver.group('version')
                        sem_version = version
                        break

        return (version, sem_version)

    def write_new_jvm_version(self, project_file: str, old: str, new: str):
        if old != new:
            self.ctx.info(f"Writing new version {new}")
            self.ctx.info("JVM writing not implemented")

    def write_new_ps_version(self, project_file: str, old: str, new: str):
        if old != new:
            text: str
            self.ctx.info(f"Writing new version {new}")
            with open(project_file, "r") as p:
                text = p.read()
                text.replace(fr"version\s*=\s*{old}", fr"version\s*=\s*{new}")

            # now all lines are updated, so write it up to the file
            with open(project_file, "w") as p:
                p.write(text)

    def write_new_js_version(self, project_file: str, old: str, new: str):
        if old != new:
            self.ctx.info(f"Writing new version {new}")
            self.ctx.info("JS writing not implemented")
            # run jq --arg VERSION $new_ver '.version = $VERSION' $file
            # run cp -f $output_file $file

    def write_new_cs_version(self, project_file: str, old: str, new: str):

        if old != new:
            self.ctx.info(f"Writing new version {new}")
            self.ctx.info("CSHARP writing not implemented")

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
