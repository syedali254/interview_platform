/**
 * M7 + M8 — Attention and posture analysis with MediaPipe Tasks Vision.
 *
 * Runs entirely in the browser against the candidate's own camera feed; no
 * video ever leaves the machine, only the derived numeric signals do.
 *
 * M7 Attention — derived from face landmark geometry rather than the raw
 * transformation matrix, because the geometric ratios are stable across
 * cameras and are straightforward to justify in writing:
 *   yaw proxy   = horizontal offset of the nose from the eye midpoint,
 *                 divided by inter-eye distance
 *   pitch proxy = vertical offset of the nose from the eye line,
 *                 divided by inter-eye distance
 * Both are calibrated against a baseline captured while the candidate is
 * settling in and looking at the screen, so the score measures deviation
 * from *their* neutral pose rather than from an assumed ideal.
 *
 * M8 Posture — from pose landmarks:
 *   shoulder tilt = vertical difference between shoulders / shoulder width
 *   slouch        = head height above the shoulder line / shoulder width
 *   lean          = horizontal offset of the head from the shoulder midpoint
 *
 * Everything degrades to null if the model assets are unavailable, so an
 * interview never fails because vision analysis could not start.
 */

// Face landmark indices (MediaPipe FaceMesh topology)
const NOSE_TIP = 1
const LEFT_EYE_OUTER = 33
const RIGHT_EYE_OUTER = 263

// Pose landmark indices (BlazePose topology)
const POSE_NOSE = 0
const POSE_LEFT_SHOULDER = 11
const POSE_RIGHT_SHOULDER = 12

// Deviation at which a signal is considered fully degraded.
const YAW_TOLERANCE = 0.42
const PITCH_TOLERANCE = 0.38
const TILT_TOLERANCE = 0.22
const SLOUCH_TOLERANCE = 0.35
const LEAN_TOLERANCE = 0.30

// Samples averaged to establish the candidate's neutral pose.
const CALIBRATION_SAMPLES = 6

// Consecutive away-samples before it counts as a genuine distraction.
const AWAY_STREAK_FOR_EVENT = 4

// Detection runs faster than analysis so the on-screen overlay tracks the
// candidate smoothly; only every Nth detection is folded into a sample.
const DETECT_INTERVAL_MS = 200
const TICKS_PER_SAMPLE = 5

/** Upper-body skeleton, as index pairs into the pose landmark array. */
export const POSE_CONNECTIONS = [
  [11, 12],           // shoulders
  [11, 13], [13, 15], // left arm
  [12, 14], [14, 16], // right arm
  [11, 23], [12, 24], // torso sides
  [23, 24],           // hips
]

/** Outer face oval, for drawing a clean contour rather than 478 dots. */
export const FACE_OVAL = [
  10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365,
  379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93,
  234, 127, 162, 21, 54, 103, 67, 109,
]

/** Eye and iris landmark groups, used to show what gaze tracking sees. */
export const LEFT_EYE = [33, 160, 158, 133, 153, 144]
export const RIGHT_EYE = [362, 385, 387, 263, 373, 380]

const clamp01 = (v) => Math.max(0, Math.min(1, v))
const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0)

/**
 * Create the analyser. Resolves to null when MediaPipe cannot be initialised
 * (assets missing, WebGL unavailable, older browser).
 *
 * @param {HTMLVideoElement} video   live camera element
 * @param {(sample: object) => void} onSample  called ~once per second
 * @param {(event: object) => void}  onEvent   called on notable events
 * @param {(frame: object) => void}  onFrame   raw landmarks, ~5 times a
 *   second, for drawing the overlay. Never store these — they are large.
 */
export async function createVisionAnalyzer({ video, onSample, onEvent, onFrame }) {
  let FilesetResolver, FaceLandmarker, PoseLandmarker
  try {
    ({ FilesetResolver, FaceLandmarker, PoseLandmarker } = await import('@mediapipe/tasks-vision'))
  } catch (err) {
    console.warn('[vision] tasks-vision unavailable:', err?.message)
    return null
  }

  let fileset, faceLandmarker, poseLandmarker
  try {
    fileset = await FilesetResolver.forVisionTasks('/mediapipe/wasm')
  } catch (err) {
    console.warn('[vision] WASM runtime failed to load:', err?.message)
    return null
  }

  // GPU is much faster but is not available everywhere; fall back silently.
  const build = async (Task, modelAssetPath, extra) => {
    for (const delegate of ['GPU', 'CPU']) {
      try {
        return await Task.createFromOptions(fileset, {
          baseOptions: { modelAssetPath, delegate },
          runningMode: 'VIDEO',
          ...extra,
        })
      } catch (err) {
        if (delegate === 'CPU') {
          console.warn(`[vision] ${modelAssetPath} failed to load:`, err?.message)
          return null
        }
      }
    }
    return null
  }

  faceLandmarker = await build(FaceLandmarker, '/mediapipe/models/face_landmarker.task', {
    numFaces: 2,
    outputFaceBlendshapes: true,
  })
  poseLandmarker = await build(PoseLandmarker, '/mediapipe/models/pose_landmarker_lite.task', {
    numPoses: 1,
  })

  if (!faceLandmarker && !poseLandmarker) return null

  const startedAt = Date.now()
  const calibration = { yaw: [], pitch: [], slouch: [], ready: false, yaw0: 0, pitch0: 0, slouch0: 0 }
  let blinkCount = 0
  let wasBlinking = false
  let awayStreak = 0
  let noFaceStreak = 0
  let multiFaceReported = false
  let timer = null
  let stopped = false

  const elapsed = () => Math.floor((Date.now() - startedAt) / 1000)

  const analyseFace = (nowMs) => {
    if (!faceLandmarker) return null
    let result
    try {
      result = faceLandmarker.detectForVideo(video, nowMs)
    } catch {
      return null
    }

    const faces = result?.faceLandmarks?.length || 0
    if (!faces) return { faces: 0 }

    const lm = result.faceLandmarks[0]
    const nose = lm[NOSE_TIP]
    const eyeL = lm[LEFT_EYE_OUTER]
    const eyeR = lm[RIGHT_EYE_OUTER]
    if (!nose || !eyeL || !eyeR) return { faces }

    const eyeMidX = (eyeL.x + eyeR.x) / 2
    const eyeMidY = (eyeL.y + eyeR.y) / 2
    const eyeDist = Math.hypot(eyeR.x - eyeL.x, eyeR.y - eyeL.y) || 1e-6

    const yaw = (nose.x - eyeMidX) / eyeDist
    const pitch = (nose.y - eyeMidY) / eyeDist

    // Blink detection from blendshapes.
    const shapes = result.faceBlendshapes?.[0]?.categories || []
    const blinkScore = Math.max(
      shapes.find(c => c.categoryName === 'eyeBlinkLeft')?.score || 0,
      shapes.find(c => c.categoryName === 'eyeBlinkRight')?.score || 0,
    )
    const blinking = blinkScore > 0.5
    if (blinking && !wasBlinking) blinkCount++
    wasBlinking = blinking

    return { faces, yaw, pitch, blinkScore, landmarks: lm }
  }

  const analysePose = (nowMs) => {
    if (!poseLandmarker) return null
    let result
    try {
      result = poseLandmarker.detectForVideo(video, nowMs)
    } catch {
      return null
    }

    const lm = result?.landmarks?.[0]
    if (!lm) return null

    const nose = lm[POSE_NOSE]
    const shoulderL = lm[POSE_LEFT_SHOULDER]
    const shoulderR = lm[POSE_RIGHT_SHOULDER]
    if (!nose || !shoulderL || !shoulderR) return null

    const shoulderWidth = Math.hypot(shoulderR.x - shoulderL.x, shoulderR.y - shoulderL.y) || 1e-6
    const shoulderMidX = (shoulderL.x + shoulderR.x) / 2
    const shoulderMidY = (shoulderL.y + shoulderR.y) / 2

    return {
      tilt: Math.abs(shoulderL.y - shoulderR.y) / shoulderWidth,
      slouch: (shoulderMidY - nose.y) / shoulderWidth,
      lean: Math.abs(nose.x - shoulderMidX) / shoulderWidth,
      landmarks: lm,
    }
  }

  // Values accumulated between sample emissions.
  let tickCount = 0
  let bufAttention = []
  let bufPosture = []
  let bufAway = 0
  let bufFlags = {}
  let bufFaces = 0

  const emitSample = (extra = {}) => {
    const minutes = Math.max(elapsed() / 60, 1 / 60)
    const flags = Object.entries(bufFlags)
      .filter(([, n]) => n > bufAttention.length / 2)
      .map(([flag]) => flag)

    onSample?.({
      t: elapsed(),
      attention: bufAttention.length ? Number(mean(bufAttention).toFixed(3)) : null,
      posture: bufPosture.length ? Number(mean(bufPosture).toFixed(3)) : null,
      lookingAway: bufAway > bufAttention.length / 2,
      postureFlags: flags,
      faces: bufFaces,
      blinkRate: Number((blinkCount / minutes).toFixed(1)),
      ...extra,
    })
    bufAttention = []
    bufPosture = []
    bufAway = 0
    bufFlags = {}
  }

  const tick = () => {
    if (stopped || video.readyState < 2 || !video.videoWidth) return
    const nowMs = performance.now()
    tickCount++
    const dueForSample = tickCount % TICKS_PER_SAMPLE === 0

    const face = analyseFace(nowMs)
    const pose = analysePose(nowMs)

    // ── No face / multiple faces ─────────────────────────────────────────
    if (!face || face.faces === 0) {
      noFaceStreak++
      if (noFaceStreak === 8 * TICKS_PER_SAMPLE) {
        onEvent?.({ type: 'no_face', detail: 'Candidate left the camera view' })
      }
      onFrame?.({ face: null, pose: null, faces: 0, attention: 0, posture: null })
      if (dueForSample) {
        onSample?.({ t: elapsed(), attention: 0, posture: null, faces: 0, lookingAway: true })
      }
      return
    }
    noFaceStreak = 0
    bufFaces = face.faces

    if (face.faces > 1 && !multiFaceReported) {
      multiFaceReported = true
      onEvent?.({ type: 'multi_face', detail: `${face.faces} faces visible in frame` })
    }

    // ── Calibrate against the candidate's own neutral pose ────────────────
    if (!calibration.ready) {
      if (face.yaw !== undefined) {
        calibration.yaw.push(face.yaw)
        calibration.pitch.push(face.pitch)
      }
      if (pose) calibration.slouch.push(pose.slouch)

      if (calibration.yaw.length >= CALIBRATION_SAMPLES * TICKS_PER_SAMPLE) {
        calibration.yaw0 = mean(calibration.yaw)
        calibration.pitch0 = mean(calibration.pitch)
        calibration.slouch0 = calibration.slouch.length ? mean(calibration.slouch) : 0
        calibration.ready = true
      }
      onFrame?.({
        face: face.landmarks, pose: pose?.landmarks || null,
        faces: face.faces, attention: null, posture: null, calibrating: true,
      })
      if (dueForSample) {
        onSample?.({ t: elapsed(), attention: null, posture: null,
                     faces: face.faces, calibrating: true })
      }
      return
    }

    // ── M7 attention ─────────────────────────────────────────────────────
    const yawDev = Math.abs(face.yaw - calibration.yaw0) / YAW_TOLERANCE
    const pitchDev = Math.abs(face.pitch - calibration.pitch0) / PITCH_TOLERANCE
    const attention = clamp01(1 - (yawDev + pitchDev) / 2)
    const lookingAway = attention < 0.45

    bufAttention.push(attention)
    if (lookingAway) bufAway++

    if (lookingAway) {
      awayStreak++
      if (awayStreak === AWAY_STREAK_FOR_EVENT * TICKS_PER_SAMPLE) {
        onEvent?.({ type: 'looking_away', detail: 'Sustained gaze away from the screen' })
      }
    } else {
      awayStreak = 0
    }

    // ── M8 posture ───────────────────────────────────────────────────────
    let posture = null
    const postureFlags = []
    if (pose) {
      const tiltDev = pose.tilt / TILT_TOLERANCE
      const slouchDev = Math.max(0, calibration.slouch0 - pose.slouch) / SLOUCH_TOLERANCE
      const leanDev = pose.lean / LEAN_TOLERANCE
      posture = clamp01(1 - (tiltDev + slouchDev + leanDev) / 3)
      bufPosture.push(posture)

      if (tiltDev > 1) postureFlags.push('shoulders uneven')
      if (slouchDev > 1) postureFlags.push('slouching')
      if (leanDev > 1) postureFlags.push('leaning off-centre')
      for (const flag of postureFlags) bufFlags[flag] = (bufFlags[flag] || 0) + 1
    }

    // Overlay gets live values every tick; the report gets a stable average.
    onFrame?.({
      face: face.landmarks,
      pose: pose?.landmarks || null,
      faces: face.faces,
      attention,
      posture,
      lookingAway,
      postureFlags,
    })

    if (dueForSample) emitSample()
  }

  timer = setInterval(tick, DETECT_INTERVAL_MS)

  return {
    stop() {
      stopped = true
      if (timer) clearInterval(timer)
      try { faceLandmarker?.close() } catch { /* already closed */ }
      try { poseLandmarker?.close() } catch { /* already closed */ }
    },
  }
}

/** Condense a run of samples into the summary the report consumes. */
export function summariseVision(samples) {
  const valid = samples.filter(s => s && s.attention !== null && !s.calibrating)
  if (!valid.length) return null

  const attention = valid.map(s => s.attention)
  const postures = valid.map(s => s.posture).filter(p => p !== null && p !== undefined)
  const awayCount = valid.filter(s => s.lookingAway).length

  const flagTally = {}
  for (const s of valid) {
    for (const flag of s.postureFlags || []) {
      flagTally[flag] = (flagTally[flag] || 0) + 1
    }
  }

  return {
    samples: valid.length,
    avg_attention: Number(mean(attention).toFixed(3)),
    min_attention: Number(Math.min(...attention).toFixed(3)),
    looking_away_ratio: Number((awayCount / valid.length).toFixed(3)),
    avg_posture: postures.length ? Number(mean(postures).toFixed(3)) : null,
    posture_flags: Object.entries(flagTally)
      .filter(([, n]) => n / valid.length > 0.15)
      .map(([flag, n]) => ({ flag, ratio: Number((n / valid.length).toFixed(2)) })),
    avg_blink_rate: Number(mean(valid.map(s => s.blinkRate || 0)).toFixed(1)),
  }
}
