#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Batch add YAML frontmatter to wiki markdown files if they don't have one."""

import os
import sys
import io
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WIKI_DIR = Path("wiki")
CATEGORY_MAP = {
    "交通法規": "CONCEPT",
    "勞工法規": "CONCEPT",
    "金融投資": "CONCEPT",
    "烘培食譜": "METHOD",
    "AI工具": "METHOD",
    "工具軟體": "METHOD",
    "youtube-notes": "CONCEPT",
    "System": "METHOD"
}

def add_frontmatter(file_path: Path, dry_run: bool = False) -> bool:
    content = None
    encodings = ['utf-8', 'utf-8-sig', 'cp950', 'gbk']
    
    for enc in encodings:
        try:
            content = file_path.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
            
    if content is None:
        try:
            # Fallback with ignore/replace to guarantee decoding doesn't crash
            content = file_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")
            return False

    # Check if already has frontmatter (starts with ---)
    if content.strip().startswith('---'):
        return False

    title = file_path.stem
    
    # Determine category and tags based on parent directory
    try:
        rel_parent = file_path.parent.relative_to(WIKI_DIR)
        parent_dir = rel_parent.parts[0] if rel_parent.parts else ""
    except ValueError:
        parent_dir = ""

    category = CATEGORY_MAP.get(parent_dir, "CONCEPT")
    tags = [parent_dir] if parent_dir else []
    
    # Get last modification time
    mtime = file_path.stat().st_mtime
    updated_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

    frontmatter = f"""---
title: {title}
category: {category}
tags: {tags}
sources: []
status: verified
updated: {updated_date}
---

"""
    
    if dry_run:
        print(f"[DRY-RUN] Will add frontmatter to: {file_path}")
        print(f"          Title: {title}, Category: {category}, Tags: {tags}, Updated: {updated_date}")
    else:
        file_path.write_text(frontmatter + content, encoding='utf-8')
        print(f"[ADDED] Frontmatter added to: {file_path}")
    
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch add YAML frontmatter to wiki files")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing to files")
    args = parser.parse_args()

    if not WIKI_DIR.exists():
        print(f"Error: {WIKI_DIR} folder not found.")
        sys.exit(1)

    count = 0
    for root, dirs, files in os.walk(WIKI_DIR):
        for file in files:
            if file.endswith(".md"):
                file_path = Path(root) / file
                if add_frontmatter(file_path, dry_run=args.dry_run):
                    count += 1

    print(f"\nTotal files processed (modified): {count}")

if __name__ == "__main__":
    main()
