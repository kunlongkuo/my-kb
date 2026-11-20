#!/usr/bin/env node
// Check that local links in .md / .html files point to files that exist.
//
// Usage: node check-links.mjs <file> [<file> ...]
//
// Collects Markdown link targets ([text](target), ![alt](target)) and
// src / href / poster attribute values, skips external and in-page targets
// (http:, https:, mailto:, #..., data:), resolves the rest relative to the
// file that contains them, and lists every target that does not exist.
// Exit code: 0 = all targets exist, 1 = something is missing, 2 = bad usage.
import fs from "node:fs";
import path from "node:path";

const files = process.argv.slice(2);
if (files.length === 0) {
    console.error("usage: node check-links.mjs <file.md|file.html> [...]");
    process.exit(2);
}

const SKIP = /^(https?:|mailto:|#|data:)/i;
const MD_LINK = /!?\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+["'(][^)]*)?\)/g;
const ATTR = /\b(?:src|href|poster)\s*=\s*(?:"([^"]*)"|'([^']*)')/gi;

let missing = 0;
let checked = 0;

for (const file of files) {
    if (!fs.existsSync(file)) {
        console.log(`MISSING FILE  ${file}`);
        missing++;
        continue;
    }
    const text = fs.readFileSync(file, "utf-8");
    const base = path.dirname(file);
    const targets = [];
    const lineOf = (idx) => text.slice(0, idx).split("\n").length;

    for (const m of text.matchAll(MD_LINK)) {
        targets.push({ raw: m[1].replace(/^<|>$/g, ""), line: lineOf(m.index) });
    }
    for (const m of text.matchAll(ATTR)) {
        targets.push({ raw: m[1] ?? m[2], line: lineOf(m.index) });
    }

    for (const { raw, line } of targets) {
        const t = raw.trim();
        if (!t || SKIP.test(t)) continue;
        let rel = t.split("#")[0].split("?")[0];
        if (!rel) continue;
        try {
            rel = decodeURIComponent(rel);
        } catch {
            // keep the undecoded form
        }
        const target = path.resolve(base, rel);
        checked++;
        if (!fs.existsSync(target)) {
            console.log(`MISSING  ${file}:${line}  ${t}`);
            missing++;
        }
    }
}

console.log(`${checked} local link(s) checked · ${missing} missing`);
process.exit(missing > 0 ? 1 : 0);
