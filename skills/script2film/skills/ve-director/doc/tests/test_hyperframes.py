"""doc_common.hyperframes (s2f-1a D2): the HyperFrames CLI is found in this repo (root package.json, `npm ci`) or at
$S2F_HF_BIN, runs on a Node 22+ `node` from PATH, and a failed render stops doc_cut instead of printing `rendered`."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import doc_common  # noqa: E402

# A stand-in for the CLI: prints what it was started with, then exits with the code in its name.
FAKE = """const out = {argv: process.argv.slice(2), cwd: process.cwd(), run_id: process.env.HYPERFRAMES_RUN_ID,
             gpu: process.env.PRODUCER_BROWSER_GPU_MODE ?? null};
console.log(JSON.stringify(out));
process.exit(%d);
"""


def fake_pkg(root, code=0):
    (root / "bin").mkdir(parents=True)
    (root / "package.json").write_text(json.dumps({"name": "hyperframes", "bin": {"hyperframes": "./bin/hf.mjs"}}))
    (root / "bin/hf.mjs").write_text(FAKE % code)
    return root


@pytest.fixture
def clean_env(monkeypatch):
    for k in ("S2F_HF_BIN", "HYPERFRAMES_RUN_ID", "PRODUCER_BROWSER_GPU_MODE"):
        monkeypatch.delenv(k, raising=False)
    return monkeypatch


def run_fake(tmp_path, command="render", *args):
    log = tmp_path / "run.log"
    with open(log, "w") as f:
        r = doc_common.hyperframes(command, tmp_path / "proj", *args, stdout=f)
    return r, json.loads(log.read_text().strip().splitlines()[-1])


def test_repo_node_modules(clean_env):
    entry, root = doc_common.hf_package()
    assert root == (doc_common.REPO / "node_modules/hyperframes").resolve()
    assert entry == (root / json.loads((root / "package.json").read_text())["bin"]["hyperframes"]).resolve()
    assert entry.exists()


def test_s2f_hf_bin(clean_env, tmp_path):
    pkg = fake_pkg(tmp_path / "elsewhere/hyperframes")
    clean_env.setenv("S2F_HF_BIN", str(pkg))
    assert doc_common.hf_package() == ((pkg / "bin/hf.mjs").resolve(), pkg.resolve())
    clean_env.setenv("S2F_HF_BIN", str(pkg / "bin/hf.mjs"))   # the entry script itself works too
    assert doc_common.hf_package() == ((pkg / "bin/hf.mjs").resolve(), pkg.resolve())


def test_not_found_says_npm_ci(clean_env, tmp_path):
    clean_env.setattr(doc_common, "REPO", tmp_path)
    with pytest.raises(SystemExit) as e:
        doc_common.hf_package()
    assert "npm ci" in str(e.value)


def test_old_node_stops(clean_env, tmp_path):
    fake_pkg(tmp_path / "hyperframes")
    clean_env.setenv("S2F_HF_BIN", str(tmp_path / "hyperframes"))
    (tmp_path / "nodebin").mkdir()
    node = tmp_path / "nodebin/node"
    node.write_text("#!/bin/sh\necho v18.20.0\n")
    node.chmod(0o755)
    clean_env.setenv("PATH", f"{node.parent}{os.pathsep}{os.environ['PATH']}")
    with pytest.raises(SystemExit) as e:
        doc_common.hyperframes("render", tmp_path)
    assert "22" in str(e.value) and "v18" in str(e.value)


def test_invocation(clean_env, tmp_path, monkeypatch):
    pkg = fake_pkg(tmp_path / "hyperframes")
    clean_env.setenv("S2F_HF_BIN", str(pkg))
    monkeypatch.chdir(tmp_path)
    r, got = run_fake(tmp_path, "render", "-o", "rel/out.mp4", "--fps", "30")
    assert r.returncode == 0
    assert Path(got["cwd"]).resolve() == pkg.resolve()
    assert got["argv"] == ["render", str((tmp_path / "proj").resolve()), "-o", str((tmp_path / "rel/out.mp4").resolve()),
                           "--fps", "30"]
    assert Path(got["argv"][3]).is_absolute()
    assert got["gpu"] == "hardware"
    assert got["run_id"].startswith("s2f-")
    # values already set outside are kept
    clean_env.setenv("PRODUCER_BROWSER_GPU_MODE", "software")
    clean_env.setenv("HYPERFRAMES_RUN_ID", "outer-run")
    _, got = run_fake(tmp_path, "render")
    assert got["gpu"] == "software" and got["run_id"] == "outer-run"
    # the GPU setting is for renders only
    clean_env.delenv("PRODUCER_BROWSER_GPU_MODE")
    _, got = run_fake(tmp_path, "snapshot")
    assert got["gpu"] is None


def test_nonzero_is_returned(clean_env, tmp_path):
    clean_env.setenv("S2F_HF_BIN", str(fake_pkg(tmp_path / "hyperframes", code=3)))
    r, _ = run_fake(tmp_path)
    assert r.returncode == 3


def test_doc_cut_render_failure_stops(clean_env, tmp_path):
    pkg = fake_pkg(tmp_path / "hyperframes", code=3)
    (tmp_path / "cut").mkdir()
    env = {**os.environ, "S2F_HF_BIN": str(pkg)}
    code = f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import doc_cut; from pathlib import Path; doc_cut.render(Path({str(tmp_path / 'cut')!r}))"
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert r.returncode != 0
    assert "rendered" not in r.stdout
    assert "render.log" in r.stderr
