// Tests for the practice planner. Run:  node SongManager\test_practice.js
const PR = require('./practice.js');
const EX = require('./exercises.js');
let fails = 0, runs = 0;
const check = (label, ok, detail) => { runs++; if (!ok) fails++; console.log(`${ok ? ' ok ' : 'FAIL'} ${label}${detail && !ok ? '  -> ' + detail : ''}`); };
const frets = seq => seq.map(n => EX.SNAME[n.s] + n.f).join(' ');
const names = seq => seq.map(n => EX.noteName(n.m)).join(' ');
const MAJ = EX.FORMULAS.major;

// ---- positions ----------------------------------------------------------------------------
{
  const p = PR.positions(0, MAJ);   // C major
  check('C major has the 5 CAGED positions', p.length === 5, p.length);
  check('C major windows: 0-4 2-6 4-8 7-11 9-13 (anchored on E G A C D, the pentatonic tones on the low E)', p.map(x => x.lo + '-' + x.hi).join(' ') === '0-4 2-6 4-8 7-11 9-13', p.map(x => x.lo + '-' + x.hi).join(' '));
  check('anchors of the major scale are its pentatonic (tritone pair F-B dropped)', PR.anchors(MAJ).join() === '0,2,4,7,9', PR.anchors(MAJ).join());
  check('anchors of the natural minor are the minor pentatonic', PR.anchors(EX.FORMULAS.naturalMinor).join() === '0,3,5,7,10');
  check('anchors of the blues scale drop the b5', PR.anchors(EX.FORMULAS.blues).join() === '0,3,5,7,10');
  check('harmonic minor (two tritone pairs) anchors on every tone, thinned to hand positions', PR.anchors(EX.FORMULAS.harmonicMinor).length === 7 && PR.positions(9, EX.FORMULAS.harmonicMinor).every((x, i, a) => i === 0 || x.lo - a[i - 1].lo >= 2));
  check('G major: E shape 2-6, D shape 4-8, C shape 6-10, A shape 9-13, G shape open 0-4', PR.positions(7, MAJ).map(x => x.lo + '-' + x.hi).join(' ') === '0-4 2-6 4-8 6-10 9-13', PR.positions(7, MAJ).map(x => x.lo + '-' + x.hi).join(' '));
  check('relative keys share positions: A minor = C major', PR.positions(9, EX.FORMULAS.naturalMinor).map(x => x.lo).join() === PR.positions(0, MAJ).map(x => x.lo).join());
  check('position 2 (frets 2-6) runs G2 up to A4 with no scale tone skipped',
    names(p[1].notes) === 'G2 A2 B2 C3 D3 E3 F3 G3 A3 B3 C4 D4 E4 F4 G4 A4', names(p[1].notes));
  check('position 2 fingering', frets(p[1].notes) === 'E3 E5 A2 A3 A5 D2 D3 D5 G2 G4 G5 B3 B5 B6 e3 e5', frets(p[1].notes));
  const gapFree = p.every(x => x.notes.every((n, i) => i === 0 || (n.m - x.notes[i - 1].m) <= 2));
  check('every position has consecutive scale tones (no gap wider than a tone)', gapFree);
  check('positions never leave the 15-fret board', p.every(x => x.notes.every(n => n.f >= x.lo && n.f <= x.hi && n.f <= 15)));
}
{
  const p = PR.positions(7, EX.FORMULAS.minorPent);   // G minor pentatonic
  check('G minor pentatonic has 5 positions (boxes)', p.length === 5, p.length);
  check('G minor pentatonic boxes: 0-4 (from F) 2-6 (from G) 5-9 7-11 9-13', p.map(x => x.lo + '-' + x.hi).join(' ') === '0-4 2-6 5-9 7-11 9-13', p.map(x => x.lo + '-' + x.hi).join(' '));
}

// ---- neck layer -----------------------------------------------------------------------------
{
  const n = PR.neck(0, MAJ);
  check('C major on the whole neck: 59 positions in frets 0-15 (brute-force count)', n.length === 59, n.length);
  check('neck notes are all in the scale', n.every(x => MAJ.includes(((x.m % 12) + 12) % 12)));
  check('neck is per string, not deduped by pitch (E3 appears on E12 and D2 and A7)', n.filter(x => x.m === 52).length === 3);
}

// ---- plan -------------------------------------------------------------------------------------
{
  const p = PR.plan({ key: 0, scale: 'major', reps: 10 });
  check('all positions by default: 5 chosen', p.chosen.join() === '0,1,2,3,4', p.chosen.join());
  check('10 reps x 5 positions = 50 segments', p.segments.length === 50, p.segments.length);
  check('segments tile the sequence exactly', p.segments.every((s, i) => s.start === (i ? p.segments[i - 1].end : 0)) && p.segments[49].end === p.seq.length);
  check('no two consecutive notes share a pitch (the detector reports on change only)', p.seq.every((n, i) => i === 0 || n.m !== p.seq[i - 1].m));
  check('first segment goes up and back down position 1', names(p.seq.slice(p.segments[0].start, p.segments[0].end)).startsWith('E2 F2 G2 A2 B2 C3') && p.seq[p.segments[0].end - 1].m < p.seq[p.segments[0].end - 2].m);
  check('rep numbers run 1..10 in order', p.segments.map(s => s.rep).join() === Array.from({ length: 50 }, (_, i) => Math.floor(i / 5) + 1).join());
  check('where() maps an index to its rep and position', PR.where(p, p.segments[8].start + 2).rep === 2 && PR.where(p, p.segments[8].start + 2).pos === 3);
  check('where() past the end gives the last segment', PR.where(p, p.seq.length) === p.segments[49]);
}
{
  const one = PR.plan({ key: 7, scale: 'major', positions: [1], reps: 3 });
  const seg = one.segments;
  check('one position x 3: three segments', seg.length === 3 && seg.every(s => s.pos === 1));
  const boundary = one.seq[seg[1].start], prev = one.seq[seg[0].end - 1];
  check('at a rep boundary the repeated low note is dropped, so the loop stays continuous', boundary.m !== prev.m && one.seq[seg[0].start].m === prev.m);
  check('the run still ends on the low note', one.seq[one.seq.length - 1].m === one.seq[0].m);
}
check('positions given out of order or duplicated are normalised', PR.plan({ key: 0, scale: 'major', positions: [3, 1, 3], reps: 1 }).chosen.join() === '1,3');
check('reps are clamped to 1..200', PR.plan({ key: 0, scale: 'major', reps: 0 }).reps === 1 && PR.plan({ key: 0, scale: 'major', reps: 999 }).reps === 200);
check('unknown scale throws', (() => { try { PR.plan({ key: 0, scale: 'nope', reps: 1 }); return false; } catch (e) { return true; } })());
check('every key x scale builds a plan with 4-6 positions covering the neck', PR.KEYS.every(k => PR.SCALES.every(s => { const p = PR.plan({ key: k.pc, scale: s.id, reps: 1 }).positions; return p.length >= 4 && p.length <= 6 && p[0].lo <= 1 && p[p.length - 1].hi >= 11; })));   // the shape at fret 12 repeats the open one

console.log(`\n${runs - fails}/${runs} passed`);
process.exit(fails ? 1 : 0);
