// Tests for the fretboard diagram. Run:  node SongManager\test_fretboard.js
const FB = require('./fretboard.js');
const EX = require('./exercises.js');
let fails = 0, runs = 0;
const check = (label, ok, detail) => { runs++; if (!ok) fails++; console.log(`${ok ? ' ok ' : 'FAIL'} ${label}${detail && !ok ? '  -> ' + detail : ''}`); };
const byId = id => EX.CATALOGUE.find(e => e.id === id);
const count = (s, re) => (s.match(re) || []).length;

// ---- geometry of the board itself -----------------------------------------------------
{
  const s = FB.svg([]);
  check('6 strings, 15 frets plus a nut', count(s, /class="fb-string"/g) === 6 && count(s, /class="fb-fret"/g) === 15 && count(s, /class="fb-nut"/g) === 1);
  check('string names read e B G D A E top to bottom',
    [...s.matchAll(/class="fb-sname" x="16" y="([\d.]+)"[^>]*>(\w)</g)].sort((a, b) => a[1] - b[1]).map(m => m[2]).join('') === 'eBGDAE');
  check('fret numbers 1..15 underneath', [...s.matchAll(/class="fb-num"[^>]*>(\d+)</g)].map(m => m[1]).join(' ') === '1 2 3 4 5 6 7 8 9 10 11 12 13 14 15');
  check('inlays at 3 5 7 9 15 and a double at 12', count(s, /class="fb-inlay"/g) === 7);
  check('no notes drawn for an empty sequence', count(s, /class="fb-n /g) === 0);
}

// ---- notes ------------------------------------------------------------------------------
{
  const e = byId('a-minor-pent-box1');
  const s = FB.svg(e.seq, { root: 9 });
  const uniq = new Set(e.seq.map(n => n.s + ':' + n.f)).size;
  check('one circle per distinct position (box 1 = 12)', count(s, /class="fb-n /g) === uniq && uniq === 12, count(s, /class="fb-n /g));
  check('before a run every note is todo', count(s, /class="fb-n todo/g) === 12 && !s.includes('fb-n now') && !s.includes('fb-n done'));
  check('the three A positions are marked root', count(s, /class="fb-n todo root"/g) === 3);
  check('labels are note names without octave', s.includes('>A<') && s.includes('>C<') && !s.includes('>A2<'));
  check('E5 is the low string at fret 5', /data-pos="E5"/.test(s));
}
{
  const e = byId('a-major-arp');
  const s = FB.svg(e.seq, { root: e.seq[0].m % 12 });
  check('A major arpeggio shows C# and E', s.includes('>C#<') && s.includes('>E<'));
  // C# on the A string fret 4: x = 72 + 3.5 * fret width, y = row of the A string (second from bottom)
  const fw = (1000 - 72 - 8) / 15;
  const m = s.match(/<g class="fb-n todo" data-pos="A4"><circle cx="([\d.]+)" cy="([\d.]+)"/);
  check('A4 is drawn in the middle of fret 4 on the A string row', m && Math.abs(m[1] - (72 + 3.5 * fw)) < 1e-6 && Number(m[2]) === FB.TOP + 4 * FB.GAP, m && m.slice(1).join(','));
}
{
  const e = byId('c-major-open');
  const s = FB.svg(e.seq, { root: 0 });
  check('open strings sit left of the nut', /data-pos="E0"><circle cx="46"/.test(s));
  check('C major open has 17 positions and 2 roots (A3, B1)', count(s, /class="fb-n /g) === 17 && count(s, / root"/g) === 2, count(s, / root"/g));
}

// ---- run states ---------------------------------------------------------------------------
{
  const e = byId('a-minor-pent-box1');       // 23 notes: 12 up, 11 down
  let s = FB.svg(e.seq, { index: 0, root: 9 });
  check('at index 0 the low A is now and pulses', /class="fb-n now root" data-pos="E5"><circle class="fb-pulse"/.test(s) && count(s, /fb-n now/g) === 1);
  s = FB.svg(e.seq, { index: 3, root: 9 });
  check('at index 3: E5 E8 A5 still to come on the way down, so none are done yet', count(s, /fb-n done/g) === 0 && /fb-n now" data-pos="A7"/.test(s));
  s = FB.svg(e.seq, { index: 12, root: 9 });   // first note of the descent = e5 (index 12)
  check('on the way down, the top e8 is done and e5 is now', /fb-n done" data-pos="e8"/.test(s) && /fb-n now root" data-pos="e5"/.test(s));
  s = FB.svg(e.seq, { index: e.seq.length, root: 9 });
  check('past the end everything is done', count(s, /fb-n done/g) === 12 && !s.includes('fb-n now') && !s.includes('fb-n todo'));
}
{
  const st = FB.states([{ s: 0, f: 5, m: 45 }, { s: 0, f: 8, m: 48 }, { s: 0, f: 5, m: 45 }], 1);
  check('states(): repeated position keeps one entry', st.length === 2 && st.find(x => x.f === 5).state === 'todo' && st.find(x => x.f === 8).state === 'now');
}
{
  const seq = [{ s: 0, f: 5, m: 45 }, { s: 0, f: 7, m: 47 }];
  const ghost = [{ s: 0, f: 5, m: 45 }, { s: 1, f: 2, m: 47 }, { s: 5, f: 5, m: 69 }];
  const s = FB.svg(seq, { ghost, root: 9 });
  check('ghost notes draw faint, skipping positions the sequence already uses', count(s, /fb-n ghost/g) === 2 && /fb-n ghost root" data-pos="e5"/.test(s) && count(s, /class="fb-n /g) === 4, count(s, /fb-n ghost/g));
}
check('every catalogue exercise renders with one circle per position', EX.CATALOGUE.every(e =>
  count(FB.svg(e.seq), /class="fb-n /g) === new Set(e.seq.map(n => n.s + ':' + n.f)).size));
check('svg is well formed enough: tags balance', EX.CATALOGUE.every(e => { const s = FB.svg(e.seq); return count(s, /<g /g) === count(s, /<\/g>/g) && count(s, /<svg/g) === 1 && count(s, /<\/svg>/g) === 1; }));

console.log(`\n${runs - fails}/${runs} passed`);
process.exit(fails ? 1 : 0);
