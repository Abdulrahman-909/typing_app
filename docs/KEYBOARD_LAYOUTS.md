# Keyboard guide status
English: basic unshifted US QWERTY rows and finger hints, project-authored. Number row, Shift key highlighting, and alternate layouts are not implemented.

Dari and Pashto: illustrative letter rows with prominent unverified labels. They are NOT validated mappings of Windows Persian Standard or Windows Pashto. Do not use these guides to teach exact key positions until a native keyboard user reviews every key against the relevant Windows layout. Full Shift/AltGr layers and Pashto-specific letters need expansion.

Data lives in static/layouts/*.json. The practice engine accepts Unicode text independently of these guides. Review content separately from keyboard mappings. In Django admin, mark a passage reviewed only after a fluent speaker has checked it.

Noto Naskh Arabic is bundled under its original license. RTL text is rendered as intact word spans, preserving contextual glyph shaping. Word-level feedback and a current-word underline are used rather than an exact per-character RTL caret. Native OS IME interaction still needs manual Windows testing.
