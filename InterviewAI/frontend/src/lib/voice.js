/**
 * M10 — Vocal delivery analysis from prosodic features.
 *
 * Analyses the candidate's microphone stream locally with the Web Audio API.
 * No audio is recorded, stored or transmitted; only per-second numeric
 * features leave this module.
 *
 * Features extracted per frame (10 Hz):
 *   RMS energy       loudness of the frame
 *   F0               fundamental frequency by bounded autocorrelation,
 *                    restricted to the human speech range (75-400 Hz)
 *   voiced flag      whether the frame carries speech at all
 *
 * Aggregated per second and then over the session into:
 *   pitch variability   monotone delivery vs expressive delivery
 *   voiced ratio        how much of the time the candidate was speaking
 *   long pause count    hesitation while formulating an answer
 *   vocal confidence    a 0-100 composite, defined in scoreConfidence()
 *
 * This is a prosodic substitute for a wav2vec2 emotion classifier. It runs
 * offline, adds no model download, and every component is inspectable —
 * which matters more for an explainability-focused system than a black-box
 * emotion label would.
 */

// Human speech fundamental frequency bounds, in Hz.
const F0_MIN = 75
const F0_MAX = 400

// A frame quieter than this is treated as silence.
const VOICED_RMS_THRESHOLD = 0.012

// Silence longer than this counts as a hesitation pause.
const LONG_PAUSE_SECONDS = 1.2

const FRAME_HZ = 10
const FFT_SIZE = 2048

const clamp01 = (v) => Math.max(0, Math.min(1, v))
const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0)
const std = (xs) => {
  if (xs.length < 2) return 0
  const m = mean(xs)
  return Math.sqrt(mean(xs.map(x => (x - m) ** 2)))
}

/**
 * Bounded autocorrelation pitch estimate.
 *
 * Only lags corresponding to F0_MIN..F0_MAX are evaluated, which keeps this
 * cheap enough to run at 10 Hz on the main thread — a full O(n^2)
 * autocorrelation would not be.
 */
function estimatePitch(buffer, sampleRate) {
  let sumSquares = 0
  for (let i = 0; i < buffer.length; i++) sumSquares += buffer[i] * buffer[i]
  const rms = Math.sqrt(sumSquares / buffer.length)
  if (rms < VOICED_RMS_THRESHOLD) return { f0: null, rms }

  const minLag = Math.floor(sampleRate / F0_MAX)
  const maxLag = Math.min(Math.floor(sampleRate / F0_MIN), Math.floor(buffer.length / 2))
  if (maxLag <= minLag) return { f0: null, rms }

  let bestLag = -1
  let bestScore = 0
  let prevScore = 0
  let rising = false

  for (let lag = minLag; lag <= maxLag; lag++) {
    let sum = 0
    for (let i = 0; i < buffer.length - lag; i++) sum += buffer[i] * buffer[i + lag]
    const score = sum / (buffer.length - lag)

    // Take the first clear local maximum rather than the global one, which
    // avoids locking onto an octave-below harmonic.
    if (score > prevScore) {
      rising = true
    } else if (rising && score < prevScore && prevScore > bestScore) {
      bestScore = prevScore
      bestLag = lag - 1
      rising = false
    }
    prevScore = score
  }

  if (bestLag < 0 || bestScore <= 0) return { f0: null, rms }

  const f0 = sampleRate / bestLag
  if (f0 < F0_MIN || f0 > F0_MAX) return { f0: null, rms }
  return { f0, rms }
}

/**
 * Start analysing a microphone stream.
 *
 * @param {MediaStream} stream        the candidate's media stream
 * @param {(sample: object) => void} onSample  called once per second
 * @returns {{stop: Function}|null}   null when Web Audio is unavailable
 */
export function createVoiceAnalyzer({ stream, onSample }) {
  const audioTracks = stream?.getAudioTracks?.() || []
  if (!audioTracks.length) return null

  const AudioCtx = window.AudioContext || window.webkitAudioContext
  if (!AudioCtx) return null

  let ctx, analyser, source
  try {
    ctx = new AudioCtx()
    source = ctx.createMediaStreamSource(new MediaStream([audioTracks[0]]))
    analyser = ctx.createAnalyser()
    analyser.fftSize = FFT_SIZE
    analyser.smoothingTimeConstant = 0
    source.connect(analyser)
  } catch (err) {
    console.warn('[voice] analyser unavailable:', err?.message)
    return null
  }

  const buffer = new Float32Array(analyser.fftSize)
  const startedAt = Date.now()

  let framePitches = []
  let frameEnergies = []
  let voicedFrames = 0
  let totalFrames = 0
  let silenceRun = 0
  let longPauses = 0
  let stopped = false

  const frameTimer = setInterval(() => {
    if (stopped) return
    try {
      analyser.getFloatTimeDomainData(buffer)
    } catch {
      return
    }

    const { f0, rms } = estimatePitch(buffer, ctx.sampleRate)
    totalFrames++
    frameEnergies.push(rms)

    if (f0 !== null) {
      framePitches.push(f0)
      voicedFrames++
      if (silenceRun / FRAME_HZ >= LONG_PAUSE_SECONDS) longPauses++
      silenceRun = 0
    } else {
      silenceRun++
    }
  }, 1000 / FRAME_HZ)

  const sampleTimer = setInterval(() => {
    if (stopped || !totalFrames) return

    onSample?.({
      t: Math.floor((Date.now() - startedAt) / 1000),
      f0: framePitches.length ? Number(mean(framePitches).toFixed(1)) : null,
      pitch_sd: framePitches.length > 1 ? Number(std(framePitches).toFixed(1)) : null,
      rms: Number(mean(frameEnergies).toFixed(4)),
      voiced_ratio: Number((voicedFrames / totalFrames).toFixed(3)),
      long_pauses: longPauses,
    })

    framePitches = []
    frameEnergies = []
    voicedFrames = 0
    totalFrames = 0
  }, 1000)

  return {
    stop() {
      stopped = true
      clearInterval(frameTimer)
      clearInterval(sampleTimer)
      try { source.disconnect() } catch { /* already disconnected */ }
      try { ctx.close() } catch { /* already closed */ }
    },
  }
}

/**
 * Composite vocal confidence, 0-100.
 *
 * Four equally weighted components, each scoring 0-1:
 *   projection  loudness sits in a comfortable band; too quiet reads as
 *               tentative, clipping-loud is not better than adequate
 *   fluency     proportion of time actually speaking, targeting the 30-75%
 *               a normal answering turn occupies
 *   expression  pitch variability; both monotone and erratic delivery score
 *               below a naturally varied one
 *   composure   penalty for frequent long hesitation pauses
 */
export function scoreConfidence(summary) {
  if (!summary || !summary.samples) return null

  // Projection: full marks from 0.03 RMS upward, scaling in below that.
  const projection = clamp01(summary.avg_energy / 0.03)

  // Fluency: 30-75% voiced is the healthy band for answering turns.
  const voiced = summary.voiced_ratio
  const fluency = voiced < 0.3 ? clamp01(voiced / 0.3)
    : voiced > 0.75 ? clamp01(1 - (voiced - 0.75) / 0.25)
    : 1

  // Expression: 10-45 Hz of pitch movement reads as natural.
  const sd = summary.pitch_variability ?? 0
  const expression = sd < 10 ? clamp01(sd / 10)
    : sd > 45 ? clamp01(1 - (sd - 45) / 45)
    : 1

  // Composure: more than roughly one long pause a minute starts to cost.
  const pausesPerMin = summary.long_pauses_per_min ?? 0
  const composure = clamp01(1 - pausesPerMin / 4)

  const score = (projection + fluency + expression + composure) / 4 * 100

  const indicators = []
  if (projection < 0.6) indicators.push('Quiet delivery — low vocal projection')
  if (voiced < 0.25) indicators.push('Long silences relative to speaking time')
  if (sd < 10) indicators.push('Monotone delivery')
  if (sd > 45) indicators.push('Unsteady pitch — possible nervousness')
  if (pausesPerMin > 2) indicators.push('Frequent hesitation pauses')

  return {
    vocal_confidence: Number(score.toFixed(1)),
    components: {
      projection: Number(projection.toFixed(2)),
      fluency: Number(fluency.toFixed(2)),
      expression: Number(expression.toFixed(2)),
      composure: Number(composure.toFixed(2)),
    },
    indicators,
  }
}

/** Condense per-second samples into the session summary. */
export function summariseVoice(samples) {
  const valid = (samples || []).filter(s => s && s.rms !== undefined)
  if (!valid.length) return null

  const voicedSamples = valid.filter(s => s.f0 !== null)
  const durationMins = Math.max(valid.length / 60, 1 / 60)
  const longPauses = valid.reduce((max, s) => Math.max(max, s.long_pauses || 0), 0)

  const summary = {
    samples: valid.length,
    avg_pitch_hz: voicedSamples.length ? Number(mean(voicedSamples.map(s => s.f0)).toFixed(1)) : null,
    pitch_variability: voicedSamples.length
      ? Number(mean(voicedSamples.map(s => s.pitch_sd || 0)).toFixed(1)) : null,
    avg_energy: Number(mean(valid.map(s => s.rms)).toFixed(4)),
    voiced_ratio: Number(mean(valid.map(s => s.voiced_ratio)).toFixed(3)),
    long_pauses: longPauses,
    long_pauses_per_min: Number((longPauses / durationMins).toFixed(2)),
  }

  return { ...summary, ...(scoreConfidence(summary) || {}) }
}
