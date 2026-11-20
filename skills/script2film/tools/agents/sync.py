"""把 skills/ 底下的每個 skill 接到各家 agent 會找的位置。

原檔只有一份：skills/<名稱>/（SKILL.md 連同旁邊的檔）。這支在 .agents/skills/<名稱>（Antigravity）與
.claude/skills/<名稱>（Claude Code）各建一個指到 ../../skills/<名稱> 的符號連結。

  python3 tools/agents/sync.py            建連結（已經對的不動；那個位置有實體檔或資料夾時不刪，報錯）
  python3 tools/agents/sync.py --check    只檢查，有問題逐條印出、exit 1

--check 看的：每個 skill 在兩處都有指對的連結、兩處沒有多餘的項目、每個 SKILL.md 有檔頭（--- 包住，
name 和資料夾同名、description 不是空的）、倉庫根目錄有 AGENTS.md。檔頭只讀 name: 與 description: 兩個
單行鍵（不引入 YAML 套件）。Windows 上 git 預設把符號連結簽出成文字檔，要開 core.symlinks。
"""
import os
import sys
from pathlib import Path

PLACES = (".agents/skills", ".claude/skills")


def skills(repo):
    """skills/ 底下有 SKILL.md 的資料夾名（排序）。"""
    root = Path(repo) / "skills"
    return sorted(d.name for d in root.iterdir() if (d / "SKILL.md").is_file()) if root.is_dir() else []


def front_matter(path):
    """SKILL.md 的檔頭 → {鍵: 值}（只收單行的 鍵: 值）；沒有用 --- 包住的檔頭回 None。"""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    out = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip().strip("\"'").strip()
    return None


def target(name):
    return f"../../skills/{name}"


def sync(repo):
    """建或修正連結；回傳做不了的事（那個位置是實體檔或資料夾）。"""
    repo, errors = Path(repo), []
    for place in PLACES:
        (repo / place).mkdir(parents=True, exist_ok=True)
        for name in skills(repo):
            link = repo / place / name
            if link.is_symlink():
                if os.readlink(link) == target(name):
                    continue
                link.unlink()
            elif link.exists():
                errors.append(f"{place}/{name} is a real file or folder, not a link: move it away yourself, then run this again")
                continue
            link.symlink_to(target(name))
    return errors


def check(repo):
    repo, errors = Path(repo), []
    names = skills(repo)
    if not (repo / "AGENTS.md").is_file():
        errors.append("no AGENTS.md at the repository root")
    for name in names:
        fm = front_matter(repo / "skills" / name / "SKILL.md")
        if fm is None:
            errors.append(f"skills/{name}/SKILL.md has no front matter (the first line must be ---, with a closing --- after it)")
            continue
        if fm.get("name") != name:
            errors.append(f"skills/{name}/SKILL.md has name {fm.get('name')!r}: it must match the folder name")
        if not fm.get("description"):
            errors.append(f"skills/{name}/SKILL.md has an empty description")
    for place in PLACES:
        for name in names:
            link = repo / place / name
            if not link.is_symlink():
                errors.append(f"{place}/{name} " + ("is a real file or folder, not a link" if link.exists() else "does not exist")
                              + ": run python3 tools/agents/sync.py")
            elif os.readlink(link) != target(name):
                errors.append(f"{place}/{name} points to {os.readlink(link)}; it should point to {target(name)}")
        extra = sorted(p.name for p in (repo / place).iterdir() if p.name not in names) if (repo / place).is_dir() else []
        errors += [f"{place}/{name} has no matching skill under skills/" for name in extra]
    return errors


USAGE = """Link every skill under skills/ into the places each agent looks.

There is one original: skills/<name>/ (SKILL.md and the files next to it). This makes .agents/skills/<name> (Antigravity)
and .claude/skills/<name> (Claude Code), each a symbolic link to ../../skills/<name>.

  python3 tools/agents/sync.py            make the links (correct ones are left alone; a real file or folder there is not deleted, it is reported)
  python3 tools/agents/sync.py --check    check only: print each problem, exit 1

--check looks at: every skill has a correct link in both places, neither place has extra entries, every SKILL.md has
front matter (between --- lines, name equal to the folder name, description not empty), and AGENTS.md is at the
repository root. The front matter is read for the single-line name: and description: keys only (no YAML package).
On Windows, git checks symbolic links out as text files unless core.symlinks is on."""


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    repo = Path(__file__).resolve().parents[2]
    if "--repo" in args:
        i = args.index("--repo")
        if i + 1 >= len(args):
            print(USAGE)
            return 64
        repo = Path(args[i + 1])
        del args[i:i + 2]
    if args not in ([], ["--check"]):
        print(USAGE)
        return 64
    errors = check(repo) if args else sync(repo) + check(repo)
    for e in errors:
        print(f"✗ {e}")
    if not errors:
        print(f"✓ {len(skills(repo))} skills, linked in all {len(PLACES)} places")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
