from src.cli import Environment 
import os
import shutil
from src.utils.lang.jvmutils import JvmUtils

ctx = Environment()

test_file = "/".join((os.path.dirname(__file__), "test_files/pom.xml"))

def test_jvm_parse_version():
    version, sem_version = JvmUtils(ctx).parseProjectVersion(test_file)
    assert version == "0.17.0-SNAPSHOT5"
    assert sem_version == "0.17.0"

def test_jvm_update_snapshot_version():
    shutil.copy(test_file, "/tmp/")
    JvmUtils(ctx).updateSnapshotVersion("0.17.0-SNAPSHOT5", "/tmp/pom.xml") 
    # now fetch it and check the version was updated
    version, sem_version = JvmUtils(ctx).parseProjectVersion("/tmp/pom.xml")
    assert version == "0.17.0-SNAPSHOT6"
    assert sem_version == "0.17.0"
