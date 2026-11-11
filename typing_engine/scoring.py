"""Deterministic grapheme scoring and replay. No Django imports."""

import math
import unicodedata
import regex


def units(text):
    return regex.findall(r"\X", unicodedata.normalize("NFC", text))


def score(target, typed, elapsed, inserted=None, error_keys=0):
    if not math.isfinite(elapsed) or elapsed <= 0 or elapsed > 7200:
        raise ValueError("Invalid elapsed time")
    t, u = units(target), units(typed)
    correct = sum(a == b for a, b in zip(t, u))
    # Only fully correct words earn net WPM; separators belong to the preceding correct word.
    earned = 0
    pos = 0
    for word in target.split(" "):
        chars = units(word)
        end = pos + len(chars)
        complete = len(u) >= end and u[pos:end] == chars
        if complete:
            earned += len(chars)
        if complete and len(u) > end and end < len(t) and u[end] == " ":
            earned += 1
        pos = end + 1
    inserted = len(u) if inserted is None else inserted
    return {
        "wpm": round(earned / 5 * 60 / elapsed, 2),
        "raw_wpm": round(inserted / 5 * 60 / elapsed, 2),
        "accuracy": round(100 * (inserted - error_keys) / inserted, 2) if inserted else 100.0,
        "final_accuracy": round(correct / max(len(u), 1) * 100, 2) if u else 100.0,
        "mistakes": len(u) - correct,
        "error_keys": error_keys,
        "correct_chars": earned,
        "elapsed": round(elapsed, 3),
        "typed_chars": len(u),
    }


def replay(target, events, elapsed):
    """Replay append/delete snapshots, preserving corrected errors in keystroke accuracy."""
    if not isinstance(events, list) or len(events) > 15000:
        raise ValueError("Invalid event log")
    previous = []
    inserted = errors = 0
    last = -1
    target_units = units(target)
    for e in events:
        if not isinstance(e, dict):
            raise ValueError("Invalid event")
        ms = e.get("t")
        value = e.get("v")
        kind = e.get("kind", "insertText")
        if (
            isinstance(ms, bool)
            or not isinstance(ms, (int, float))
            or not math.isfinite(ms)
            or ms < last
            or ms < 0
            or ms > elapsed * 1000 + 100
        ):
            raise ValueError("Invalid event time")
        if not isinstance(value, str) or len(value) > 20000:
            raise ValueError("Invalid text")
        if kind not in ["insertText", "insertCompositionText", "deleteContentBackward"]:
            raise ValueError("Unsupported input type")
        current = units(value)
        common = 0
        while common < min(len(previous), len(current)) and previous[common] == current[common]:
            common += 1
        if common < min(len(previous), len(current)) and not (
            kind == "insertCompositionText" and common >= len(previous) - 1
        ):
            raise ValueError("Only append and backspace are supported")
        added = current[common:]
        if len(added) > 1 and kind != "insertCompositionText":
            raise ValueError("Bulk input is not permitted")
        for i, c in enumerate(added, common):
            inserted += 1
            errors += int(i >= len(target_units) or c != target_units[i])
        previous = current
        last = ms
    return score(target, "".join(previous), elapsed, inserted, errors)
