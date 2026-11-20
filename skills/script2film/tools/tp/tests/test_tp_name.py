"""tp_host.tp_name: segment names are built the way TP shows them, so the media-library and My Videos lookups find them."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tp_host  # noqa: E402


def test_tp_name_matches_what_tp_shows():
    assert tp_host.tp_name("tpcheck") == "Tpcheck"
    assert tp_host.tp_name("boba_emma") == "Boba emma"      # 2026-11-18: "Boba_emma part1" was never found
    assert tp_host.tp_name("Ep01r2") == "Ep01r2"
