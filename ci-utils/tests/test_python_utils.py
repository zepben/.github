from src.cli import Environment
import os
import shutil
import pytest

from src.utils.lang.pyutils import PyUtils
from tests.test_utils.configs import configs
from jinja2 import Environment as JEnv, FileSystemLoader

ctx = Environment()
environment = JEnv(loader=FileSystemLoader(
    os.path.join(os.path.dirname(__file__), "test_files")))

config = configs["python"]


@pytest.fixture
def test_path():
    template = environment.get_template(config.project_file)
    content = template.render(current_version=config.current_version)
    fpath = os.path.join("/tmp", config.project_file)
    with open(fpath, "w") as f:
        f.write(content)
    yield fpath


def test_py_parse_version(test_path):
    version, sem_version = PyUtils(ctx).parseProjectVersion(test_path)
    assert version == config.current_version
    assert sem_version == config.current_version.split("b")[0]


def test_py_update_snapshot_version(test_path):
    PyUtils(ctx).updateSnapshotVersion(config.current_version, test_path)
    # now fetch it and check the version was updated
    version, sem_version = PyUtils(ctx).parseProjectVersion(test_path)
    assert version == config.next_snapshot
    assert sem_version == config.current_version.split("b")[0]
