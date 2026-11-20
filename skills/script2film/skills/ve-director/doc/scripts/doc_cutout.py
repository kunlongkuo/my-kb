"""Cut a person (or the main subject) out of a photo for the 2.5D photo layer (lib.js overlays: fg).

  python3 doc_cutout.py <in.jpg> <out.png>
A photo layer with "fg": "auto" gets <src stem>_fg.png next to its src, made once (doc_code.py calls fg_auto).
Apple Vision's foreground mask (macOS 14+, built in, no model download; tested on three player photos, clean
edges). pyobjc rather than a Swift binary: swiftc on this machine's CommandLineTools stops on a duplicate SwiftBridging
module map. Same size as the source, transparent ground, so it lines up with the photo under it.
"""
import sys
from pathlib import Path


def cutout(src, dst):
    try:
        import Quartz, Vision
        from Foundation import NSURL
    except ImportError:
        sys.exit("✗ fg auto needs macOS with pyobjc (Vision, Quartz); cut the photo out by hand and give fg a png path")
    handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(NSURL.fileURLWithPath_(str(src)), None)
    req = Vision.VNGenerateForegroundInstanceMaskRequest.alloc().init()
    ok, err = handler.performRequests_error_([req], None)
    if not ok or not req.results():
        sys.exit(f"✗ no foreground found in {src} ({err}); give fg a hand-made png or drop it")
    obs = req.results()[0]
    buf, err = obs.generateMaskedImageOfInstances_fromRequestHandler_croppedToInstancesExtent_error_(obs.allInstances(), handler, False, None)
    if buf is None:
        sys.exit(f"✗ cut-out failed for {src} ({err})")
    ci = Quartz.CIImage.imageWithCVPixelBuffer_(buf)
    cg = Quartz.CIContext.context().createCGImage_fromRect_(ci, ci.extent())
    out = Quartz.CGImageDestinationCreateWithURL(NSURL.fileURLWithPath_(str(dst)), "public.png", 1, None)
    Quartz.CGImageDestinationAddImage(out, cg, None)
    if not Quartz.CGImageDestinationFinalize(out):
        sys.exit(f"✗ could not write {dst}")


def fg_path(src):
    """Where "fg": "auto" puts the cut-out of src (a project-relative path string)."""
    p = Path(src)
    return str(p.with_name(p.stem + "_fg.png"))


def fg_auto(P, params):
    """params with every photo layer's "fg": "auto" replaced by its cut-out path, cutting out the ones not made yet."""
    photos = params.get("photos")
    if not photos or not any(o.get("fg") == "auto" for o in photos):
        return params
    out = []
    for o in photos:
        if o.get("fg") == "auto":
            o = {**o, "fg": fg_path(o["src"])}
            if not (P / o["fg"]).is_file():
                cutout(P / o["src"], P / o["fg"])
        out.append(o)
    return {**params, "photos": out}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    cutout(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
