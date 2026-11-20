"""No guessing of tool locations here (s2f-1a D7). Until 2026-11-13 this file filled in the Cutline folder from a guessed
sibling checkout, which hid whether doc mode still needed Cutline. Doc mode now runs without it; a test that needs the
Cutline folder (cloud Scribe) sets the variable itself with monkeypatch."""
