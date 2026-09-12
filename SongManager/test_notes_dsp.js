// Tests for the pitch detector. Run:  node SongManager\test_notes_dsp.js
//
// Synthesises guitar-like tones (a handful of decaying harmonics plus a little
// noise) for every open string and a spread of fretted notes, and checks the
// detector lands on the right note. Octave errors on the low E are the classic
// failure mode, so E2 gets extra attention.

const DSP = require('./notes-dsp.js');

const SR = 48000, N = 2048;
const NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const name = m => NAMES[((Math.round(m) % 12) + 12) % 12] + (Math.floor(Math.round(m) / 12) - 1);
const hz = m => 440 * Math.pow(2, (m - 69) / 12);

// Deterministic noise so a failure reproduces.
let seed = 12345;
const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff - 0.5; };

function tone(freq, { amp = 0.3, harmonics = 8, noise = 0.005, phase = 0.3 } = {}) {
  const out = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    const t = i / SR;
    let s = 0;
    for (let k = 1; k <= harmonics; k++) s += Math.sin(2 * Math.PI * k * freq * t + phase * k) / k;
    out[i] = amp * s / 1.5 + noise * rnd();
  }
  return out;
}

let fails = 0, runs = 0;
function expectNote(label, buf, wantMidi, tolCents = 5) {
  runs++;
  const r = DSP.analyse(buf, SR);
  if (!r.freq) { fails++; console.log(`FAIL ${label}: no pitch (rms ${r.rms.toFixed(4)})`); return; }
  const m = DSP.midi(r.freq);
  const cents = (m - wantMidi) * 100;
  const ok = Math.abs(cents) <= tolCents && r.clarity >= 0.8;
  if (!ok) fails++;
  console.log(`${ok ? ' ok ' : 'FAIL'} ${label.padEnd(26)} want ${name(wantMidi).padEnd(3)} got ${name(m).padEnd(3)} ${r.freq.toFixed(2).padStart(8)} Hz  ${cents >= 0 ? '+' : ''}${cents.toFixed(1)} c  clarity ${r.clarity.toFixed(3)}`);
}

// Open strings, standard tuning: E2 A2 D3 G3 B3 E4
for (const [lbl, m] of [['E2 open (low E)', 40], ['A2 open', 45], ['D3 open', 50], ['G3 open', 55], ['B3 open', 59], ['E4 open', 64]]) {
  expectNote(lbl, tone(hz(m)), m);
}
// Drop D and a 7-string low B
expectNote('D2 (drop D)', tone(hz(38)), 38);
expectNote('B1 (7-string)', tone(hz(35)), 35);
// A spread of fretted notes up the neck
for (const m of [43, 47, 52, 57, 62, 67, 71, 76, 81, 88]) expectNote(`fretted ${name(m)}`, tone(hz(m)), m);
// Low E with a weak fundamental (a plucked string near the bridge): the octave trap.
expectNote('E2 weak fundamental', (() => { const b = tone(hz(40), { harmonics: 10 }); const f = tone(hz(40), { harmonics: 1, noise: 0 }); for (let i = 0; i < N; i++) b[i] -= 0.5 * f[i]; return b; })(), 40, 8);
// Slightly out of tune should read as cents, not a different note
{
  runs++;
  const r = DSP.analyse(tone(hz(45) * Math.pow(2, 20 / 1200)), SR);
  const cents = (DSP.midi(r.freq) - 45) * 100;
  const ok = Math.abs(cents - 20) < 4;
  if (!ok) fails++;
  console.log(`${ok ? ' ok ' : 'FAIL'} ${'A2 +20 cents'.padEnd(26)} read ${cents.toFixed(1)} cents`);
}
// Silence and noise must not produce a note
for (const [lbl, buf] of [['silence', new Float32Array(N)], ['noise only', (() => { const b = new Float32Array(N); for (let i = 0; i < N; i++) b[i] = 0.02 * rnd(); return b; })()]]) {
  runs++;
  const r = DSP.analyse(buf, SR);
  const ok = r.freq === 0 || r.clarity < 0.8;
  if (!ok) fails++;
  console.log(`${ok ? ' ok ' : 'FAIL'} ${lbl.padEnd(26)} freq ${r.freq.toFixed(1)} clarity ${r.clarity.toFixed(3)}`);
}
// Speed: one analysis must be well under the 512-sample hop (10.7 ms at 48 kHz).
{
  const b = tone(hz(40));
  const t0 = process.hrtime.bigint();
  for (let i = 0; i < 50; i++) DSP.analyse(b, SR);
  const ms = Number(process.hrtime.bigint() - t0) / 1e6 / 50;
  runs++;
  const ok = ms < 5;
  if (!ok) fails++;
  console.log(`${ok ? ' ok ' : 'FAIL'} ${'speed'.padEnd(26)} ${ms.toFixed(2)} ms per analysis (budget 10.7 ms)`);
}

console.log(`\n${runs - fails}/${runs} passed`);
process.exit(fails ? 1 : 0);
