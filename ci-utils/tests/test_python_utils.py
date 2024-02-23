from src.cli import Environment 
import os
import shutil
from src.utils.lang.pyutils import PyUtils

from tests.test_utils.configs import configs

ctx = Environment()

config = configs["python"]
test_file = "/".join((os.path.dirname(__file__), "test_files", config.project_file))

def test_py_parse_version():
    version, sem_version = PyUtils(ctx).parseProjectVersion(test_file)
    assert version == config.current_version
    assert sem_version == config.current_version.split("b")[0]

def test_py_update_snapshot_version():
    tmp_path = "/tmp/test_setup.py"
    shutil.copy(test_file, tmp_path)
    PyUtils(ctx).updateSnapshotVersion(config.current_version, tmp_path) 
    # # now fetch it and check the version was updated
    version, sem_version = PyUtils(ctx).parseProjectVersion(tmp_path)
    assert version == config.next_snapshot
    assert sem_version == config.current_version.split("b")[0]
