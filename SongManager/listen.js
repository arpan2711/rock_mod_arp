// Shared guitar listener for the Song Manager pages: opens the input (the NUX MG-300
// by preference), runs notes-dsp.js in an AudioWorklet, and hands raw readings to the
// page. Listen-only - nothing reaches the speakers except the optional test tone at a
// whisper. Lifted from notes.html; notes.html still carries its own copy, this one is
// for the practice page (and any page after it).
//
//   const L = LISTEN.create({ device: <select>, remember: 'rsm-notes-device',
//                             gate: () => linear, test: <checkbox>, testMidi: () => 40,
//                             onReading: r => ..., flash: (kind, text, ms) => ... });
//   await L.start();  L.stop();  L.switchDevice(id);  L.setGate(lin);  L.testTone();
//
//   const D = LISTEN.debounce({ a4: () => 440, onLevel(db), onNote(midi, cents, hz, changed), onClear() });
//   D.feed(reading)   - two agreeing readings before the note changes; 250 ms hold on silence

const LISTEN = (() => {
  function explain(err) {
    const n = err && err.name;
    if (n === 'NotAllowedError') return 'Microphone access was refused. Allow it for 127.0.0.1 in the browser and try again.';
    if (n === 'NotFoundError') return 'No audio input found. Plug in the MG-300 (USB) and press Start again.';
    if (n === 'NotReadableError') return 'The input is busy — if Rocksmith is running it holds the NUX exclusively (RS_ASIO). Close the game and retry.';
    if (n === 'OverconstrainedError') return 'That input disappeared. Pick another one.';
    return (err && err.message) || String(err);
  }

  function create(o) {
    const L = { ctx: null, stream: null, source: null, worklet: null, osc: null, oscGain: null };
    const flash = o.flash || (() => {});
    const remember = o.remember || 'rsm-notes-device';
    const midiHz = m => 440 * Math.pow(2, (m - 69) / 12);

    async function listDevices() {
      const devs = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'audioinput');
      const sel = o.device, remembered = localStorage.getItem(remember);
      sel.innerHTML = devs.map(d => `<option value="${d.deviceId}">${d.label || 'input ' + d.deviceId.slice(0, 6)}</option>`).join('') || '<option value="">no inputs found</option>';
      const nux = devs.find(d => /nux/i.test(d.label));
      const pick = devs.find(d => d.deviceId === remembered) || nux || devs[0];
      if (pick) sel.value = pick.deviceId;
      if (!nux) flash('warn', 'No NUX input found — is the MG-300 plugged in? Using ' + (pick ? (pick.label || 'the first input') : 'nothing') + ' for now.');
      return pick ? pick.deviceId : null;
    }
    const openDevice = id => navigator.mediaDevices.getUserMedia({ audio: { deviceId: { exact: id }, channelCount: 1,
      echoCancellation: false, noiseSuppression: false, autoGainControl: false } });

    // Resolves to {label, sampleRate, baseLatency} or null (the error has been flashed).
    async function start() {
      try {
        if (!L.stream) {
          // Any input first, to get permission (labels are hidden until then); then the right one.
          L.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
          const id = await listDevices();
          if (id && !(L.stream.getAudioTracks()[0].getSettings().deviceId || '').startsWith(id)) {
            L.stream.getTracks().forEach(t => t.stop());
            L.stream = await openDevice(id);
          }
        }
        L.ctx = new AudioContext({ latencyHint: 'interactive', sampleRate: 48000 });
        await L.ctx.audioWorklet.addModule('/notes-dsp.js');
        L.worklet = new AudioWorkletNode(L.ctx, 'note-processor', {
          numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [1],
          processorOptions: { window: 2048, hop: 512, opts: { gate: o.gate() } },
        });
        L.worklet.port.onmessage = e => o.onReading(e.data);
        const mute = L.ctx.createGain(); mute.gain.value = 0;   // the worklet only runs if it reaches the destination
        L.worklet.connect(mute).connect(L.ctx.destination);
        L.source = L.ctx.createMediaStreamSource(L.stream);
        L.source.connect(L.worklet);
        testTone();
        return { label: L.stream.getAudioTracks()[0].label, sampleRate: L.ctx.sampleRate, baseLatency: L.ctx.baseLatency || 0 };
      } catch (err) {
        flash('stop', explain(err));
        await stop();
        return null;
      }
    }

    function testTone() {
      if (!L.ctx) return;
      const on = o.test && o.test.checked;
      if (on && !L.osc) {
        L.osc = L.ctx.createOscillator(); L.osc.type = 'sawtooth'; L.osc.frequency.value = midiHz(o.testMidi());
        L.oscGain = L.ctx.createGain(); L.oscGain.gain.value = 0.25;
        L.osc.connect(L.oscGain).connect(L.worklet);
        const hear = L.ctx.createGain(); hear.gain.value = 0.05;
        L.oscGain.connect(hear).connect(L.ctx.destination);
        L.osc.start();
        if (L.source) L.source.disconnect();
        flash('warn', 'Test tone on — the input is ignored while this is ticked.', 3000);
      } else if (!on && L.osc) {
        L.osc.stop(); L.osc.disconnect(); L.oscGain.disconnect(); L.osc = L.oscGain = null;
        if (L.source) L.source.connect(L.worklet);
      }
    }
    function setTestMidi(m) { if (L.osc) L.osc.frequency.value = midiHz(m); }
    function setGate(lin) { if (L.worklet) L.worklet.port.postMessage({ opts: { gate: lin } }); }

    async function stop() {
      if (L.osc) { try { L.osc.stop(); } catch (_) {} L.osc = L.oscGain = null; }
      if (L.source) { try { L.source.disconnect(); } catch (_) {} L.source = null; }
      if (L.worklet) { try { L.worklet.disconnect(); } catch (_) {} L.worklet = null; }
      if (L.ctx) { try { await L.ctx.close(); } catch (_) {} L.ctx = null; }
      if (L.stream) { L.stream.getTracks().forEach(t => t.stop()); L.stream = null; }
    }

    // Resolves to the new input's label, or null.
    async function switchDevice(id) {
      localStorage.setItem(remember, id);
      if (!L.ctx) return null;
      try {
        const s = await openDevice(id);
        if (L.source) L.source.disconnect();
        L.stream.getTracks().forEach(t => t.stop());
        L.stream = s; L.source = L.ctx.createMediaStreamSource(L.stream);
        if (!L.osc) L.source.connect(L.worklet);
        return L.stream.getAudioTracks()[0].label;
      } catch (err) { flash('stop', explain(err)); return null; }
    }

    L.start = start; L.stop = stop; L.testTone = testTone; L.setTestMidi = setTestMidi;
    L.setGate = setGate; L.switchDevice = switchDevice; L.active = () => !!L.ctx;
    return L;
  }

  function debounce(o) {
    let readings = [], shown = null, shownSince = 0;
    const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());
    return {
      get shown() { return shown; },
      reset() { shown = null; readings = []; },
      feed(r) {
        const db = r.rms > 0 ? 20 * Math.log10(r.rms) : -120;
        if (o.onLevel) o.onLevel(db);
        if (!r.freq || r.clarity < 0.8) {
          readings = [];
          if (shown !== null && now() - shownSince > 250) { shown = null; if (o.onClear) o.onClear(); }
          return;
        }
        const m = 69 + 12 * Math.log2(r.freq / (o.a4() || 440));
        const rounded = Math.round(m);
        readings.push(rounded); if (readings.length > 3) readings.shift();
        const agree = readings.length >= 2 && readings[readings.length - 1] === readings[readings.length - 2];
        if (rounded !== shown && !agree) return;
        const changed = rounded !== shown;
        shown = rounded; shownSince = now();
        if (o.onNote) o.onNote(rounded, (m - rounded) * 100, r.freq, changed);
      },
    };
  }

  return { create, debounce, explain };
})();

if (typeof window !== 'undefined') window.LISTEN = LISTEN;
if (typeof module !== 'undefined' && module.exports) module.exports = LISTEN;
