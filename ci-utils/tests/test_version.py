from src.cli import Environment
from src.utils.version import VersionUtils

import os
import pytest
import shutil

ctx = Environment()


def test_validate_version():
    test_file = "/".join((os.path.dirname(__file__), "test_files/test.csproj"))
    utils = VersionUtils(ctx, "csharp", test_file)
    assert utils.version == "0.26.0-pre3"
    assert utils.sem_version == "0.26.0"

    utils.validate_version(utils.version)


def test_validate_bad_version():
    test_file = "/".join((os.path.dirname(__file__), "test_files/test.csproj"))
    utils = VersionUtils(ctx, "csharp", test_file)
    assert utils.version == "0.26.0-pre3"
    assert utils.sem_version == "0.26.0"

    with pytest.raises(Exception):
        utils.validate_version(f"{utils.version}.33")


def test_increment_version():
    test_file = "/".join((os.path.dirname(__file__), "test_files/test.csproj"))
    utils = VersionUtils(ctx, "csharp", test_file)
    assert utils.version == "0.26.0-pre3"
    assert utils.sem_version == "0.26.0"

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
    test_file = "/".join((os.path.dirname(__file__), "test_files/test.csproj"))
    shutil.copy(test_file, "/tmp/")
    utils = VersionUtils(ctx, "csharp", "/tmp/test.csproj")
    # Update the pre$ version and write the file
    utils.update_snapshot_version()
    # now fetch it and check the version was updated
    version, sem_version = utils.lang_utils.parseProjectVersion("/tmp/test.csproj")
    assert version == "0.26.0-pre4"
    assert sem_version == "0.26.0"


def test_update_js_snapshot_version():
    test_file = "/".join((os.path.dirname(__file__), "test_files/test_package.json"))
    shutil.copy(test_file, "/tmp/")
    utils = VersionUtils(ctx, "js", "/tmp/test_package.json")
    # Update the pre$ version and write the file
    utils.update_snapshot_version()
    # now fetch it and check the version was updated
    version, sem_version = utils.lang_utils.parseProjectVersion("/tmp/test_package.json")
    assert version == "5.1.0-next2"
    assert sem_version == "5.1.0"


def test_update_jvm_snapshot_version():
    test_file = "/".join((os.path.dirname(__file__), "test_files/pom.xml"))
    shutil.copy(test_file, "/tmp/")
    utils = VersionUtils(ctx, "jvm", "/tmp/pom.xml")
    # Update the pre$ version and write the file
    utils.update_snapshot_version()
    # now fetch it and check the version was updated
    version, sem_version = utils.lang_utils.parseProjectVersion("/tmp/pom.xml")
    assert version == "0.17.0-SNAPSHOT6"
    assert sem_version == "0.17.0"


def test_update_python_snapshot_version():
    test_file = "/".join((os.path.dirname(__file__), "test_files/test_setup.pp"))
    shutil.copy(test_file, "/tmp/")
    utils = VersionUtils(ctx, "python", "/tmp/test_setup.py")
    # Update the pre$ version and write the file
    utils.update_snapshot_version()
    # now fetch it and check the version was updated
    version, sem_version = utils.lang_utils.parseProjectVersion("/tmp/test_setup.py")
    assert version == "0.38.0b3"
    assert sem_version == "0.38.0"
