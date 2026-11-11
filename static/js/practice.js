import {
  units,
  score
} from './scoring.js';
import {
  drawChart
} from './charts.js';
const $ = id => document.getElementById(id),
  csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
let session = null,
  events = [],
  startTime = null,
  interval = null,
  active = false,
  composing = false,
  last = '',
  inserted = 0,
  errors = 0,
  loading = false,
  audioContext, layout = null;
const controls = ['language', 'mode', 'amount', 'difficulty', 'punctuation', 'numbers', 'ranked'];
async function api(path, data) {
  const r = await fetch(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrf
    },
    body: JSON.stringify(data)
  });
  const out = await r.json();
  if (!r.ok) throw Error(out.error || 'Request failed. Please try again.');
  return out
}

function options() {
  return Object.fromEntries(controls.filter(id => $(id)).map(id => [id, $(id).type === 'checkbox' ? $(id).checked : $(id).value]))
}
async function load(extra = {}) {
  if (loading) return;
  loading = true;
  clearInterval(interval);
  active = false;
  startTime = null;
  events = [];
  last = '';
  inserted = errors = 0;
  $('typing').disabled = true;
  $('status').textContent = 'Preparing your passage…';
  $('results').hidden = true;
  try {
    const lesson = new URLSearchParams(location.search).get('lesson');
    session = await api('/api/start/', {
      ...options(),
      ...(lesson ? {
        lesson
      } : {}),
      ...(new URLSearchParams(location.search).has('weak') ? {
        weak: true
      } : {}),
      ...(new URLSearchParams(location.search).get('challenge') ? {
        challenge: new URLSearchParams(location.search).get('challenge')
      } : {}),
      ...extra
    });
    $('typing').value = '';
    $('typing').dir = session.language === 'en' ? 'ltr' : 'rtl';
    $('typing').lang = session.language;
    $('passage').dir = $('typing').dir;
    $('passage').lang = session.language;
    $('language-note').hidden = session.language === 'en';
    $('typing').disabled = false;
    active = true;
    controls.forEach(id => {
      if ($(id)) $(id).disabled = false
    });
    $('state-label').textContent = 'READY WHEN YOU ARE';
    $('status').textContent = 'Start typing to begin.';
    $('typing-help').textContent = 'Stay accurate. Speed will follow.';
    render();
    updateMetrics();
    await keyboard();
  } catch (e) {
    $('status').textContent = e.message
  } finally {
    loading = false
  }
}

function render() {
  const el = $('passage'),
    target = units(session.target),
    typed = units(last);
  el.replaceChildren();
  // Render an intact word span for RTL. No per-letter splitting of joined glyphs.
  if (session.language !== 'en') {
    let pos = 0;
    for (const word of session.target.split(' ')) {
      const span = document.createElement('span'),
        len = units(word).length;
      span.textContent = word;
      span.dataset.start = pos;
      if (typed.length >= pos + len) span.className = units(word).every((c, i) => typed[pos + i] === c) ? 'correct' : 'incorrect';
      if (typed.length >= pos && typed.length <= pos + len) span.classList.add('current');
      el.append(span, document.createTextNode(' '));
      pos += len + 1;
      if (pos > typed.length + 500) break;
    }
  } else {
    target.slice(0, typed.length + 500).forEach((c, i) => {
      const span = document.createElement('span');
      span.textContent = c;
      span.className = i < typed.length ? (c === typed[i] ? 'correct' : 'incorrect') : i === typed.length ? 'current' : '';
      el.append(span)
    })
  }
  const current = el.querySelector('.current');
  if (current) el.scrollTop = Math.max(0, current.offsetTop - el.offsetTop - 45);
  const next = target[typed.length];
  document.querySelectorAll('.key').forEach(key => key.classList.toggle('active', key.dataset.char === next?.toLowerCase()));
  if (layout) {
    const key = layout.keys.find(k => k.char === next?.toLowerCase());
    $('finger-guide').textContent = key ? `${key.label}: ${key.finger}${next!==next?.toLowerCase()?' + Shift':''}` : 'Follow the next character in the passage.'
  }
}

function updateMetrics() {
  const elapsed = startTime === null ? 0 : (performance.now() - startTime) / 1000;
  const m = score(session.target, last, elapsed, inserted, errors);
  $('timer').textContent = session.mode === 'time' ? Math.max(0, Math.ceil(session.amount - elapsed)) : Math.floor(elapsed);
  $('timer-unit').textContent = session.mode === 'time' ? 'seconds left' : 'seconds elapsed';
  $('wpm').textContent = elapsed < .3 ? '0' : Math.round(m.wpm);
  $('accuracy').textContent = Math.round(m.accuracy) + '%';
}

function sound() {
  if (!$('sound').checked) return;
  try {
    audioContext ??= new AudioContext();
    const o = audioContext.createOscillator(),
      g = audioContext.createGain();
    o.type = 'sine';
    o.frequency.value = 440;
    g.gain.value = Number($('volume').value) / 100 * .025;
    o.connect(g);
    g.connect(audioContext.destination);
    o.start();
    o.stop(audioContext.currentTime + .025)
  } catch {}
}

function input(kind = 'insertText') {
  if (!active || composing || !session) return;
  const now = performance.now();
  if (startTime !== null && session.mode === 'time' && now - startTime >= session.amount * 1000) {
    $('typing').value = last;
    finish();
    return
  }
  let value = $('typing').value.normalize('NFC');
  const old = units(last),
    next = units(value);
  let common = 0;
  while (common < Math.min(old.length, next.length) && old[common] === next[common]) common++;
  if ((common < Math.min(old.length, next.length) && !(kind === 'insertCompositionText' && common >= old.length - 1)) || (next.length - common > 1 && kind !== 'insertCompositionText')) {
    $('typing').value = last;
    $('typing-help').textContent = 'Type at the end of the text. Use Backspace to correct.';
    return
  }
  if (value === last) return;
  if (startTime === null) {
    startTime = now;
    controls.forEach(id => {
      if ($(id)) $(id).disabled = true
    });
    $('state-label').textContent = 'IN THE FLOW';
    $('status').textContent = 'Test started. Keep going.';
    interval = setInterval(() => {
      updateMetrics();
      if (session.mode === 'time' && performance.now() - startTime >= session.amount * 1000) finish()
    }, 70)
  }
  const target = units(session.target);
  for (let i = common; i < next.length; i++) {
    inserted++;
    if (next[i] !== target[i]) errors++
  }
  last = value;
  events.push({
    t: Math.round(now - startTime),
    v: value,
    kind: next.length < old.length ? 'deleteContentBackward' : kind
  });
  render();
  updateMetrics();
  sound();
  if (session.mode === 'words' && last === session.target) finish();
}
async function finish() {
  if (!active || startTime === null) return;
  active = false;
  clearInterval(interval);
  const elapsed = session.mode === 'time' ? session.amount : events.at(-1).t / 1000;
  $('typing').disabled = true;
  $('state-label').textContent = 'COMPLETE';
  $('status').textContent = 'Checking your result…';
  try {
    const out = await api('/api/submit/', {
      token: session.token,
      elapsed: Math.max(.001, elapsed),
      events
    });
    $('results').hidden = false;
    $('result-metrics').replaceChildren();
    for (const [label, value] of [
        ['Net WPM', out.metrics.wpm],
        ['Accuracy', out.metrics.accuracy + '%'],
        ['Mistakes', out.metrics.mistakes],
        ['Error inputs', out.metrics.error_keys]
      ]) {
      const d = document.createElement('div'),
        strong = document.createElement('strong'),
        small = document.createElement('small');
      strong.textContent = value;
      small.textContent = label;
      d.append(strong, small);
      $('result-metrics').append(d)
    }
    drawChart($('result-chart'), out.samples);
    $('save-note').textContent = out.saved ? `Saved to your progress. Ranking: ${out.review}.` : 'Guest result: shown for this session only. Create an account to save future tests.';
    $('result-link').hidden = !out.saved;
    if (out.saved) {
      $('result-link').href = '/results/' + out.result_id + '/';
      $('result-link').textContent = 'View saved result →'
    }
    $('status').textContent = 'Test complete. Your result is ready.';
    $('wpm').textContent = Math.round(out.metrics.wpm);
    $('accuracy').textContent = out.metrics.accuracy + '%';
    $('timer').textContent = session.mode === 'time' ? '0' : Math.round(elapsed)
  } catch (e) {
    $('status').textContent = e.message + ' Use New test to continue.'
  } finally {
    controls.forEach(id => {
      if ($(id)) $(id).disabled = false
    })
  }
}
$('typing').addEventListener('compositionstart', () => composing = true);
$('typing').addEventListener('compositionend', () => {
  composing = false;
  input('insertCompositionText')
});
$('typing').addEventListener('input', e => {
  if (!composing) input(e.inputType === 'insertCompositionText' ? 'insertCompositionText' : e.inputType === 'deleteContentBackward' ? 'deleteContentBackward' : 'insertText')
});
for (const type of ['paste', 'drop']) $('typing').addEventListener(type, e => {
  e.preventDefault();
  $('typing-help').textContent = 'Please type the passage yourself. Paste is available in Custom text below.'
});
$('typing').addEventListener('keydown', e => {
  if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(e.key)) e.preventDefault();
  if (e.key === 'Escape') $('typing').blur()
});
$('typing').addEventListener('click', () => {
  $('typing').selectionStart = $('typing').selectionEnd = $('typing').value.length
});
$('restart').onclick = () => {
  if (!startTime || !active || confirm('End this unfinished test and start a new one?')) load()
};
$('retry').onclick = () => {
  if (!startTime || !active || confirm('Restart this passage?')) load({
    retry: session.id
  })
};
for (const id of controls) $(id)?.addEventListener('change', () => {
  if (id === 'mode') {
    $('amount').replaceChildren(...($(id).value === 'time' ? [15, 30, 60, 120] : [10, 25, 50, 100]).map(n => new Option(n, n)));
    $('amount').value = $(id).value === 'time' ? '30' : '25'
  }
  load()
});
$('font-size').value = localStorage.getItem('typing-size') || '29';

function resize() {
  $('passage').style.fontSize = $('font-size').value + 'px';
  localStorage.setItem('typing-size', $('font-size').value)
}
$('font-size').onchange = resize;
resize();
$('show-keyboard').onchange = () => {
  $('keyboard-panel').hidden = !$('show-keyboard').checked
};
async function keyboard() {
  const r = await fetch('/static/layouts/' + session.language + '.json');
  layout = await r.json();
  $('keyboard').replaceChildren();
  $('keyboard-label').textContent = layout.name + ' · ' + layout.review_status;
  for (const row of layout.rows) {
    const div = document.createElement('div');
    div.className = 'key-row';
    for (const char of row) {
      const key = document.createElement('span');
      key.className = 'key';
      key.dataset.char = char;
      key.textContent = char === ' ' ? 'space' : char;
      div.append(key)
    }
    $('keyboard').append(div)
  }
}
$('custom-start').onclick = () => {
  if ($('ranked')) $('ranked').checked = false;
  load({
    custom: $('custom-text').value,
    ranked: false
  })
};
$('custom-file').onchange = async () => {
  const file = $('custom-file').files[0];
  if (!file) return;
  const data = new FormData();
  data.append('file', file);
  try {
    const r = await fetch('/api/upload/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrf
      },
      body: data
    });
    const out = await r.json();
    if (!r.ok) throw Error(out.error);
    $('custom-text').value = out.text
  } catch (e) {
    $('status').textContent = e.message
  }
};
for (const id of ['sound', 'volume', 'show-keyboard']) {
  const control = $(id),
    saved = localStorage.getItem('preference-' + id);
  if (saved !== null) {
    if (control.type === 'checkbox') control.checked = saved === 'true';
    else control.value = saved
  }
  control.addEventListener('change', () => localStorage.setItem('preference-' + id, control.type === 'checkbox' ? control.checked : control.value));
}
$('keyboard-panel').hidden = !$('show-keyboard').checked;
load();
