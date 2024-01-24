from src.cli import Environment 
import os
import shutil
from src.utils.lang.jsutils import JsUtils

ctx = Environment()

test_file = "/".join((os.path.dirname(__file__), "test_files/test_package.json"))

def test_js_parse_version():
    version, sem_version = JsUtils(ctx).parseProjectVersion(test_file)
    assert version == "5.1.0-next1"
    assert sem_version == "5.1.0"

def test_js_update_snapshot_version():
    shutil.copy(test_file, "/tmp/")
    JsUtils(ctx).updateSnapshotVersion("5.1.0-next1", "/tmp/test_package.json") 

    # # now fetch it and check the version was updated
    version, sem_version = JsUtils(ctx).parseProjectVersion("/tmp/test_package.json")
    assert version == "5.1.0-next2"
    assert sem_version == "5.1.0"
