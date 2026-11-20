"""A long web_evidence still from a full-page screenshot: the headline and the paragraphs that matter stitched into one
column (ads, photos and sidebars between them left out), and each phrase to highlight found by on-device OCR
(show more of the page or the whole news item, not one sentence).

  python3 doc_evidence.py <spec.json>
spec: {"src": full-page png, "out": stitched png, "x": [x0, x1], "slices": [[y0, y1], ...] (source pixels, top to bottom),
       "find": [phrase, ...]}
Prints the stitched size and, per phrase, its box [x, y, w, h] in the stitched image (for web_evidence "marks") or ✗ when
OCR does not see it. Writes <out>.json beside it with the same: {"size": [w, h], "boxes": {phrase: box | null}}.
OCR is Apple Vision (VNRecognizeTextRequest, zh-Hant + en), like doc_cutout's foreground mask; macOS only.
"""
import json, sys
from pathlib import Path

import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[4] / "tools/config"))
import s2f_config; s2f_config.load()
from doc_common import read_json
from PIL import Image

GAP = 36   # white space between stitched slices, source pixels


def stitch(src, x, slices):
    im = Image.open(src).convert("RGB")
    x0, x1 = x
    h = sum(b - a for a, b in slices) + GAP * (len(slices) - 1)
    out = Image.new("RGB", (x1 - x0, h), "white")
    y = 0
    for a, b in slices:
        out.paste(im.crop((x0, a, x1, b)), (0, y))
        y += b - a + GAP
    return out


def ocr_lines(path):
    """[(text, [x, y, w, h])] in image pixels, top-left origin."""
    import Quartz, Vision
    from Foundation import NSURL
    url = NSURL.fileURLWithPath_(str(Path(path).resolve()))
    src = Quartz.CGImageSourceCreateWithURL(url, None)
    img = Quartz.CGImageSourceCreateImageAtIndex(src, 0, None)
    W, H = Quartz.CGImageGetWidth(img), Quartz.CGImageGetHeight(img)
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLanguages_(["zh-Hant", "en-US"])
    req.setUsesLanguageCorrection_(False)
    Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(img, None).performRequests_error_([req], None)
    out = []
    for r in req.results() or []:
        cand = r.topCandidates_(1)[0]
        text = cand.string()
        out.append((text, cand, W, H))
    return out


def find_box(lines, phrase):
    """Box of phrase inside one OCR line (Vision gives the sub-range box), or None."""
    from Foundation import NSMakeRange
    want = phrase.replace(" ", "")
    for text, cand, W, H in lines:
        keep = [k for k, c in enumerate(text) if c != " "]   # OCR spaces CJK and digits unevenly: match without spaces
        i = "".join(text[k] for k in keep).find(want)
        if i < 0:
            continue
        a, b = keep[i], keep[i + len(want) - 1] + 1
        obs, _ = cand.boundingBoxForRange_error_(NSMakeRange(a, b - a), None)
        if obs is None:
            continue
        bb = obs.boundingBox()
        x, y, w, h = bb.origin.x * W, (1 - bb.origin.y - bb.size.height) * H, bb.size.width * W, bb.size.height * H
        return [round(x), round(y), round(w), round(h)]
    return None


def main():
    spec_path = Path(sys.argv[1]).resolve()
    spec = read_json(spec_path)
    base = spec_path.parent
    out = base / spec["out"]
    im = stitch(base / spec["src"], spec["x"], spec["slices"])
    im.save(out)
    lines = ocr_lines(out)
    boxes = {p: find_box(lines, p) for p in spec.get("find", [])}
    out.with_suffix(".json").write_text(json.dumps({"size": list(im.size), "boxes": boxes}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out.name}: {im.size[0]} x {im.size[1]}")
    for p, b in boxes.items():
        print(f"  {p}: {b if b else '✗ not found by OCR'}")
    sys.exit(1 if any(b is None for b in boxes.values()) else 0)


if __name__ == "__main__":
    main()
