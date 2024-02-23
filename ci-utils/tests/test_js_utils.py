from src.cli import Environment 
import os
import shutil
from src.utils.lang.jsutils import JsUtils
from tests.test_utils.configs import configs

ctx = Environment()

test_file = "/".join((os.path.dirname(__file__), "test_files/test_package.json"))
config = configs["js"]

def test_js_parse_version():
    version, sem_version = JsUtils(ctx).parseProjectVersion(test_file)
    assert version == config.current_version
    assert sem_version == config.current_version.split("-")[0]
    
def test_js_update_snapshot_version():
    shutil.copy(test_file, "/tmp/")
    JsUtils(ctx).updateSnapshotVersion(config.current_version, "/tmp/test_package.json") 

    # # now fetch it and check the version was updated
    version, sem_version = JsUtils(ctx).parseProjectVersion("/tmp/test_package.json")
    assert version == config.next_snapshot
    assert sem_version == config.current_version.split("-")[0]
