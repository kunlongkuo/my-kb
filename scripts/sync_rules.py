#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sync core rules to other agent rule files in root directory."""

import shutil
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    src = root / "core_rules.md"
    
    if not src.exists():
        print(f"Error: Core rules source file '{src}' does not exist.")
        return
        
    targets = ["agents.md", "claude.md", "ANTIGRAVITY.md"]
    
    print(f"Reading core rules from '{src.name}'...")
    
    for filename in targets:
        dest = root / filename
        try:
            # Check if they are the same file (e.g. HardLink)
            if dest.exists() and dest.stat().st_ino == src.stat().st_ino:
                print(f"'{filename}' is a HardLink pointing to '{src.name}'. No sync needed (OS level auto-sync).")
                continue
            shutil.copyfile(src, dest)
            print(f"Successfully synced to '{filename}'")
        except shutil.SameFileError:
            print(f"'{filename}' and '{src.name}' are the same file (SameFileError). No sync needed.")
        except Exception as e:
            print(f"Error syncing to '{filename}': {e}")

if __name__ == "__main__":
    main()
