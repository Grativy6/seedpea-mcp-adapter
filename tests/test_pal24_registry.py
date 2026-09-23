import re

from seedpea_foundation.contracts import compatibility_profile, pal24_source_profile, source_registry


def test_source_versions_remain_separately_addressable():
    for version, record in (("2.3", "22240134"), ("2.4", "22888036")):
        result = source_registry({"operation": "read", "source_id": "PAL", "version": version})
        assert result["source"]["version"] == version
        assert result["source"]["url"].endswith(record)
    assert compatibility_profile("2.3")["pal_target"] == "2.3"
    assert compatibility_profile()["pal_target"] == "2.4"
    assert compatibility_profile()["ppp_declared_pal"] == "2.2"


def test_packaged_source_manifest_keeps_open_obligations_and_exact_artifact_pins():
    manifest = pal24_source_profile()
    assert manifest["version"] == "2.4"
    assert manifest["doi"] == "10.5281/zenodo.22888036"
    assert manifest["source_obligations"] == {"O63": "OPEN", "O64": "OPEN", "O65": "OPEN"}
    assert len(manifest["artifacts"]) == 5
    assert len({a["filename"] for a in manifest["artifacts"]}) == 5
    for artifact in manifest["artifacts"]:
        assert re.fullmatch("[0-9a-f]{64}", artifact["sha256"])
        assert re.fullmatch("[0-9a-f]{32}", artifact["published_md5"])
