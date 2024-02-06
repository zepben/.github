import os
import re
import datetime

from typing import Union

from src.utils.lang.jsutils import JsUtils
from src.utils.lang.jvmutils import JvmUtils
from src.utils.lang.pyutils import PyUtils
from src.utils.lang.csutils import CsUtils


class VersionUtils:
    lang: str
    project_file: str
    version: str
    new_version: str
    sem_version: str

    lang_utils: Union[JsUtils, JvmUtils, PyUtils, CsUtils]

    def __init__(self, ctx, lang: str, project_file: str):
        self.ctx = ctx
        self.lang = lang
        self.project_file = project_file
        self.version = ""
        self.sem_version = ""

        match lang:
            case "js":
                self.lang_utils = JsUtils(ctx)
            case "jvm":
                self.lang_utils = JvmUtils(ctx)
            case "python":
                self.lang_utils = PyUtils(ctx)
            case "csharp":
                self.lang_utils = CsUtils(ctx)
            case _:
                self.ctx.fail(f"Unsupported language provided: {lang}")

        self.get_versions()

    def validate_version(self, version: str):
        if not re.match(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            self.ctx.fail(
                f"Could not proceed due to the tag {version} not having #.#.# format."
            )

        version_array = version.split(".")
        print(version_array)
        if len(version_array) > 3:
            self.ctx.fail(
                f"Version {version} had more than 3 parts and is not a valid version. Did you enter the correct minor version?"
            )

    def increment_version(self, version_type: str):
        self.ctx.info(f"Updating {version_type} version...")

        version_array = [int(i) for i in self.sem_version.split(".")]
        match version_type:
            case "patch":
                version_array[2] += 1
            case "minor":
                version_array[1] += 1
                version_array[2] = 0
            case "major":
                version_array[0] += 1
                version_array[1] = 0
                version_array[2] = 0
            case _:
                self.ctx.fail(f"{version_type} is invalid.")

        self.new_version = ".".join((str(i) for i in version_array))
        self.ctx.info(f"New version: {self.new_version}")

    def update_version(self, vtype):
        self.increment_version(vtype)
        self._update_new_version(self.new_version)
        self.lang_utils.writeNewVersion(self.project_file,
                                        old=self.version,
                                        new=self.new_version)

    def update_snapshot_version(self):
        self.lang_utils.updateSnapshotVersion(self.version, self.project_file)

    def get_versions(self):
        # Check that file exists
        if not os.path.exists(self.project_file):
            self.ctx.fail(
                f"The provided file {self.project_file} doesn't exist!")

        if self.version or self.sem_version:
            return (self.version, self.sem_version)

        (self.version, self.sem_version) = self.lang_utils.parseProjectVersion(
            self.project_file)

        if not self.version:
            # If version not found
            self.ctx.fail(
                f"Error parsing {self.project_file}. Check that {self.lang} is matching and the format of the file is correct."
            )

        return (self.version, self.sem_version)

    def update_changelog(self, grow_changelog: bool, changelog_file: str):
        release_notes_template = "### Breaking Changes\n* None.\n\n### New Features\n* None.\n\n### Enhancements\n* None.\n\n### Fixes\n* None.\n\n### Notes\n* None.\n"
        # Check if the version pattern matches ## [num.num.num - ]
        with open(changelog_file, "r") as f:
            grow_pattern_ok: bool = False
            text = f.read().split("\n")
            for line in text:
                if re.match(r"## \[[0-9]+\.[0-9]+\.[0-9]\] -", line):
                    grow_pattern_ok = True
                    break

        if grow_changelog and grow_pattern_ok:
            self.ctx.info("Updating the release date")

            new_changelog: list[str] = []
            with open(changelog_file, "r") as f:
                text = f.read().split("\n")
                for line in text:
                    if re.match("^# ", line):
                        ## Make a new line with a template
                        line = f"{line}\n## [{self.new_version}-SNAPSHOT*] - UNRELEASED\n{release_notes_template}"
                    else:
                        # Replace the *existing* UNRELEASED with date
                        unreleased_line = re.search("UNRELEASED", line)
                        if unreleased_line:
                            line = line.replace(
                                "UNRELEASED",
                                datetime.datetime.now().strftime("%Y-%m-%d"))
                    new_changelog.append(line)

            self.ctx.info("Inserting template into changelog...")
            if len(new_changelog) > 0:
                with open(changelog_file, "w") as f:
                    f.write("\n".join(new_changelog))
        else:
            self.ctx.info("Resetting changelog to template...")
            with open(changelog_file, "w") as f:
                f.write(
                    f"## [{self.new_version}-SNAPSHOT*] - UNRELEASED\n{release_notes_template}"
                )

    def _update_new_version(self, base: str):
        if not self.new_version:
            self.ctx.fail(
                "New version was not generated, check you've ran increment_version prior to updating it"
            )

        match self.lang:
            case "js":
                self.new_version = f"{base}-next1"
            case "jvm":
                self.new_version = f"{base}-SNAPSHOT1"
            case "python":
                self.new_version = f"{base}b"
            case "csharp":
                if self.project_file.endswith(
                        ".csproj") or self.project_file.endswith(".nuspec"):
                    self.new_version = f"${self.new_version}-pre1"
