from src.cli import Environment 
import os
from src.utils.lang.csutils import CsUtils

ctx = Environment()


def test_cs_parse_version_cproj():
    test_file = "/".join((os.path.dirname(__file__), "test_files/test.csproj"))
    version, sem_version = CsUtils(ctx).parseProjectVersion(test_file)
    assert version == "0.26.0-pre3"
    assert sem_version == "0.26.0"


def test_cs_parse_version_nuspec():
    test_file = "/".join((os.path.dirname(__file__), "test_files/test.nuspec"))
    version, sem_version = CsUtils(ctx).parseProjectVersion(test_file)
    assert version == "0.26.0-pre3"
    assert sem_version == "0.26.0"


def test_cs_parse_version_assemblyinfo():
    test_file = "/".join((os.path.dirname(__file__), "test_files/AssemblyInfo.cs"))
    version, sem_version = CsUtils(ctx).parseProjectVersion(test_file)
    assert version == "2.5.39.4"
    assert sem_version == "2.5.39.4"

# def test_cs_update_snapshot_version_csproj():
#     test_file = "/".join((os.path.dirname(__file__), "test_files/test.csproj"))
#     shutil.copy(test_file, "/tmp/")
#     CsUtils(ctx).updateSnapshotVersion("2.5.39.4-pre28", "/tmp/test.csproj") 
#
#     # # now fetch it and check the version was updated
#     version, sem_version = CsUtils(ctx).parseProjectVersion("/tmp/test.csproj")
#     assert version == "2.5.39.4-pre28"
#     assert sem_version == "2.5.39.4"
#     # assert 1==0
#
# def test_cs_update_snapshot_version_nuspec():
#     test_file = "/".join((os.path.dirname(__file__), "test_files/test.nuspec"))
#     shutil.copy(test_file, "/tmp/")
#     CsUtils(ctx).updateSnapshotVersion("2.5.39.4-pre28", "/tmp/test.nuspec") 
#     # # now fetch it and check the version was updated
#     version, sem_version = CsUtils(ctx).parseProjectVersion("/tmp/test.nuspec")
#     assert version == "2.5.39.4-pre28"
#     assert sem_version == "2.5.39.4"
#     # assert 1==0
#
# def test_cs_update_snapshot_version_assemblyinfo():
#     test_file = "/".join((os.path.dirname(__file__), "test_files/AssemblyInfo.cs"))
#     shutil.copy(test_file, "/tmp/")
#     CsUtils(ctx).updateSnapshotVersion("0.222.88-pre5", "/tmp/AssemblyInfo.cs") 
#     # # now fetch it and check the version was updated
#     # version, sem_version = CsUtils(ctx).parseProjectVersion(test_file)
#     # assert version == "2.5.39.4"
#     # assert sem_version == "2.5.39.4"
#     assert 1==0
