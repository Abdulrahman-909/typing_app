# Scoring contract
Both engines use NFC and grapheme segmentation (Python regex \X / browser Intl.Segmenter). Arabic/Persian letter variants are strict; ZWNJ, ZWJ, tatweel and diacritics are not silently stripped or mapped. Grapheme segmentation can differ between Unicode versions; pin browsers for formal comparisons.

Net WPM = correct complete-word graphemes (plus each correctly typed following separator) / 5 / minutes. An unfinished or incorrect word contributes zero net characters. Raw WPM = inserted graphemes / 5 / minutes. Five-character words are a convention, not a linguistic statement.

Keystroke accuracy = (insertions - incorrect insertions) / insertions * 100. Backspace does not add an insertion. A corrected error still reduces this accuracy. Final-text accuracy compares the resulting text at logical positions. Mistakes are uncorrected positions; error inputs count all mistakes at insertion time. No input means 100% accuracy but zero speed.

Time starts on first accepted input; timed tests finish at the selected limit. Word tests finish only when the entire passage is correct. Pauses and tab switches do not pause the clock. Selection replacement and middle insertion are rejected; Backspace may cross word boundaries. An early space remains an incorrect positional character. Extra characters count as errors until deleted.

The browser submits snapshots with monotonic elapsed times and input types. The server replays these and recomputes scores and chart samples. Logs are not persisted; only aggregate metrics and error counts are stored. Composition is committed as a single event; large composed strings remain a trust limitation. No browser-based system can prove that every event came from a physical keyboard.

Signed sessions are browser/account bound, expire after two hours and are consumed once. Ranked scores with unusually fast input are hidden pending moderation. Test duration is bounded by server-observed session age. The server does not trust submitted WPM values. These checks reduce abuse; they do not eliminate synthetic input.
