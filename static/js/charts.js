export function drawChart(svg, values) {
  svg.replaceChildren();
  if (!values.length) return;
  const ns = 'http://www.w3.org/2000/svg',
    max = Math.max(20, ...values.map(v => v.wpm));
  for (let i = 0; i < 3; i++) {
    const y = 15 + i * 45,
      line = document.createElementNS(ns, 'line');
    for (const [k, v] of Object.entries({
        x1: 35,
        x2: 590,
        y1: y,
        y2: y,
        stroke: 'currentColor',
        'stroke-opacity': '.12'
      })) line.setAttribute(k, v);
    svg.append(line);
    const label = document.createElementNS(ns, 'text');
    label.setAttribute('x', 0);
    label.setAttribute('y', y + 4);
    label.setAttribute('fill', 'currentColor');
    label.setAttribute('font-size', '9');
    label.textContent = Math.round(max * (1 - i / 2));
    svg.append(label)
  }
  const line = document.createElementNS(ns, 'polyline');
  line.setAttribute('points', values.map((v, i) => `${35+i/Math.max(1,values.length-1)*555},${105-v.wpm/max*90}`).join(' '));
  line.setAttribute('fill', 'none');
  line.setAttribute('stroke', 'currentColor');
  line.setAttribute('stroke-width', '2');
  svg.append(line);
}
for (const svg of document.querySelectorAll('[data-chart]')) drawChart(svg, JSON.parse(document.getElementById(svg.dataset.chart).textContent));
