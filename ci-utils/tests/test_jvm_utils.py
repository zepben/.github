from src.cli import Environment
import os
import shutil
from src.utils.lang.jvmutils import JvmUtils
from tests.test_utils.configs import configs

ctx = Environment()
config = configs["jvm"]

test_file = "/".join((os.path.dirname(__file__), "test_files/pom.xml"))


def test_jvm_parse_version():
    version, sem_version = JvmUtils(ctx).parseProjectVersion(test_file)
    assert version == config.current_version
    assert sem_version == config.current_version.split("-")[0]


def test_jvm_update_snapshot_version():
    shutil.copy(test_file, "/tmp/")
    JvmUtils(ctx).updateSnapshotVersion(config.current_version, "/tmp/pom.xml")
    # now fetch it and check the version was updated
    version, sem_version = JvmUtils(ctx).parseProjectVersion("/tmp/pom.xml")
    assert version == config.next_snapshot
    assert sem_version == config.current_version.split("-")[0]
