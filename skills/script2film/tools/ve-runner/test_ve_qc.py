from ve_qc import state

LOG_WAIT = """10:00:01 Create Image sent; waiting for candidates (up to 4 min)
10:00:20 2 candidate(s)
10:00:20 QC shot1: 2 candidate(s); compare /r/shot1_compare.jpg
10:00:21 QC WAITING: write one of [12rq] to /r/decision.txt
"""


def test_waiting_gate():
    s = state(LOG_WAIT)
    assert s["pending"] and s["label"] == "shot1" and s["n"] == 2 and s["compare"] == "/r/shot1_compare.jpg"
    assert not s["done"] and not s["failed"]


def test_answered_gate_is_not_pending():
    s = state(LOG_WAIT + "10:00:30 decision: 2\n10:00:31 Create Video sent (plain)\n")
    assert not s["pending"] and s["waits"] == 1


def test_reroll_opens_a_second_gate_for_the_same_label():
    log = LOG_WAIT + "10:00:30 decision: r\n10:00:30 shot1 re-roll\n10:00:50 QC shot1: 1 candidate(s)\n10:00:51 QC WAITING: write one of [1rq] to /r/decision.txt\n"
    s = state(log)
    assert s["pending"] and s["waits"] == 2 and s["n"] == 1 and s["compare"] is None


def test_finished_and_failed():
    assert state(LOG_WAIT + "10:01:00 decision: 1\n10:02:00 all 3 shot(s) submitted. Collect the clips with:\n")["done"]
    assert state(LOG_WAIT + "10:01:00 decision: 1\n10:02:00 all 0 shot(s) submitted (no video); saved images: {'shot1': 1}\n")["done"]
    assert state("Traceback (most recent call last):\n")["failed"]
    assert state(LOG_WAIT + "10:00:30 decision: q\n10:00:30 stopped: stopped at QC gate\n")["failed"]
    assert state("10:00:30 crashed:\nTraceback (most recent call last):\n")["failed"]


def test_compare_path_with_spaces():
    s = state("10:00:20 QC shot2: 2 candidate(s); compare /a b/shot2_compare.jpg\n10:00:21 QC WAITING: x\n")
    assert s["compare"] == "/a b/shot2_compare.jpg"


def test_skip_answer_closes_the_gate():
    s = state(LOG_WAIT + "10:00:30 decision: s\n10:00:30 shot1 skipped at QC (no video)\n")
    assert not s["pending"] and not s["failed"]
