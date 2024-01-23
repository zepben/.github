import xml.etree.ElementTree as ET

import re


class JvmUtils():

    ctx: str

    def __init__(self, ctx):
        self.ctx = ctx

    def write_new_version(self, project_file: str, old: str, new: str):
        if old != new:
            self.ctx.info(f"Writing new version {new}")
            self.ctx.fail("JVM writing not implemented")

    def parseVersionFromPom(ctx, project_file: str) -> (str, str):
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
                ctx.fail(f"Error parsing version in {project_file}, either none found or too many")
        else:
            ctx.fail(f"Couldn't find project in {project_file}. Project is XML namespace, and for POM it's expected to be something like 'http://maven.apache.org/POM/4.0.0'")

        if not version:
            ctx.fail("ERRRRR")

        return (version, sem_version)
