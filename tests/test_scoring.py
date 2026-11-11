import pytest
from typing_engine.scoring import score, replay, units


def test_known_wpm():
    assert score("hello world", "hello world", 60)["wpm"] == 2.2


def test_incorrect_word_gets_no_net_credit():
    m = score("hello world", "hello worlx", 60)
    assert m["wpm"] == 1.2 and m["mistakes"] == 1


def test_corrected_error_remains_in_accuracy():
    events = [
        {"t": 0, "v": "x"},
        {"t": 200, "v": "", "kind": "deleteContentBackward"},
        {"t": 300, "v": "h"},
        {"t": 400, "v": "hi"},
    ]
    m = replay("hi", events, 1)
    assert m["accuracy"] == 66.67 and m["final_accuracy"] == 100 and m["mistakes"] == 0


@pytest.mark.parametrize("elapsed", [0, -1, float("nan"), float("inf"), 7201])
def test_bad_time(elapsed):
    with pytest.raises(ValueError):
        score("a", "a", elapsed)


@pytest.mark.parametrize("text", ["دری", "پښتو", "a\u0301", "می\u200cروم", "ک", "ي"])
def test_unicode(text):
    assert score(text, text, 1)["final_accuracy"] == 100


def test_nfc():
    assert units("a\u0301") == units("á")


def test_strict_letter_variants():
    assert score("ک", "ك", 1)["mistakes"] == 1


def test_reject_paste():
    with pytest.raises(ValueError):
        replay("hello", [{"t": 0, "v": "hello", "kind": "insertFromPaste"}], 1)


def test_reject_bulk():
    with pytest.raises(ValueError):
        replay("hello", [{"t": 0, "v": "hello"}], 1)


def test_reject_nonmonotonic():
    with pytest.raises(ValueError):
        replay("ab", [{"t": 100, "v": "a"}, {"t": 0, "v": "ab"}], 1)


def test_composition():
    assert (
        replay("دری", [{"t": 0, "v": "دری", "kind": "insertCompositionText"}], 1)["accuracy"] == 100
    )
