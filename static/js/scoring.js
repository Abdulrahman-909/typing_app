const segmenter = new Intl.Segmenter(undefined, {
  granularity: 'grapheme'
});
export const units = text => Array.from(segmenter.segment(text.normalize('NFC')), s => s.segment);
export function score(target, typed, elapsed, inserted = units(typed).length, errorKeys = 0) {
  const t = units(target),
    u = units(typed);
  let correct = 0,
    earned = 0,
    pos = 0;
  u.forEach((c, i) => {
    if (c === t[i]) correct++
  });
  for (const word of target.split(' ')) {
    const chars = units(word),
      end = pos + chars.length,
      complete = u.length >= end && chars.every((c, i) => u[pos + i] === c);
    if (complete) earned += chars.length;
    if (complete && u.length > end && end < t.length && u[end] === ' ') earned++;
    pos = end + 1
  }
  return {
    wpm: elapsed > 0 ? earned / 5 * 60 / elapsed : 0,
    raw_wpm: elapsed > 0 ? inserted / 5 * 60 / elapsed : 0,
    accuracy: inserted ? 100 * (inserted - errorKeys) / inserted : 100,
    mistakes: u.length - correct,
    error_keys: errorKeys
  };
}
