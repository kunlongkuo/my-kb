"""skill-rag: scan, index, and query multi-file knowledge.

This script is intentionally dependency-light:
- stdlib for local scanning/chunking/scoring and DOCX text extraction
- optional pypdf for PDF text extraction
- optional SQL export for MySQL import

It does not print secrets.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import html
import json
import os
import re
import sqlite3
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - PDF support is optional
    PdfReader = None

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "you", "your", "are",
    "was", "were", "will", "would", "could", "should", "about", "into", "than",
    "then", "when", "what", "which", "where", "how", "why", "can", "may", "might",
    "not", "too", "also", "have", "has", "had", "use", "using", "used", "into",
    "all", "any", "our", "their", "them", "they", "there", "here", "each", "one",
    "two", "three", "if", "else", "than", "a", "an", "of", "to", "in", "on",
    "at", "as", "by", "or", "is", "it", "be", "we", "do", "does", "did",
}

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mpeg", ".mpg", ".wmv", ".flv", ".3gp"}
MEDIA_EXTS = IMAGE_EXTS | VIDEO_EXTS
SUBTITLE_EXTS = {".srt", ".vtt"}
SUPPORTED_EXTS = {
    ".md", ".markdown", ".txt", ".json", ".yaml", ".yml", ".sql", ".docx", ".pdf",
    *MEDIA_EXTS, *SUBTITLE_EXTS,
}
IGNORE_NAMES = {"setup.json", "PLAN.md", "SKILL.md"}
DEFAULT_SOURCE_DIRS = ("sources", "references", "knowledge", "docs")
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MARKDOWN_LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(\s*(<[^>]+>|[^)\s]+)", re.I)
HTML_MEDIA_SRC_RE = re.compile(r"<(?:img|video|source|iframe)\b[^>]*?\bsrc\s*=\s*(['\"])(.*?)\1", re.I | re.S)
BARE_URL_RE = re.compile(r"(?i)(?:https?://|file://)[^\s<>\"'()]+")
MEDIA_LABEL_RE = re.compile(r"image|photo|picture|video|movie|clip|watch|play|圖片|照片|圖檔|影片|視頻|播放|觀看|影像", re.I)
VIDEO_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "vimeo.com", "www.vimeo.com", "player.vimeo.com"}


@dataclasses.dataclass
class Chunk:
    source_path: str
    source_name: str
    source_hash: str
    doc_type: str
    title: str
    chunk_index: int
    chunk_title: str
    content: str
    chunk_content: str
    summary: str
    keywords: list[str]
    tags: list[str]
    rag_model: str
    embedding_model: str
    score: float
    status: str = "active"


def load_setup(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    mysql = data.get("mysql", {})
    openai = data.get("openai", {})
    rag = data.get("rag", {})
    if not mysql.get("user") or not mysql.get("password") or not mysql.get("database"):
        raise ValueError("setup.json missing mysql.user/password/database")
    if not openai.get("api_key"):
        raise ValueError("setup.json missing openai.api_key")
    rag.setdefault("chunk_size", 1200)
    rag.setdefault("chunk_overlap", 150)
    rag.setdefault("top_k", 5)
    rag.setdefault("score_threshold", 0.35)
    rag.setdefault("rebuild_mode", "full")
    return {"mysql": mysql, "openai": openai, "rag": rag}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_docx_text(path: Path) -> str:
    """Extract paragraphs, including those inside tables, in document order."""
    try:
        with zipfile.ZipFile(path) as archive:
            document_xml = ElementTree.fromstring(archive.read("word/document.xml"))
    except (KeyError, ElementTree.ParseError, zipfile.BadZipFile) as exc:
        raise ValueError(f"Unable to read DOCX document content from {path.name}") from exc

    paragraphs: list[str] = []
    for paragraph in document_xml.findall(f".//{{{WORD_NS}}}p"):
        parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{{{WORD_NS}}}t":
                parts.append(node.text or "")
            elif node.tag == f"{{{WORD_NS}}}tab":
                parts.append("\t")
            elif node.tag in {f"{{{WORD_NS}}}br", f"{{{WORD_NS}}}cr"}:
                parts.append("\n")
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def read_pdf_text(path: Path) -> str:
    """Extract selectable text from each PDF page; OCR is intentionally out of scope."""
    if PdfReader is None:
        raise RuntimeError("PDF extraction requires pypdf. Install it with: python -m pip install -r requirements.txt")

    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise ValueError(f"Password-protected PDF is not supported: {path.name}")
        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(f"# Page {page_number}\n{text}")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Unable to extract text from PDF {path.name}: {exc}") from exc

    if not pages:
        raise ValueError(f"No selectable text found in {path.name}; scanned/image-only PDFs need OCR first")
    return "\n\n".join(pages)


def read_media_text(path: Path) -> str:
    """Make media searchable by filename and optional same-stem description/transcript."""
    media_type = "Image" if path.suffix.lower() in IMAGE_EXTS else "Video"
    parts = [f"{media_type} file: {path.stem}"]
    for suffix in (".md", ".txt", ".srt", ".vtt"):
        sidecar = path.with_suffix(suffix)
        if sidecar.is_file():
            description = read_subtitle_text(sidecar) if sidecar.suffix.lower() in SUBTITLE_EXTS else sidecar.read_text(encoding="utf-8", errors="replace").strip()
            if description:
                parts.append(description)
    return "\n\n".join(parts)


def read_subtitle_text(path: Path) -> str:
    lines = []
    for raw_line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.upper() == "WEBVTT" or "-->" in line or line.isdigit():
            continue
        if line.upper().startswith(("NOTE", "STYLE", "REGION")):
            continue
        line = html.unescape(re.sub(r"<[^>]+>", "", line)).strip()
        if line:
            lines.append(line)
    return "\n\n".join(lines)


def read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx_text(path)
    if suffix == ".pdf":
        return read_pdf_text(path)
    if suffix in MEDIA_EXTS:
        return read_media_text(path)
    if suffix in SUBTITLE_EXTS:
        return read_subtitle_text(path)
    return path.read_text(encoding="utf-8", errors="replace")


def sha256_source(path: Path, text: str) -> str:
    if path.suffix.lower() not in MEDIA_EXTS:
        return sha256_text(text)
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)
    digest.update(b"\0")
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()


def is_media_url(url: str) -> bool:
    parsed = urlsplit(url)
    host = parsed.netloc.lower().split(":", 1)[0]
    return Path(unquote(parsed.path)).suffix.lower() in MEDIA_EXTS or host in VIDEO_HOSTS


def extract_media_links(text: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for match in MARKDOWN_LINK_RE.finditer(text):
        raw_url = match.group(3).strip()
        if raw_url.startswith("<") and raw_url.endswith(">"):
            raw_url = raw_url[1:-1]
        label = match.group(2).strip() or Path(urlsplit(raw_url).path).name or "查看媒體"
        if match.group(1) or is_media_url(raw_url) or MEDIA_LABEL_RE.search(label):
            links.append((label, raw_url))
    for match in HTML_MEDIA_SRC_RE.finditer(text):
        url = html.unescape(match.group(2).strip())
        links.append((Path(urlsplit(url).path).name or "查看媒體", url))
    for match in BARE_URL_RE.finditer(text):
        url = match.group(0).rstrip(".,;!?:")
        if is_media_url(url):
            links.append((Path(urlsplit(url).path).name or urlsplit(url).netloc or "查看媒體", url))
    unique: dict[str, tuple[str, str]] = {}
    for label, url in links:
        if url:
            unique.setdefault(url, (label, url))
    return list(unique.values())


def clickable_media_url(url: str, source_path: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme.lower() in {"http", "https", "file"}:
        return url
    if re.match(r"^[A-Za-z]:[\\/]", url):
        return Path(url).resolve().as_uri()
    if not parsed.scheme and Path(unquote(parsed.path)).suffix.lower() in MEDIA_EXTS:
        local_path = (Path(source_path).resolve().parent / unquote(parsed.path)).resolve()
        if local_path.exists():
            return local_path.as_uri()
    return url


def media_links_for_hit(hit: dict) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    source_path = hit.get("source_path", "")
    if source_path:
        parsed_source = urlsplit(source_path)
        if parsed_source.scheme.lower() in {"http", "https", "file"} and is_media_url(source_path):
            links.append((hit.get("source_name", "查看媒體"), source_path))
        else:
            local_source = Path(source_path)
            if local_source.suffix.lower() in MEDIA_EXTS:
                related_paths = [local_source]
            elif local_source.exists():
                related_paths = [
                    candidate for candidate in local_source.parent.glob(f"{local_source.stem}.*")
                    if candidate.suffix.lower() in MEDIA_EXTS
                ]
            else:
                related_paths = []
            for media_path in related_paths:
                links.append((media_path.name, media_path.resolve().as_uri()))
    for label, url in extract_media_links(hit.get("content", "")):
        clickable = clickable_media_url(url, source_path)
        pair = (label, clickable)
        if pair not in links:
            links.append(pair)
    return links


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\r\n?", "\n", text).strip()


def split_paragraphs(text: str) -> list[str]:
    text = normalize_whitespace(text)
    if not text:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]


def split_large_block(block: str, max_chars: int, overlap: int) -> list[str]:
    if len(block) <= max_chars:
        return [block.strip()]
    sentences = re.split(r"(?<=[。！？.!?])\s+|\n", block)
    out: list[str] = []
    buf = ""
    for piece in sentences:
        piece = piece.strip()
        if not piece:
            continue
        if not buf:
            buf = piece
        elif len(buf) + 1 + len(piece) <= max_chars:
            buf = f"{buf} {piece}"
        else:
            out.append(buf.strip())
            tail = buf[-overlap:] if overlap > 0 else ""
            buf = (tail + " " + piece).strip() if tail else piece
    if buf.strip():
        out.append(buf.strip())
    return out


def chunk_text(text: str, max_chars: int, overlap: int) -> list[tuple[str, str]]:
    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return []
    chunks: list[tuple[str, str]] = []
    cur: list[str] = []
    cur_len = 0
    heading = ""
    for para in paragraphs:
        if para.startswith("#"):
            heading = para.lstrip("#").strip()
        blocks = [para]
        if len(para) > max_chars:
            blocks = split_large_block(para, max_chars, overlap)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            if cur and cur_len + 2 + len(block) > max_chars:
                chunk = "\n\n".join(cur).strip()
                chunks.append((heading or f"chunk-{len(chunks)+1}", chunk))
                tail = chunk[-overlap:] if overlap > 0 else ""
                cur = [tail, block] if tail else [block]
                cur_len = sum(len(x) for x in cur) + max(0, len(cur) - 1) * 2
            else:
                cur.append(block)
                cur_len += len(block) + (2 if len(cur) > 1 else 0)
    if cur:
        chunk = "\n\n".join(cur).strip()
        chunks.append((heading or f"chunk-{len(chunks)+1}", chunk))
    return chunks


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]{1,2}", text.lower()) if t and t not in STOPWORDS]


def summarize(text: str, limit: int = 180) -> str:
    flat = re.sub(r"\s+", " ", text).strip()
    return flat[:limit] + ("…" if len(flat) > limit else "")


def extract_keywords(text: str, limit: int = 12) -> list[str]:
    counts = Counter(t for t in tokens(text) if len(t) > 1)
    return [k for k, _ in counts.most_common(limit)]


def infer_doc_type(path: Path) -> str:
    if path.suffix.lower() in {".md", ".markdown"}:
        return "markdown"
    if path.suffix.lower() == ".docx":
        return "docx"
    if path.suffix.lower() == ".pdf":
        return "pdf"
    if path.suffix.lower() in IMAGE_EXTS:
        return "image"
    if path.suffix.lower() in VIDEO_EXTS:
        return "video"
    if path.suffix.lower() in SUBTITLE_EXTS:
        return "subtitle"
    if path.suffix.lower() in {".txt"}:
        return "text"
    if path.suffix.lower() in {".json"}:
        return "json"
    if path.suffix.lower() in {".yaml", ".yml"}:
        return "yaml"
    if path.suffix.lower() in {".sql"}:
        return "sql"
    return path.suffix.lower().lstrip(".") or "text"


def infer_title(text: str, path: Path) -> str:
    for line in normalize_whitespace(text).split("\n"):
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return path.stem


def iter_source_files(root: Path, extra_dirs: Iterable[str] = DEFAULT_SOURCE_DIRS) -> Iterator[Path]:
    seen = set()
    for dirname in extra_dirs:
        base = root / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.name in IGNORE_NAMES:
                continue
            if path.suffix.lower() not in SUPPORTED_EXTS:
                continue
            key = str(path.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            yield path


def build_chunks(root: Path, setup: dict, source_dirs: Iterable[str] = DEFAULT_SOURCE_DIRS) -> list[Chunk]:
    rag = setup["rag"]
    max_chars = int(rag["chunk_size"])
    overlap = int(rag["chunk_overlap"])
    chat_model = setup["openai"].get("chat_model", "gpt-4o-mini")
    embedding_model = setup["openai"].get("embedding_model", "text-embedding-3-large")
    records: list[Chunk] = []
    for path in iter_source_files(root, source_dirs):
        text = read_text(path)
        source_hash = sha256_source(path, text)
        title = infer_title(text, path)
        doc_type = infer_doc_type(path)
        for idx, (chunk_title, chunk) in enumerate(chunk_text(text, max_chars=max_chars, overlap=overlap), start=1):
            rec = Chunk(
                source_path=str(path.resolve()),
                source_name=path.name,
                source_hash=source_hash,
                doc_type=doc_type,
                title=title,
                chunk_index=idx,
                chunk_title=chunk_title,
                content=chunk,
                chunk_content=chunk,
                summary=summarize(chunk),
                keywords=extract_keywords(chunk),
                tags=[doc_type],
                rag_model=chat_model,
                embedding_model=embedding_model,
                score=0.0,
            )
            records.append(rec)
    return records


def to_dicts(records: list[Chunk]) -> list[dict]:
    out = []
    for r in records:
        d = dataclasses.asdict(r)
        d["keywords"] = json.dumps(r.keywords, ensure_ascii=False)
        d["tags"] = json.dumps(r.tags, ensure_ascii=False)
        out.append(d)
    return out


def export_index(root: Path, output: Path, setup: dict, source_dirs: Iterable[str] = DEFAULT_SOURCE_DIRS) -> dict:
    records = build_chunks(root, setup, source_dirs)
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(root.resolve()),
        "records": to_dicts(records),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def export_sql(payload: dict, output: Path) -> None:
    lines = ["-- Generated by skill-rag", "START TRANSACTION;"]
    grouped: dict[str, list[dict]] = {}
    for r in payload["records"]:
        grouped.setdefault(r["source_path"], []).append(r)
    for source_path, records in grouped.items():
        head = records[0]
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append("")
        lines.append("INSERT INTO rag_sources (source_path, source_name, doc_type, title, source_hash, status, last_scanned_at)")
        lines.append("VALUES (")
        lines.append(
            "  "
            + ", ".join(
                [
                    sql_literal(source_path),
                    sql_literal(head["source_name"]),
                    sql_literal(head["doc_type"]),
                    sql_literal(head["title"]),
                    sql_literal(head["source_hash"]),
                    sql_literal("active"),
                    sql_literal(now),
                ]
            )
        )
        lines.append(") ON DUPLICATE KEY UPDATE")
        lines.append("  id = LAST_INSERT_ID(id),")
        lines.append("  source_name = VALUES(source_name),")
        lines.append("  doc_type = VALUES(doc_type),")
        lines.append("  title = VALUES(title),")
        lines.append("  source_hash = VALUES(source_hash),")
        lines.append("  status = VALUES(status),")
        lines.append("  last_scanned_at = VALUES(last_scanned_at),")
        lines.append("  updated_at = CURRENT_TIMESTAMP;")
        lines.append("SET @source_id := LAST_INSERT_ID();")
        lines.append("")
        for idx, r in enumerate(records, start=1):
            lines.append("INSERT INTO rag_chunks (source_id, chunk_index, chunk_title, content, chunk_content, summary, keywords, tags, rag_model, embedding_model, score, status)")
            lines.append("VALUES (")
            lines.append(
                "  "
                + ", ".join(
                    [
                        "@source_id",
                        sql_literal(r["chunk_index"]),
                        sql_literal(r["chunk_title"]),
                        sql_literal(r["content"]),
                        sql_literal(r["chunk_content"]),
                        sql_literal(r["summary"]),
                        sql_literal(r["keywords"]),
                        sql_literal(r["tags"]),
                        sql_literal(r["rag_model"]),
                        sql_literal(r["embedding_model"]),
                        sql_literal(r["score"]),
                        sql_literal(r["status"]),
                    ]
                )
            )
            lines.append(") ON DUPLICATE KEY UPDATE")
            lines.append("  chunk_title = VALUES(chunk_title),")
            lines.append("  content = VALUES(content),")
            lines.append("  chunk_content = VALUES(chunk_content),")
            lines.append("  summary = VALUES(summary),")
            lines.append("  keywords = VALUES(keywords),")
            lines.append("  tags = VALUES(tags),")
            lines.append("  rag_model = VALUES(rag_model),")
            lines.append("  embedding_model = VALUES(embedding_model),")
            lines.append("  score = VALUES(score),")
            lines.append("  status = VALUES(status),")
            lines.append("  updated_at = CURRENT_TIMESTAMP;")
    lines.append("")
    lines.append("COMMIT;")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{s}'"


def score_query(query: str, record: dict) -> float:
    q = set(tokens(query))
    if not q:
        return 0.0
    hay = " ".join([record["title"], record["chunk_title"], record["summary"], record["content"], " ".join(record.get("keywords", [])), " ".join(record.get("tags", []))]).lower()
    h = set(tokens(hay))
    overlap = len(q & h)
    if overlap == 0:
        return 0.0
    bonus = 0.0
    if any(tok in record["title"].lower() for tok in q):
        bonus += 0.5
    if any(tok in record["chunk_title"].lower() for tok in q):
        bonus += 0.25
    return overlap + bonus


def query_index(payload: dict, question: str, top_k: int = 5) -> list[dict]:
    records = payload["records"]
    scored = []
    for r in records:
        s = score_query(question, r)
        if s <= 0:
            continue
        item = dict(r)
        item["score"] = s
        scored.append(item)
    scored.sort(key=lambda x: (-x["score"], x["source_name"], x["chunk_index"]))
    return scored[:top_k]


def render_answer(question: str, hits: list[dict]) -> str:
    if not hits:
        return (
            f"問題：{question}\n"
            "找不到直接對應的內容。請補充更明確的關鍵字、檔名，或要查的主題。"
        )
    lines = [f"問題：{question}", "", "答案候選："]
    for hit in hits:
        lines.append(f"- {hit['title']} / {hit['source_name']} / chunk {hit['chunk_index']} (score={hit['score']:.2f})")
        lines.append(f"  {hit['summary']}")
        for label, url in media_links_for_hit(hit):
            lines.append(f"  媒體：[{label}](<{url}>)")
    lines.append("")
    lines.append("來源：")
    for hit in hits:
        source_name = hit["source_name"]
        if hit.get("doc_type") in {"image", "video"} and hit.get("source_path"):
            source_url = Path(hit["source_path"]).resolve().as_uri()
            source_name = f"[{source_name}](<{source_url}>)"
        lines.append(f"- {source_name} :: chunk {hit['chunk_index']}")
    return "\n".join(lines)


def load_index(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser()
    setup = load_setup(Path(args.setup).expanduser())
    payload = export_index(root, Path(args.output).expanduser(), setup, source_dirs=args.source_dir)
    if args.sql_output:
        export_sql(payload, Path(args.sql_output).expanduser())
    print(json.dumps({"records": len(payload["records"]), "output": str(Path(args.output).resolve())}, ensure_ascii=False))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    payload = load_index(Path(args.index).expanduser())
    hits = query_index(payload, args.question, top_k=args.top_k)
    print(render_answer(args.question, hits))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    setup = load_setup(Path(args.setup).expanduser())
    print(json.dumps({"ok": True, "mysql": {"configured": True}, "rag": setup["rag"]}, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="skill-rag", description="Scan, index, and query multi-file knowledge.")
    p.add_argument("--setup", default="setup.json", help="Path to setup.json")
    sub = p.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan", help="Scan source files and export an index JSON")
    scan.add_argument("--root", default=".", help="Project root to scan")
    scan.add_argument("--output", default="build/index.json", help="Index JSON output")
    scan.add_argument("--sql-output", default="build/index.sql", help="Optional SQL scaffold output")
    scan.add_argument("--source-dir", action="append", default=list(DEFAULT_SOURCE_DIRS), help="Source directories to scan (repeatable)")
    scan.set_defaults(func=cmd_scan)

    query = sub.add_parser("query", help="Query a built index JSON")
    query.add_argument("--index", default="build/index.json", help="Index JSON path")
    query.add_argument("--question", required=True, help="Question to answer")
    query.add_argument("--top-k", type=int, default=5, help="Number of hits to return")
    query.set_defaults(func=cmd_query)

    validate = sub.add_parser("validate-config", help="Validate setup.json")
    validate.set_defaults(func=cmd_validate)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
