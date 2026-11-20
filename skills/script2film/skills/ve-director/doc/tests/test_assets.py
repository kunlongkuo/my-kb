"""Two asset layers (s2f-1a D4): the user layer $S2F_ASSETS_LOCAL is looked in before the bundled layer $S2F_ASSETS; no file in
either stops with how to get it; the sfx manifests of both layers merge (user layer wins on an id) and every sound is
found in its own layer's folder."""
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import doc_common  # noqa: E402
import doc_sfx  # noqa: E402


@pytest.fixture
def layers(monkeypatch, tmp_path):
    bundled, local = tmp_path / "bundled", tmp_path / "local"
    for d in (bundled, local):
        (d / "fonts").mkdir(parents=True)
        (d / "sfx").mkdir(parents=True)
    monkeypatch.setenv("S2F_ASSETS", str(bundled))
    monkeypatch.setenv("S2F_ASSETS_LOCAL", str(local))
    return bundled, local


def manifest(d, entries):
    (d / "sfx/manifest.json").write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    for m in entries:
        (d / "sfx" / m["file"]).parent.mkdir(parents=True, exist_ok=True)
        (d / "sfx" / m["file"]).write_bytes(b"x")


def test_bundled_only(layers):
    bundled, _ = layers
    (bundled / "fonts/A.ttf").write_bytes(b"x")
    assert doc_common.asset("fonts", "A.ttf") == bundled / "fonts/A.ttf"


def test_user_layer_first(layers):
    bundled, local = layers
    for d in (bundled, local):
        (d / "fonts/A.ttf").write_bytes(b"x")
    assert doc_common.assets("fonts") == [local / "fonts", bundled / "fonts"]
    assert doc_common.asset("fonts", "A.ttf") == local / "fonts/A.ttf"


def test_user_layer_unset_or_missing(layers, monkeypatch, tmp_path):
    bundled, _ = layers
    monkeypatch.delenv("S2F_ASSETS_LOCAL")
    assert doc_common.assets("fonts") == [bundled / "fonts"]
    monkeypatch.setenv("S2F_ASSETS_LOCAL", str(tmp_path / "nowhere"))
    assert doc_common.assets("fonts") == [bundled / "fonts"]


def test_missing_everywhere_says_how_to_get_it(layers):
    with pytest.raises(SystemExit) as e:
        doc_common.asset("fonts", "Nope.ttf")
    assert "assets/README.md" in str(e.value)


def test_manifests_merge_user_layer_wins(layers):
    bundled, local = layers
    manifest(bundled, [{"id": "same", "file": "b.wav", "license": "CC0"}])
    manifest(local, [{"id": "same", "file": "ve-gen/l.mp3", "license": "VideoExpress 方案授權"}])
    lib, man = doc_sfx.library()
    assert lib == bundled / "sfx"
    assert man["same"]["file"] == "ve-gen/l.mp3" and man["same"]["_dir"] == local / "sfx"


def test_resolve_finds_each_sound_in_its_own_layer(layers):
    bundled, local = layers
    manifest(bundled, [{"id": "kenney-pop", "file": "kenney-pop.wav", "license": "CC0"}])
    manifest(local, [{"id": "ve-pop", "file": "ve-gen/ve-pop.mp3", "license": "VideoExpress 方案授權"}])
    lib, man = doc_sfx.library()
    out = doc_sfx.resolve({"a": {"files": ["kenney-pop"]}, "b": {"files": ["ve-pop"]}}, lib, man)
    assert out["a"][0] == bundled / "sfx/kenney-pop.wav"
    assert out["b"][0] == local / "sfx/ve-gen/ve-pop.mp3"
    # the user layer's sound comes first when the kind lists it first; the bundled one is the fallback behind it
    assert doc_sfx.resolve({"pop": {"files": ["ve-pop", "kenney-pop"]}}, lib, man)["pop"][1]["id"] == "ve-pop"
    (local / "sfx/ve-gen/ve-pop.mp3").unlink()
    assert doc_sfx.resolve({"pop": {"files": ["ve-pop", "kenney-pop"]}}, lib, man)["pop"][1]["id"] == "kenney-pop"


def test_no_manifest_anywhere_stops(layers):
    with pytest.raises(SystemExit) as e:
        doc_sfx.library()
    assert "git checkout -- assets/sfx" in str(e.value)


def test_shipped_sounds_cover_every_kind(monkeypatch):
    """The sounds in the repository's assets/sfx (in git since 2026-11-17): with no user layer, every kind in sfx_map.json
    finds a file, and every entry has an accepted licence and its file on disk."""
    monkeypatch.delenv("S2F_ASSETS", raising=False)
    monkeypatch.delenv("S2F_ASSETS_LOCAL", raising=False)
    lib, man = doc_sfx.library()
    assert lib == doc_common.REPO / "assets/sfx"
    for m in man.values():
        assert (lib / m["file"]).is_file(), m["file"]
        assert any(x in m["license"] for x in doc_sfx.LICENSED), m["id"]
    kinds = doc_sfx.sfx_map({})
    out = doc_sfx.resolve(kinds, lib, man)
    assert sorted(out) == sorted(kinds)
