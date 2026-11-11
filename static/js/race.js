const cfg = JSON.parse(document.getElementById('race-config').textContent),
  field = document.getElementById('race-input'),
  status = document.getElementById('race-status');
let started = null,
  offset = 0,
  events = [],
  previous = '',
  timer, lastSent = 0,
  finished = false;
const socket = new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/race/${cfg.id}/`);
socket.onclose = () => {
  field.disabled = true;
  status.textContent = 'Connection closed. Reload to reconnect. The server must use ASGI for races.'
};
socket.onmessage = e => {
  const data = JSON.parse(e.data);
  if (data.type === 'error') {
    status.textContent = data.message;
    return
  }
  offset = Date.parse(data.server_now) - Date.now();
  if (data.starts_at && !started) {
    started = Date.parse(data.starts_at);
    timer = setInterval(() => {
      const remaining = started - Date.now() - offset;
      if (remaining > 0) {
        status.textContent = 'Starting in ' + Math.ceil(remaining / 1000)
      } else if (!finished) {
        field.disabled = false;
        status.textContent = 'Go!';
        clearInterval(timer);
        field.focus()
      }
    }, 100)
  } else if (!started) status.textContent = 'Waiting for the host to start.';
  const players = document.getElementById('players');
  players.replaceChildren();
  for (const player of data.players) {
    const p = document.createElement('p');
    p.textContent = `${player.name} · ${Math.round(player.progress)}%${player.finished?' · '+player.wpm+' WPM':''}`;
    players.append(p)
  }
};
document.getElementById('race-start')?.addEventListener('click', () => {
  if (socket.readyState === 1) socket.send(JSON.stringify({
    type: 'start'
  }))
});

function send() {
  if (socket.readyState === 1 && started) socket.send(JSON.stringify({
    type: 'progress',
    elapsed: (Date.now() + offset - started) / 1000,
    events
  }))
}
field.addEventListener('paste', e => e.preventDefault());
field.addEventListener('drop', e => e.preventDefault());
field.addEventListener('input', e => {
  const text = field.value.normalize('NFC');
  if (!text.startsWith(previous) && !previous.startsWith(text)) {
    field.value = previous;
    return
  }
  if (text.length - previous.length > 1 && !e.isComposing) {
    field.value = previous;
    return
  }
  events.push({
    t: Math.max(0, Date.now() + offset - started),
    v: text,
    kind: text.length < previous.length ? 'deleteContentBackward' : e.isComposing ? 'insertCompositionText' : 'insertText'
  });
  previous = text;
  if (Date.now() - lastSent > 200) {
    send();
    lastSent = Date.now()
  }
  if (text === cfg.target) {
    finished = true;
    field.disabled = true;
    status.textContent = 'Finished. Checking result…';
    setTimeout(send, 250)
  }
});
