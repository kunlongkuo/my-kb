"""tools/agents/sync.py。"""
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/agents"))
import sync  # noqa: E402


def skill(repo, name, front=None):
    d = repo / "skills" / name
    d.mkdir(parents=True)
    front = f"---\nname: {name}\ndescription: Use when testing {name}.\n---\n" if front is None else front
    (d / "SKILL.md").write_text(front + "\nbody\n", encoding="utf-8")
    return d


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# x\n", encoding="utf-8")
    skill(tmp_path, "alpha")
    skill(tmp_path, "beta")
    return tmp_path


def test_sync_links_every_skill_into_both_places(repo):
    assert sync.sync(repo) == [] and sync.check(repo) == []
    for place in sync.PLACES:
        for name in ("alpha", "beta"):
            link = repo / place / name
            assert link.is_symlink() and os.readlink(link) == f"../../skills/{name}"
            assert (link / "SKILL.md").read_text(encoding="utf-8").startswith(f"---\nname: {name}\n")


def test_sync_twice_changes_nothing(repo):
    sync.sync(repo)
    before = sorted(str(p.relative_to(repo)) for p in repo.rglob("*"))
    assert sync.sync(repo) == [] and before == sorted(str(p.relative_to(repo)) for p in repo.rglob("*"))


def test_check_names_a_missing_link(repo):
    sync.sync(repo)
    (repo / ".agents/skills/beta").unlink()
    assert [e for e in sync.check(repo) if ".agents/skills/beta" in e]


def test_check_names_a_link_that_points_elsewhere(repo):
    sync.sync(repo)
    link = repo / ".claude/skills/alpha"
    link.unlink()
    link.symlink_to("../../skills/beta")
    assert [e for e in sync.check(repo) if ".claude/skills/alpha" in e]


def test_a_real_folder_in_place_of_a_link_is_reported_and_never_removed(repo):
    real = repo / ".agents/skills/alpha"
    real.mkdir(parents=True)
    (real / "SKILL.md").write_text("mine\n", encoding="utf-8")
    assert [e for e in sync.sync(repo) if ".agents/skills/alpha" in e]
    assert (real / "SKILL.md").read_text(encoding="utf-8") == "mine\n" and not real.is_symlink()
    assert [e for e in sync.check(repo) if ".agents/skills/alpha" in e]


def test_check_names_an_extra_entry(repo):
    sync.sync(repo)
    (repo / ".agents/skills/gamma").mkdir()
    assert [e for e in sync.check(repo) if ".agents/skills/gamma" in e]


@pytest.mark.parametrize("front,word", [
    ("", "front matter"),
    ("---\nname: other\ndescription: x\n---\n", "name"),
    ("---\nname: bad\ndescription:\n---\n", "description"),
    ("---\nname: bad\n---\n", "description"),
    ("---\nname: bad\ndescription: x\n", "front matter"),
])
def test_check_rejects_a_bad_front_matter(repo, front, word):
    skill(repo, "bad", front)
    sync.sync(repo)
    assert [e for e in sync.check(repo) if "skills/bad" in e and word in e]


def test_check_wants_AGENTS_md(repo):
    sync.sync(repo)
    (repo / "AGENTS.md").unlink()
    assert [e for e in sync.check(repo) if "AGENTS.md" in e]


def test_folders_without_SKILL_md_are_not_skills(repo):
    (repo / "skills/notes").mkdir()
    assert sync.sync(repo) == [] and sync.check(repo) == [] and not (repo / ".agents/skills/notes").exists()


def test_quoted_description_counts(repo):
    skill(repo, "quoted", '---\nname: quoted\ndescription: "Use when: quoting"\n---\n')
    assert sync.sync(repo) == [] and sync.check(repo) == []


def test_main_exit_codes(repo, capsys):
    assert sync.main(["--check", "--repo", str(repo)]) == 1 and ".agents/skills/alpha" in capsys.readouterr().out
    assert sync.main(["--repo", str(repo)]) == 0
    assert sync.main(["--check", "--repo", str(repo)]) == 0


def test_this_repo_is_in_sync():
    assert sync.check(REPO) == []
