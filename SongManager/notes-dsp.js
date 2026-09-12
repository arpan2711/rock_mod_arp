// Guitar pitch detection for the Song Manager "Guitar Notes" page.
//
// Loaded two ways: as an AudioWorklet module in the browser (registerProcessor is
// defined) and as a plain module in node for the tests (module.exports). The
// detector itself is a pure function so both paths run identical code.
//
// McLeod Pitch Method: normalised square difference function (NSDF) + peak
// picking. The lag range is limited to the guitar's pitch range so the O(N*tau)
// autocorrelation stays cheap enough for the realtime audio thread.

const NOTE_DSP = (() => {
  const DEFAULTS = {
    fmin: 55,        // A1 - covers drop tunings on a 7-string; below this the window is too short
    fmax: 1500,      // above the 24th fret on the high E
    gate: 0.004,     // RMS below this is silence (about -48 dBFS)
    k: 0.9,          // MPM: take the first peak at least this fraction of the tallest one
    minClarity: 0.8, // below this the estimate is reported but flagged unreliable
  };

  // buf: Float32Array window, sr: sample rate. Returns {freq, clarity, rms}.
  // freq is 0 when nothing periodic was found.
  function analyse(buf, sr, opts) {
    const o = Object.assign({}, DEFAULTS, opts || {});
    const n = buf.length;

    // Prefix sums of x^2 give both energy terms of the NSDF denominator in O(1).
    const P = new Float64Array(n + 1);
    let acc = 0;
    for (let i = 0; i < n; i++) { acc += buf[i] * buf[i]; P[i + 1] = acc; }
    const rms = Math.sqrt(acc / n);
    if (rms < o.gate) return { freq: 0, clarity: 0, rms };

    const tauMin = Math.max(2, Math.floor(sr / o.fmax));
    const tauMax = Math.min(n - 2, Math.ceil(sr / o.fmin));
    const nsdf = new Float32Array(tauMax + 1);
    for (let tau = 1; tau <= tauMax; tau++) {
      let ac = 0;
      const lim = n - tau;
      for (let i = 0; i < lim; i++) ac += buf[i] * buf[i + tau];
      const m = P[lim] + (P[n] - P[tau]);
      nsdf[tau] = m > 0 ? (2 * ac) / m : 0;
    }

    // Peak picking, per McLeod: ignore everything until the NSDF has first gone
    // negative (that is the main lobe), then record the maximum inside each
    // positive region.
    const peaks = [];
    let tau = 1;
    while (tau <= tauMax && nsdf[tau] > 0) tau++;      // leave the main lobe
    while (tau <= tauMax) {
      while (tau <= tauMax && nsdf[tau] <= 0) tau++;   // find the next positive region
      let best = -1, bestTau = -1;
      while (tau <= tauMax && nsdf[tau] > 0) {
        if (nsdf[tau] > best) { best = nsdf[tau]; bestTau = tau; }
        tau++;
      }
      if (bestTau >= tauMin && bestTau < tauMax) peaks.push([bestTau, best]);
    }
    if (!peaks.length) return { freq: 0, clarity: 0, rms };

    let tallest = 0;
    for (const [, v] of peaks) if (v > tallest) tallest = v;
    let pick = peaks[0];
    for (const p of peaks) { if (p[1] >= o.k * tallest) { pick = p; break; } }

    // Parabolic interpolation around the chosen peak for sub-sample precision.
    const t = pick[0];
    const a = nsdf[t - 1], b = nsdf[t], c = nsdf[t + 1];
    const denom = a - 2 * b + c;
    const shift = denom !== 0 ? 0.5 * (a - c) / denom : 0;
    const tauI = t + Math.max(-1, Math.min(1, shift));
    const clarity = Math.max(0, Math.min(1, b - 0.25 * (a - c) * shift));

    return { freq: sr / tauI, clarity, rms };
  }

  function midi(freq, a4) { return 69 + 12 * Math.log2(freq / (a4 || 440)); }

  return { analyse, midi, DEFAULTS };
})();

// ---- AudioWorklet side ------------------------------------------------------------
if (typeof registerProcessor === 'function') {
  class NoteProcessor extends AudioWorkletProcessor {
    constructor(options) {
      super();
      const p = (options && options.processorOptions) || {};
      this.win = p.window || 2048;
      this.hop = p.hop || 512;
      this.opts = p.opts || {};
      this.ring = new Float32Array(this.win);
      this.pos = 0;         // next write index in the ring
      this.filled = 0;      // samples written so far (saturates at win)
      this.since = 0;       // samples since the last analysis
      this.scratch = new Float32Array(this.win);
      this.port.onmessage = e => { if (e.data && e.data.opts) this.opts = Object.assign({}, this.opts, e.data.opts); };
    }
    process(inputs) {
      const ch = inputs[0] && inputs[0][0];
      if (!ch) return true;
      for (let i = 0; i < ch.length; i++) {
        this.ring[this.pos] = ch[i];
        this.pos = (this.pos + 1) % this.win;
      }
      this.filled = Math.min(this.win, this.filled + ch.length);
      this.since += ch.length;
      if (this.filled === this.win && this.since >= this.hop) {
        this.since = 0;
        // Unroll the ring into time order.
        const head = this.ring.subarray(this.pos), tail = this.ring.subarray(0, this.pos);
        this.scratch.set(head, 0); this.scratch.set(tail, head.length);
        const r = NOTE_DSP.analyse(this.scratch, sampleRate, this.opts);
        this.port.postMessage(r);
      }
      return true;
    }
  }
  registerProcessor('note-processor', NoteProcessor);
}

// ---- node side (tests) ------------------------------------------------------------
if (typeof module !== 'undefined' && module.exports) module.exports = NOTE_DSP;
