from src.cli import Environment
from src.utils.version import VersionUtils

from tests.test_utils.configs import configs

import os
import pytest
import shutil

ctx = Environment()


def test_validate_version():
    cs_config = configs["csharp"]
    test_file = "/".join((os.path.dirname(__file__), "test_files", cs_config.project_file))
    utils = VersionUtils(ctx, "csharp", test_file)
    assert utils.version == f"{cs_config.tag}-pre3"
    assert utils.sem_version == cs_config.tag

    utils.validate_version(utils.version)
    with pytest.raises(Exception):
        utils.validate_version(f"{utils.version}.33")


def test_increment_version():
    cs_config = configs["csharp"]
    test_file = "/".join((os.path.dirname(__file__), "test_files", cs_config.project_file))
    utils = VersionUtils(ctx, "csharp", test_file)
    assert utils.version == f"{cs_config.tag}-pre3"
    assert utils.sem_version == cs_config.tag

    # patch +1 the third number
    utils.increment_version("patch")
    assert utils.new_version == "0.26.1"

    # minor +1 the second number and resets the third
    utils.increment_version("minor")
    assert utils.new_version == "0.27.0"

    # minor +1 the first number and resets the rest
    utils.increment_version("major")
    assert utils.new_version == "1.0.0"


def test_update_csproj_snapshot_version():
    cs_config = configs["csharp"]
    test_file = "/".join((os.path.dirname(__file__), "test_files", cs_config.project_file))
    shutil.copy(test_file, cs_config.project_file)
    utils = VersionUtils(ctx, "csharp", cs_config.project_file)
    # Update the pre$ version and write the file
    utils.update_snapshot_version()
    # now fetch it and check the version was updated
    version, sem_version = utils.lang_utils.parseProjectVersion(cs_config.project_file)
    assert version == f"{cs_config.tag}-pre4"
    assert sem_version == cs_config.tag


def test_update_js_snapshot_version():
    js_config = configs["js"]
    test_file = "/".join((os.path.dirname(__file__), "test_files", js_config.project_file))
    shutil.copy(test_file, js_config.project_file)
    utils = VersionUtils(ctx, "js", js_config.project_file)
    # Update the next$ version and write the file
    utils.update_snapshot_version()
    # now fetch it and check the version was updated
    version, sem_version = utils.lang_utils.parseProjectVersion(js_config.project_file)
    assert version == f"{js_config.tag}-next2"
    assert sem_version == js_config.tag


def test_update_jvm_snapshot_version():
    jvm_config = configs["jvm"]
    test_file = "/".join((os.path.dirname(__file__), "test_files", jvm_config.project_file))
    shutil.copy(test_file, jvm_config.project_file)
    utils = VersionUtils(ctx, "jvm", jvm_config.project_file)
    # Update the SNAPSHOT$ version and write the file
    utils.update_snapshot_version()
    # now fetch it and check the version was updated
    version, sem_version = utils.lang_utils.parseProjectVersion(jvm_config.project_file)
    assert version == f"{jvm_config.tag}-SNAPSHOT6"
    assert sem_version == jvm_config.tag


def test_update_python_snapshot_version():
    python_config = configs["python"]
    test_file = "/".join((os.path.dirname(__file__), "test_files", python_config.project_file))
    shutil.copy(test_file, python_config.project_file)
    utils = VersionUtils(ctx, "python", python_config.project_file)
    # Update the b$ version and write the file
    utils.update_snapshot_version()
    # now fetch it and check the version was updated
    version, sem_version = utils.lang_utils.parseProjectVersion(python_config.project_file)
    assert version == f"{python_config.tag}b2"
    assert sem_version == python_config.tag
