from src.cli import Environment 
import os
import shutil
from src.utils.lang.pyutils import PyUtils

from tests.test_utils.configs import configs

ctx = Environment()

test_file = "/".join((os.path.dirname(__file__), "test_files", configs["python"].project_file))

def test_py_parse_version():
    version, sem_version = PyUtils(ctx).parseProjectVersion(test_file)
    assert version == "0.38.0b1"
    assert sem_version == "0.38.0"

def test_py_update_snapshot_version():
    shutil.copy(test_file, "/tmp/test_setup.py")
    PyUtils(ctx).updateSnapshotVersion("0.38.0b1", "/tmp/test_setup.py") 
    # # now fetch it and check the version was updated
    version, sem_version = PyUtils(ctx).parseProjectVersion("/tmp/test_setup.py")
    assert version == "0.38.0b2"
    assert sem_version == "0.38.0"
