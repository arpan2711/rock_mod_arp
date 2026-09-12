// Tests for the exercise catalogue and runner. Run:  node SongManager\test_exercises.js
//
// The shapes are generated from formulas, so the point of these tests is to pin
// the well-known ones to their textbook fingerings - if the generator ever drifts,
// box 1 stops being box 1 and this fails.

const EX = require('./exercises.js');
let fails = 0, runs = 0;
const check = (label, ok, detail) => { runs++; if (!ok) fails++; console.log(`${ok ? ' ok ' : 'FAIL'} ${label}${detail && !ok ? '  -> ' + detail : ''}`); };
const byId = id => EX.CATALOGUE.find(e => e.id === id);
const frets = seq => seq.map(n => EX.SNAME[n.s] + n.f).join(' ');
const names = seq => seq.map(n => EX.noteName(n.m)).join(' ');
const ascent = e => e.seq.slice(0, (e.seq.length + 1) / 2);   // every exercise here is up-then-down

// ---- textbook fingerings ------------------------------------------------------------
check('A minor pentatonic box 1 is E5 E8 A5 A7 D5 D7 G5 G7 B5 B8 e5 e8',
  frets(ascent(byId('a-minor-pent-box1'))) === 'E5 E8 A5 A7 D5 D7 G5 G7 B5 B8 e5 e8', frets(ascent(byId('a-minor-pent-box1'))));
check('A minor pentatonic box 1 notes', names(ascent(byId('a-minor-pent-box1'))) === 'A2 C3 D3 E3 G3 A3 C4 D4 E4 G4 A4 C5', names(ascent(byId('a-minor-pent-box1'))));
check('A blues adds the flat five on A and G',
  frets(ascent(byId('a-blues'))) === 'E5 E8 A5 A6 A7 D5 D7 G5 G7 G8 B5 B8 e5 e8', frets(ascent(byId('a-blues'))));
check('G major two octaves runs G to G, 15 notes',
  names(ascent(byId('g-major-2oct'))) === 'G2 A2 B2 C3 D3 E3 F#3 G3 A3 B3 C4 D4 E4 F#4 G4', names(ascent(byId('g-major-2oct'))));
check('G major E-shape fingering',
  frets(ascent(byId('g-major-2oct'))) === 'E3 E5 A2 A3 A5 D2 D4 D5 G2 G4 G5 B3 B5 e2 e3', frets(ascent(byId('g-major-2oct'))));
check('C major open position starts on the low E',
  frets(ascent(byId('c-major-open'))) === 'E0 E1 E3 A0 A2 A3 D0 D2 D3 G0 G2 B0 B1 B3 e0 e1 e3', frets(ascent(byId('c-major-open'))));
check('A natural minor runs A to A with the Aeolian fingering',
  frets(ascent(byId('a-natural-minor'))) === 'E5 E7 E8 A5 A7 A8 D5 D7 G4 G5 G7 B5 B6 B8 e5', frets(ascent(byId('a-natural-minor'))));
check('A harmonic minor has G# on the D string and the B string at 9',
  frets(ascent(byId('a-harmonic-minor'))).includes('D6') && frets(ascent(byId('a-harmonic-minor'))).includes('B9'), frets(ascent(byId('a-harmonic-minor'))));
check('A Mixolydian has G natural, not G#',
  names(ascent(byId('a-mixolydian'))).includes('G3') && !names(ascent(byId('a-mixolydian'))).includes('G#'), names(ascent(byId('a-mixolydian'))));
check('A Dorian has F#', names(ascent(byId('a-dorian'))).includes('F#3'), names(ascent(byId('a-dorian'))));
check('A major arpeggio is A C# E A C# E A',
  names(ascent(byId('a-major-arp'))) === 'A2 C#3 E3 A3 C#4 E4 A4', names(ascent(byId('a-major-arp'))));
check('A major arpeggio E-shape fingering E5 A4 A7 D7 G6 B5 e5',
  frets(ascent(byId('a-major-arp'))) === 'E5 A4 A7 D7 G6 B5 e5', frets(ascent(byId('a-major-arp'))));
check('A minor arpeggio has C on the G string', frets(ascent(byId('a-minor-arp'))).includes('G5'), frets(ascent(byId('a-minor-arp'))));
check('A7 arpeggio contains G', names(ascent(byId('a-dom7-arp'))).includes('G3'), names(ascent(byId('a-dom7-arp'))));
check('Spider 1-2-3-4 is 47 notes (24 up, 23 down) starting F2', byId('spider-1234').seq.length === 47 && byId('spider-1234').seq[0].m === 41, byId('spider-1234').seq.length);
check('Spider 1-2-3-4 first string is F F# G G#', names(byId('spider-1234').seq.slice(0, 4)) === 'F2 F#2 G2 G#2', names(byId('spider-1234').seq.slice(0, 4)));
check('Spider 1-3-2-4 first string is F G F# G#', names(byId('spider-1324').seq.slice(0, 4)) === 'F2 G2 F#2 G#2', names(byId('spider-1324').seq.slice(0, 4)));
check('Chromatic low E is 25 notes E2..E3..E2', byId('chromatic-low-e').seq.length === 25 && byId('chromatic-low-e').seq[12].m === 52);
check('C major on the A string stays on the A string', byId('c-major-a-string').seq.every(n => n.s === 1));

// ---- catalogue invariants -------------------------------------------------------------
for (const e of EX.CATALOGUE) {
  const s = e.seq;
  const dup = s.some((n, i) => i > 0 && n.m === s[i - 1].m);
  const inRange = s.every(n => n.s >= 0 && n.s <= 5 && n.f >= 0 && n.f <= 15 && n.m === EX.OPEN[n.s] + n.f);
  const palin = s.length % 2 === 1 && s.every((n, i) => n.m === s[s.length - 1 - i].m);
  check(`${e.id}: ${s.length} notes, no consecutive repeats, frets 0-15, up-then-down`, !dup && inRange && palin && s.length >= 7,
    `dup=${dup} inRange=${inRange} palindrome=${palin}`);
}
check('catalogue has warm-ups, scales and arpeggios', ['Warm-up', 'Scale', 'Arpeggio'].every(c => EX.CATALOGUE.some(e => e.cat === c)));
check('ids are unique', new Set(EX.CATALOGUE.map(e => e.id)).size === EX.CATALOGUE.length);

// ---- runner ------------------------------------------------------------------------------
{
  const e = byId('a-minor-pent-box1');
  const r = EX.createRun(e);
  let t = 1000, events = [];
  for (const n of e.seq) { events.push(r.feed(n.m, t).event); t += 500; }
  check('feeding the exact sequence completes it', r.done && events[events.length - 1] === 'done' && events.slice(0, -1).every(x => x === 'advance'), events.join(','));
  const st = r.stats(t);
  check('stats: all correct, none wrong, tempo from first to last note', st.correct === e.seq.length && st.wrong === 0 && Math.abs(st.notesPerMin - 120) < 0.01, JSON.stringify(st));
}
{
  const e = byId('a-minor-pent-box1');
  const r = EX.createRun(e);
  check('first target is the low A', r.target.m === 45);
  check('wrong note is counted and does not advance', r.feed(46, 0).event === 'wrong' && r.index === 0);
  check('right note advances', r.feed(45, 100).event === 'advance' && r.index === 1);
  check('the note just played, heard again, is ignored', r.feed(45, 200).event === 'ignore' && r.index === 1);
  check('octave error is wrong in strict mode', r.feed(48 + 12, 300).event === 'wrong');
  const s = r.stats(400);
  check('accuracy counts wrong notes', s.correct === 1 && s.wrong === 2 && Math.abs(s.accuracy - 1 / 3) < 1e-9, JSON.stringify(s));
}
{
  const r = EX.createRun(byId('a-minor-pent-box1'), { anyOctave: true });
  check('anyOctave accepts the A an octave up', r.feed(57, 0).event === 'advance');
}

console.log(`\n${runs - fails}/${runs} passed`);
process.exit(fails ? 1 : 0);
