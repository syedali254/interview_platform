/**
 * Stage the MediaPipe vision assets into public/mediapipe.
 *
 * The WASM runtime is copied out of node_modules (it ships with the npm
 * package). The .task model files are not on npm, so they are fetched once
 * from Google's model store and cached in public/.
 *
 * Everything is served from our own origin at runtime — the interview page
 * must not depend on a CDN being reachable mid-session.
 *
 * Failure here is non-fatal: the build continues and the app degrades to
 * running without face/posture analysis.
 */
import { mkdir, copyFile, readdir, access, writeFile, stat } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const root = join(here, '..')
const wasmSrc = join(root, 'node_modules', '@mediapipe', 'tasks-vision', 'wasm')
const wasmDest = join(root, 'public', 'mediapipe', 'wasm')
const modelDest = join(root, 'public', 'mediapipe', 'models')

const MODELS = [
  {
    file: 'face_landmarker.task',
    url: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
  },
  {
    file: 'pose_landmarker_lite.task',
    url: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',
  },
]

const exists = async (p) => {
  try { await access(p); return true } catch { return false }
}

async function copyWasm() {
  if (!(await exists(wasmSrc))) {
    console.warn('[vision-assets] WASM source missing — is @mediapipe/tasks-vision installed?')
    return false
  }
  await mkdir(wasmDest, { recursive: true })
  const files = await readdir(wasmSrc)
  await Promise.all(files.map(f => copyFile(join(wasmSrc, f), join(wasmDest, f))))
  console.log(`[vision-assets] WASM runtime staged (${files.length} files)`)
  return true
}

async function fetchModels() {
  await mkdir(modelDest, { recursive: true })
  let ok = 0

  for (const { file, url } of MODELS) {
    const target = join(modelDest, file)
    if (await exists(target)) {
      const { size } = await stat(target)
      if (size > 100_000) {
        console.log(`[vision-assets] ${file} already cached`)
        ok++
        continue
      }
    }
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(120_000) })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await writeFile(target, Buffer.from(await res.arrayBuffer()))
      console.log(`[vision-assets] downloaded ${file}`)
      ok++
    } catch (err) {
      console.warn(`[vision-assets] could not download ${file}: ${err.message}`)
    }
  }
  return ok
}

const wasmOk = await copyWasm()
const modelsOk = await fetchModels()

if (wasmOk && modelsOk === MODELS.length) {
  console.log('[vision-assets] ready — attention and posture analysis enabled')
} else {
  console.warn('[vision-assets] incomplete — the app will run without MediaPipe analysis')
}
