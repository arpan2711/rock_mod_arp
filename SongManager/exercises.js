// Exercises for the Guitar Notes page: warm-ups, scales and arpeggios, plus the
// small state machine that runs one against the detected notes.
//
// Every shape is generated from an interval formula inside a fret window on
// standard tuning (E A D G B e), so the fingerings are the standard position
// shapes by construction. The catalogue follows the usual method-book canon:
// Leavitt's "A Modern Method for Guitar" (Berklee) for position playing and the
// chromatic 1-2-3-4, Petrucci's "Rock Discipline" and Stetina's "Speed Mechanics"
// for the spider permutations, the CAGED / pentatonic-box tradition (Edwards'
// "Fretboard Logic", the Hal Leonard method) for the movable shapes, and the
// barre-chord arpeggio shapes every rock method teaches.
//
// Loaded in the browser (plain script -> window.GUITAR_EX) and in node for the
// tests (module.exports).

const GUITAR_EX = (() => {
  const OPEN = [40, 45, 50, 55, 59, 64];          // E2 A2 D3 G3 B3 E4
  const SNAME = ['E', 'A', 'D', 'G', 'B', 'e'];
  const NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  const noteName = m => NAMES[((m % 12) + 12) % 12] + (Math.floor(m / 12) - 1);

  const FORMULAS = {
    major:         [0, 2, 4, 5, 7, 9, 11],
    naturalMinor:  [0, 2, 3, 5, 7, 8, 10],
    harmonicMinor: [0, 2, 3, 5, 7, 8, 11],
    dorian:        [0, 2, 3, 5, 7, 9, 10],
    mixolydian:    [0, 2, 4, 5, 7, 9, 10],
    minorPent:     [0, 3, 5, 7, 10],
    majorPent:     [0, 2, 4, 7, 9],
    blues:         [0, 3, 5, 6, 7, 10],
    majTriad:      [0, 4, 7],
    minTriad:      [0, 3, 7],
    dom7:          [0, 4, 7, 10],
    maj7:          [0, 4, 7, 11],
    min7:          [0, 3, 7, 10],
    dim7:          [0, 3, 6, 9],
  };

  // All scale tones inside [lo, hi] on every string, ascending. One entry per
  // pitch: where the G-B third makes the same pitch reachable on two strings
  // inside the window, the lower string wins (that is how the box shapes go).
  function shape(root, formula, lo, hi) {
    const out = [], seen = new Set();
    for (let s = 0; s < 6; s++) {
      for (let f = lo; f <= hi; f++) {
        const m = OPEN[s] + f;
        if (!formula.includes((((m - root) % 12) + 12) % 12)) continue;
        if (seen.has(m)) continue;
        seen.add(m);
        out.push({ m, s, f });
      }
    }
    return out.sort((a, b) => a.m - b.m || a.s - b.s);
  }

  // Trim a shape to run root -> root two octaves up (the way a method book has
  // you play a position scale), or return the whole box.
  function rootToRoot(notes, root) {
    const start = notes.findIndex(n => n.m === root);
    let end = notes.findIndex(n => n.m === root + 24);
    if (end < 0) end = notes.length - 1;
    return notes.slice(Math.max(0, start), end + 1);
  }

  function upDown(notes) {
    return notes.concat(notes.slice(0, -1).reverse());
  }

  // Chromatic "spider": one finger per fret on frets lo..lo+3, the given finger
  // order on every string going up, the reverse order on every string coming down.
  function spider(order, lo) {
    const up = [], down = [];
    for (let s = 0; s < 6; s++) for (const k of order) up.push({ m: OPEN[s] + lo + k - 1, s, f: lo + k - 1 });
    const rev = order.slice().reverse();
    for (let s = 5; s >= 0; s--) for (const k of rev) down.push({ m: OPEN[s] + lo + k - 1, s, f: lo + k - 1 });
    return up.concat(down.slice(1));
  }

  function singleString(s, formula, root, lo, hi) {
    const out = [];
    for (let f = lo; f <= hi; f++) {
      const m = OPEN[s] + f;
      if (formula.includes((((m - root) % 12) + 12) % 12)) out.push({ m, s, f });
    }
    return upDown(out);
  }

  const R = { E2: 40, G2: 43, A2: 45, C3: 48 };

  function ex(id, cat, name, desc, source, tempo, seq) {
    return { id, cat, name, desc, source, tempo, seq };
  }

  const CATALOGUE = [
    // ---- warm-ups -----------------------------------------------------------------
    ex('spider-1234', 'Warm-up', 'Chromatic spider 1-2-3-4',
       'One finger per fret, frets 1-4, low E to high e and back. Keep every finger down until it is needed again; let the hand stay still and the fingers do the moving. The single most-assigned warm-up there is.',
       'Leavitt, A Modern Method for Guitar; Petrucci, Rock Discipline', 60, spider([1, 2, 3, 4], 1)),
    ex('spider-1324', 'Warm-up', 'Spider permutation 1-3-2-4',
       'Same frets, fingers out of order. The permutations are what build independence; 1-3-2-4 and 1-4-2-3 are the ones that expose a weak third finger.',
       'Stetina, Speed Mechanics for Lead Guitar', 60, spider([1, 3, 2, 4], 1)),
    ex('spider-1423', 'Warm-up', 'Spider permutation 1-4-2-3',
       'The stretch permutation. Slower than it looks. If the fourth finger lags, this is the one to live on.',
       'Stetina, Speed Mechanics for Lead Guitar', 56, spider([1, 4, 2, 3], 1)),
    ex('spider-4321', 'Warm-up', 'Spider descending 4-3-2-1',
       'Fingers land in reverse order on each string. Watch that the first finger does not lift early on the way down.',
       'Petrucci, Rock Discipline', 60, spider([4, 3, 2, 1], 1)),
    ex('chromatic-low-e', 'Warm-up', 'Chromatic run up the low E string',
       'Open to the 12th fret and back on one string, shifting position every four frets. Builds the shift and keeps the picking hand honest.',
       'Leavitt, A Modern Method for Guitar (position shifting)', 72,
       upDown(Array.from({ length: 13 }, (_, f) => ({ m: OPEN[0] + f, s: 0, f })))),

    // ---- scales ---------------------------------------------------------------------
    ex('c-major-open', 'Scale', 'C major, open position',
       'The first scale in every method book: frets 0-3, all six strings, lowest note to highest and back. Learn the note names as you go.',
       'Hal Leonard Guitar Method, book 1', 72, upDown(shape(R.C3, FORMULAS.major, 0, 3))),
    ex('g-major-2oct', 'Scale', 'G major, two octaves (E shape, 2nd position)',
       'Root on the low E at fret 3, root to root and back. The movable major shape: slide it up two frets and it is A major. Fingers 1-2-3-4 to frets 2-3-4-5.',
       'CAGED system (E shape); Leavitt, position 2', 80, upDown(rootToRoot(shape(R.G2, FORMULAS.major, 2, 5), R.G2))),
    ex('a-minor-pent-box1', 'Scale', 'A minor pentatonic, box 1 (5th fret)',
       'The rock and blues foundation. Frets 5 and 7 or 8 on every string; first and third (or fourth) fingers only. Play the whole box, low to high and back.',
       'Pentatonic box system; Hal Leonard, Pentatonic Scales for Guitar', 84, upDown(shape(R.A2, FORMULAS.minorPent, 5, 8))),
    ex('a-blues', 'Scale', 'A blues scale (5th fret)',
       'Box 1 with the flat five added on the A and G strings. Same fingers, one extra note that gives the box its attitude.',
       'Pentatonic box system', 80, upDown(shape(R.A2, FORMULAS.blues, 5, 8))),
    ex('g-major-pent', 'Scale', 'G major pentatonic (2nd position)',
       'The same shape as E minor pentatonic box 1, heard from the G. Country and major-key rock live here.',
       'Pentatonic box system', 84, upDown(shape(R.G2, FORMULAS.majorPent, 2, 5))),
    ex('a-natural-minor', 'Scale', 'A natural minor, two octaves (5th position)',
       'The Aeolian shape with the root under the first finger on the low E. Root to root and back. Relative to C major - same notes, different home.',
       'Segovia, Diatonic Major and Minor Scales; CAGED', 80, upDown(rootToRoot(shape(R.A2, FORMULAS.naturalMinor, 4, 8), R.A2))),
    ex('a-harmonic-minor', 'Scale', 'A harmonic minor, two octaves (5th position)',
       'Natural minor with the seventh raised: the G# on the D string is a fourth-finger stretch, and it comes back on the B string at fret 9. Classical and metal both use this one.',
       'Segovia, Diatonic Major and Minor Scales', 72, upDown(rootToRoot(shape(R.A2, FORMULAS.harmonicMinor, 4, 9), R.A2))),
    ex('a-dorian', 'Scale', 'A Dorian, two octaves (5th position)',
       'Minor with a raised sixth (F#). The minor sound of funk, fusion and most minor-key jam tracks. Root to root and back.',
       'Leavitt, modes in position', 80, upDown(rootToRoot(shape(R.A2, FORMULAS.dorian, 4, 8), R.A2))),
    ex('a-mixolydian', 'Scale', 'A Mixolydian, two octaves (5th position)',
       'Major with a flat seventh (G). The dominant-chord scale; the blues-rock sound over an A7. Root to root and back.',
       'Leavitt, modes in position', 80, upDown(rootToRoot(shape(R.A2, FORMULAS.mixolydian, 4, 8), R.A2))),
    ex('c-major-a-string', 'Scale', 'C major along the A string',
       'One string, frets 3 to 15, up and back. Single-string scales are how you learn where the notes are instead of where the shapes are.',
       'Leavitt; Govan, Creative Guitar 1 (single-string playing)', 72, singleString(1, FORMULAS.major, R.C3, 3, 15)),

    // ---- arpeggios ------------------------------------------------------------------
    ex('a-major-arp', 'Arpeggio', 'A major arpeggio (E-shape barre, 5th fret)',
       'The notes of the A barre chord one at a time, root to root and back. Two octaves plus the E on top. Let each note ring only until the next one.',
       'Barre-chord arpeggios (every rock method)', 72, upDown(shape(R.A2, FORMULAS.majTriad, 4, 7))),
    ex('a-minor-arp', 'Arpeggio', 'A minor arpeggio (Em-shape barre, 5th fret)',
       'Same as the major with the third dropped to C on the G string. Compare the two back to back.',
       'Barre-chord arpeggios', 72, upDown(shape(R.A2, FORMULAS.minTriad, 4, 7))),
    ex('a-dom7-arp', 'Arpeggio', 'A7 arpeggio (5th fret)',
       'Major triad plus the flat seventh, G. Outlines the dominant chord; pairs with the Mixolydian scale above.',
       'Barre-chord arpeggios', 72, upDown(shape(R.A2, FORMULAS.dom7, 4, 8))),
    ex('a-maj7-arp', 'Arpeggio', 'Amaj7 arpeggio (5th fret)',
       'Major triad plus the major seventh, G#. The jazz and neo-soul colour.',
       'Barre-chord arpeggios', 72, upDown(shape(R.A2, FORMULAS.maj7, 4, 8))),
    ex('a-min7-arp', 'Arpeggio', 'Am7 arpeggio (5th fret)',
       'Minor triad plus the flat seventh. The chord every ii-V starts on; pairs with Dorian.',
       'Barre-chord arpeggios', 72, upDown(shape(R.A2, FORMULAS.min7, 4, 8))),
    ex('a-dim7-arp', 'Arpeggio', 'A diminished 7 arpeggio (5th fret)',
       'Stacked minor thirds - the shape repeats every three frets, so once you have this one you have all of them.',
       'Barre-chord arpeggios; classical diminished studies', 66, upDown(shape(R.A2, FORMULAS.dim7, 4, 8))),
  ];

  // ---- running an exercise against detected notes ---------------------------------
  // feed(midi, now) is called once per *stable* note the page detects (on change).
  //   'advance' - matched the current target, moved on
  //   'done'    - that was the last one
  //   'ignore'  - the note just played again (still ringing / re-detected)
  //   'wrong'   - anything else; counted, cursor stays put
  function createRun(exercise, opts) {
    const o = Object.assign({ anyOctave: false }, opts || {});
    const seq = exercise.seq;
    const pc = m => ((m % 12) + 12) % 12;
    let i = 0, correct = 0, wrong = 0, started = 0, finished = 0, last = null;
    const run = {
      seq,
      get index() { return i; },
      get target() { return i < seq.length ? seq[i] : null; },
      get done() { return i >= seq.length; },
      feed(midi, now) {
        if (run.done) return { event: 'done', index: i };
        const t = seq[i].m;
        const match = o.anyOctave ? pc(midi) === pc(t) : midi === t;
        if (match) {
          if (!started) started = now;
          correct++; i++; last = midi;
          if (i >= seq.length) { finished = now; return { event: 'done', index: i }; }
          return { event: 'advance', index: i };
        }
        const prev = i > 0 ? seq[i - 1].m : null;
        if (prev !== null && (o.anyOctave ? pc(midi) === pc(prev) : midi === prev)) return { event: 'ignore', index: i };
        wrong++; last = midi;
        return { event: 'wrong', index: i };
      },
      stats(now) {
        const end = finished || now || started;
        const secs = started ? (end - started) / 1000 : 0;
        return { correct, wrong, total: seq.length, index: i, seconds: secs,
                 notesPerMin: secs > 0 && correct > 1 ? (correct - 1) / secs * 60 : 0,
                 accuracy: correct + wrong ? correct / (correct + wrong) : 1 };
      },
    };
    return run;
  }

  const label = n => SNAME[n.s] + '·' + n.f;

  return { CATALOGUE, FORMULAS, OPEN, SNAME, noteName, label, shape, rootToRoot, upDown, spider, createRun };
})();

if (typeof module !== 'undefined' && module.exports) module.exports = GUITAR_EX;
