// Practice-suite planner: a scale in a key, laid out in positions across the neck,
// and a note sequence that runs the chosen positions N times.
//
// Loaded in the browser (plain script -> window.PRACTICE, needs exercises.js first)
// and in node for the tests (module.exports).

const PRACTICE = (() => {
  const EX = typeof GUITAR_EX !== 'undefined' ? GUITAR_EX : require('./exercises.js');
  const NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  const KEYS = NAMES.map((name, pc) => ({ pc, name }));
  const SCALES = [
    { id: 'major',         name: 'Major (Ionian)' },
    { id: 'naturalMinor',  name: 'Natural minor (Aeolian)' },
    { id: 'harmonicMinor', name: 'Harmonic minor' },
    { id: 'dorian',        name: 'Dorian' },
    { id: 'mixolydian',    name: 'Mixolydian' },
    { id: 'majorPent',     name: 'Major pentatonic' },
    { id: 'minorPent',     name: 'Minor pentatonic' },
    { id: 'blues',         name: 'Blues' },
  ];
  const MAXF = 15;
  const pc = m => ((m % 12) + 12) % 12;
  const inScale = (m, rootPc, formula) => formula.includes(pc(m - rootPc));

  // Every scale tone on every string, frets 0..maxFret: the "rest of the neck" layer.
  function neck(rootPc, formula, maxFret = MAXF) {
    const out = [];
    for (let s = 0; s < 6; s++) for (let f = 0; f <= maxFret; f++) {
      const m = EX.OPEN[s] + f;
      if (inScale(m, rootPc, formula)) out.push({ m, s, f });
    }
    return out;
  }

  // Which scale tones anchor a position. The five CAGED positions of a diatonic scale
  // sit where its *pentatonic* tones fall on the low E string - the seven-note scale
  // minus its tritone pair (F and B in C major). A pentatonic or blues scale anchors on
  // its own tones; anything else (harmonic minor) on every tone, thinned below.
  function anchors(formula) {
    if (formula.length === 7) {
      const pairs = [];
      for (let i = 0; i < 7; i++) for (let j = i + 1; j < 7; j++) if (formula[j] - formula[i] === 6) pairs.push([i, j]);
      if (pairs.length === 1) return formula.filter((_, k) => !pairs[0].includes(k));
    }
    if (formula.length === 6 && formula.includes(6)) return formula.filter(x => x !== 6);   // blues: the b5 is a passing tone
    return formula.slice();
  }

  // Positions: one per anchor tone on the low E string in the first octave, as a
  // five-fret window starting one fret below it (first finger a fret behind, the way
  // Leavitt's position system and the CAGED boxes lay the scale out). Five frets, not
  // four, so no scale tone falls in the gap between strings; a pitch reachable on two
  // strings goes to the lower one, as in the box shapes. Windows a single fret apart
  // are the same hand position, so the later one is dropped.
  function positions(rootPc, formula) {
    const anc = anchors(formula), out = [];
    let lastLo = -9;
    for (let f = 0; f <= 11; f++) {
      if (!anc.includes(pc(EX.OPEN[0] + f - rootPc))) continue;
      const lo = Math.max(0, f - 1), hi = lo + 4;
      if (lo - lastLo < 2 || hi > MAXF) continue;
      lastLo = lo;
      const notes = EX.shape(rootPc + 48, formula, lo, hi);   // shape() only uses the root's pitch class
      out.push({ index: out.length, lo, hi, label: `frets ${lo}–${hi}`, notes });
    }
    return out;
  }

  // plan({key, scale, positions, reps}) -> the whole session as one sequence.
  //   key:       pitch class 0..11        scale: id from SCALES
  //   positions: array of position indexes (empty / missing = all)
  //   reps:      how many times to go through the chosen positions
  // Each position is played up and back down; where one segment ends on the same pitch
  // the next begins with, the repeat is dropped, so the run is continuous (the way you
  // would actually loop it) and the detector, which reports notes on change, can follow.
  function plan(o) {
    const formula = EX.FORMULAS[o.scale];
    if (!formula) throw new Error('unknown scale ' + o.scale);
    const rootPc = pc(o.key);
    const reps = Math.max(1, Math.min(200, Math.round(o.reps || 1)));
    const pos = positions(rootPc, formula);
    const want = (o.positions && o.positions.length ? o.positions : pos.map(p => p.index))
      .filter(i => pos[i]).sort((a, b) => a - b);
    const chosen = [...new Set(want)];
    const seq = [], segments = [];
    for (let rep = 1; rep <= reps; rep++) {
      for (const pi of chosen) {
        const start = seq.length;
        for (const n of EX.upDown(pos[pi].notes)) {
          const last = seq[seq.length - 1];
          if (last && last.m === n.m) continue;
          seq.push(n);
        }
        segments.push({ rep, pos: pi, start, end: seq.length });
      }
    }
    return { rootPc, scale: o.scale, formula, reps, positions: pos, chosen, seq, segments };
  }

  // The segment (rep + position) a sequence index falls in; the last one once finished.
  function where(p, index) {
    return p.segments.find(s => index >= s.start && index < s.end) || p.segments[p.segments.length - 1];
  }

  return { KEYS, SCALES, MAXF, neck, anchors, positions, plan, where, noteName: EX.noteName, label: EX.label };
})();

if (typeof window !== 'undefined') window.PRACTICE = PRACTICE;
if (typeof module !== 'undefined' && module.exports) module.exports = PRACTICE;
