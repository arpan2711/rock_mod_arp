// Fretboard diagram for the Guitar Notes exercises: an SVG string, drawn the way
// printed fretboard charts are drawn so it reads at a glance -
//   * nut on the left, frets running right, fret numbers underneath
//   * high e string on top, low E at the bottom, string names on the left
//   * inlay dots at 3 5 7 9 15, a double dot at 12
//   * open-string notes sit just left of the nut
//   * every note in the exercise is a labelled circle; the root is filled,
//     the note to play next is green and pulses, notes already played fade
//   * opts.ghost: extra positions drawn faint and dashed (the scale elsewhere on
//     the neck); a ghost at a position the sequence uses is skipped
//
// Loaded in the browser (plain script -> window.FRETBOARD) and in node for the
// tests (module.exports). Colours come from CSS classes so the page theme applies.

const FRETBOARD = (() => {
  const NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  const SNAME = ['E', 'A', 'D', 'G', 'B', 'e'];
  const FRETS = 15;                      // the catalogue never goes past 15
  const W = 1000, H = 244;               // viewBox; the svg scales to its container
  const NUT = 72, RIGHT = 8, TOP = 26, GAP = 34, R = 14.5;
  const FW = (W - NUT - RIGHT) / FRETS;  // uniform fret spacing reads better than true taper at 15 frets
  const BOT = TOP + 5 * GAP;

  const fx = f => (f === 0 ? NUT - 26 : NUT + (f - 0.5) * FW);
  const sy = s => TOP + (5 - s) * GAP;   // s: 0 = low E ... 5 = high e
  const noteName = m => NAMES[((m % 12) + 12) % 12];

  // One entry per fretboard position. A position can occur several times in a
  // sequence (up and down); it is 'now' if the current note is there, 'todo' if
  // it still comes later, otherwise 'done'. index < 0 means nothing has started.
  function states(seq, index) {
    const m = new Map();
    seq.forEach((n, i) => {
      const k = n.s + ':' + n.f;
      const st = m.get(k) || { s: n.s, f: n.f, m: n.m, state: 'done' };
      if (index < 0 || i > index) { if (st.state !== 'now') st.state = 'todo'; }
      if (i === index) st.state = 'now';
      m.set(k, st);
    });
    return [...m.values()];
  }

  function svg(seq, opts = {}) {
    const index = opts.index == null ? -1 : opts.index;
    const root = opts.root == null ? null : ((opts.root % 12) + 12) % 12;
    const o = [];
    o.push(`<svg class="fb" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="fretboard">`);
    o.push(`<rect class="fb-board" x="${NUT}" y="${TOP - 16}" width="${W - NUT - RIGHT}" height="${BOT - TOP + 32}" rx="3"/>`);
    for (const f of [3, 5, 7, 9, 15]) o.push(`<circle class="fb-inlay" cx="${fx(f)}" cy="${sy(2.5)}" r="5"/>`);
    o.push(`<circle class="fb-inlay" cx="${fx(12)}" cy="${sy(3.5)}" r="5"/><circle class="fb-inlay" cx="${fx(12)}" cy="${sy(1.5)}" r="5"/>`);
    for (let f = 1; f <= FRETS; f++) o.push(`<line class="fb-fret" x1="${NUT + f * FW}" y1="${TOP - 16}" x2="${NUT + f * FW}" y2="${BOT + 16}"/>`);
    o.push(`<line class="fb-nut" x1="${NUT}" y1="${TOP - 16}" x2="${NUT}" y2="${BOT + 16}"/>`);
    for (let s = 0; s < 6; s++) {
      o.push(`<line class="fb-string" x1="${NUT}" y1="${sy(s)}" x2="${W - RIGHT}" y2="${sy(s)}" stroke-width="${(2.6 - s * 0.32).toFixed(2)}"/>`);
      o.push(`<text class="fb-sname" x="16" y="${sy(s)}" dy=".35em" text-anchor="middle">${SNAME[s]}</text>`);
    }
    for (let f = 1; f <= FRETS; f++) o.push(`<text class="fb-num" x="${fx(f)}" y="${BOT + 34}">${f}</text>`);
    const used = new Set(seq.map(n => n.s + ':' + n.f));
    for (const n of (opts.ghost || [])) {
      if (used.has(n.s + ':' + n.f)) continue;
      const cls = 'fb-n ghost' + (root !== null && n.m % 12 === root ? ' root' : '');
      o.push(`<g class="${cls}" data-pos="${SNAME[n.s]}${n.f}"><circle cx="${fx(n.f)}" cy="${sy(n.s)}" r="${R}"/><text x="${fx(n.f)}" y="${sy(n.s)}" dy=".36em" text-anchor="middle">${noteName(n.m)}</text></g>`);
    }
    for (const n of states(seq, index)) {
      const cls = 'fb-n ' + n.state + (root !== null && n.m % 12 === root ? ' root' : '');
      const x = fx(n.f), y = sy(n.s);
      o.push(`<g class="${cls}" data-pos="${SNAME[n.s]}${n.f}">`);
      if (n.state === 'now') o.push(`<circle class="fb-pulse" cx="${x}" cy="${y}" r="${R}"/>`);
      o.push(`<circle cx="${x}" cy="${y}" r="${R}"/><text x="${x}" y="${y}" dy=".36em" text-anchor="middle">${noteName(n.m)}</text></g>`);
    }
    o.push('</svg>');
    return o.join('');
  }

  return { svg, states, noteName, FRETS, W, H, TOP, GAP, R };
})();

if (typeof window !== 'undefined') window.FRETBOARD = FRETBOARD;
if (typeof module !== 'undefined' && module.exports) module.exports = FRETBOARD;
