import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("install", Path(__file__).parent.parent / "scripts" / "install.py")
install = importlib.util.module_from_spec(spec)
spec.loader.exec_module(install)


def test_plan_ignores_groups_missing_from_a_partial_zip(tmp_path, monkeypatch):
    # zip B so traz packs/ecc; os outros grupos e as ROOT_SKILLS nao existem
    (tmp_path / "ecc" / "skills" / "seo").mkdir(parents=True)
    (tmp_path / "ecc" / "skills" / "seo" / "SKILL.md").write_text("x")
    monkeypatch.setattr(install, "ROOT", tmp_path)
    assert [name for _, name in install.plan(set())] == ["seo"]


def test_plan_installs_pack_c_video_skills_under_their_names(tmp_path, monkeypatch):
    # zip C: parte do ecc mais as duas skills de video na raiz de packs/
    (tmp_path / "ecc" / "skills" / "video-editing").mkdir(parents=True)
    (tmp_path / "ecc" / "skills" / "video-editing" / "SKILL.md").write_text("x")
    for d in ("video-shotcraft", "video-effects"):
        (tmp_path / d).mkdir()
    monkeypatch.setattr(install, "ROOT", tmp_path)
    assert [name for _, name in install.plan(set())] == ["video-editing", "video-shotcraft", "effects"]
