import { useRef, useEffect } from 'react'
import { POSE_CONNECTIONS, FACE_OVAL, LEFT_EYE, RIGHT_EYE } from '../lib/vision'

/**
 * Draws what MediaPipe is actually detecting on top of the candidate's video:
 * the face bounding box and contour, the eye landmarks used for gaze, and the
 * upper-body skeleton used for posture.
 *
 * This is not decoration. The candidate can see exactly which signals are
 * being measured, which is the same transparency the rest of the system
 * applies to its scoring.
 *
 * Frames arrive through a ref and are drawn on an animation frame loop rather
 * than through React state. Detection runs five times a second, and pushing
 * that through state would re-render the whole interview screen — including
 * the conversation list — at the same rate for no benefit.
 *
 * Landmarks are normalised (0-1) against the source video frame. The video is
 * rendered with object-fit: cover, so the same crop maths has to be applied
 * here or the overlay drifts away from the face.
 */
export default function LandmarkOverlay({ frameRef, videoRef, mirrored = true }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    let raf = null
    let stopped = false

    const draw = () => {
      if (stopped) return
      raf = requestAnimationFrame(draw)

      const canvas = canvasRef.current
      const video = videoRef?.current
      if (!canvas || !video) return

      const ctx = canvas.getContext('2d')
      const cssW = canvas.clientWidth
      const cssH = canvas.clientHeight
      if (!cssW || !cssH) return

      const dpr = window.devicePixelRatio || 1
      if (canvas.width !== Math.round(cssW * dpr) || canvas.height !== Math.round(cssH * dpr)) {
        canvas.width = Math.round(cssW * dpr)
        canvas.height = Math.round(cssH * dpr)
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, cssW, cssH)

      const frame = frameRef?.current
      if (!frame || (!frame.face && !frame.pose)) return

      // Replicate object-fit: cover so points land on the visible pixels.
      const vw = video.videoWidth || cssW
      const vh = video.videoHeight || cssH
      const scale = Math.max(cssW / vw, cssH / vh)
      const drawW = vw * scale
      const drawH = vh * scale
      const offsetX = (cssW - drawW) / 2
      const offsetY = (cssH - drawH) / 2

      const project = (pt) => {
        const x = offsetX + pt.x * drawW
        return { x: mirrored ? cssW - x : x, y: offsetY + pt.y * drawH }
      }

      const attention = frame.attention
      const accent = frame.calibrating ? '#a78bfa'
        : attention === null || attention === undefined ? '#94a3b8'
        : attention >= 0.7 ? '#34d399'
        : attention >= 0.45 ? '#fbbf24'
        : '#f87171'

      // ── Pose skeleton (M8) ──────────────────────────────────────────────
      if (frame.pose) {
        const pose = frame.pose
        ctx.lineWidth = 3
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.75)'
        ctx.lineCap = 'round'

        for (const [a, b] of POSE_CONNECTIONS) {
          const pa = pose[a]
          const pb = pose[b]
          // visibility is MediaPipe's own confidence for that joint
          if (!pa || !pb) continue
          if ((pa.visibility ?? 1) < 0.5 || (pb.visibility ?? 1) < 0.5) continue
          const p1 = project(pa)
          const p2 = project(pb)
          ctx.beginPath()
          ctx.moveTo(p1.x, p1.y)
          ctx.lineTo(p2.x, p2.y)
          ctx.stroke()
        }

        ctx.fillStyle = '#38bdf8'
        const drawn = new Set()
        for (const [a, b] of POSE_CONNECTIONS) {
          for (const idx of [a, b]) {
            if (drawn.has(idx)) continue
            drawn.add(idx)
            const pt = pose[idx]
            if (!pt || (pt.visibility ?? 1) < 0.5) continue
            const p = project(pt)
            ctx.beginPath()
            ctx.arc(p.x, p.y, 4, 0, Math.PI * 2)
            ctx.fill()
          }
        }
      }

      // ── Face contour, eyes and bounding box (M7) ────────────────────────
      if (frame.face) {
        const face = frame.face

        const strokePath = (indices) => {
          ctx.beginPath()
          let started = false
          for (const idx of indices) {
            const pt = face[idx]
            if (!pt) continue
            const p = project(pt)
            if (started) {
              ctx.lineTo(p.x, p.y)
            } else {
              ctx.moveTo(p.x, p.y)
              started = true
            }
          }
          ctx.closePath()
          ctx.stroke()
        }

        ctx.strokeStyle = accent
        ctx.lineWidth = 2
        strokePath(FACE_OVAL)

        // The landmarks the gaze estimate is built from
        ctx.lineWidth = 1.6
        strokePath(LEFT_EYE)
        strokePath(RIGHT_EYE)

        // Bounding box drawn as corner brackets
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
        for (const pt of face) {
          const p = project(pt)
          if (p.x < minX) minX = p.x
          if (p.x > maxX) maxX = p.x
          if (p.y < minY) minY = p.y
          if (p.y > maxY) maxY = p.y
        }
        const pad = 10
        minX -= pad; minY -= pad; maxX += pad; maxY += pad
        const corner = Math.min(26, Math.max(8, (maxX - minX) / 4))

        ctx.strokeStyle = accent
        ctx.lineWidth = 2.5
        ctx.beginPath()
        ctx.moveTo(minX, minY + corner); ctx.lineTo(minX, minY); ctx.lineTo(minX + corner, minY)
        ctx.moveTo(maxX - corner, minY); ctx.lineTo(maxX, minY); ctx.lineTo(maxX, minY + corner)
        ctx.moveTo(maxX, maxY - corner); ctx.lineTo(maxX, maxY); ctx.lineTo(maxX - corner, maxY)
        ctx.moveTo(minX + corner, maxY); ctx.lineTo(minX, maxY); ctx.lineTo(minX, maxY - corner)
        ctx.stroke()

        // Label above the box
        const label = frame.calibrating
          ? 'Calibrating…'
          : attention === null || attention === undefined
          ? 'Tracking'
          : `Attention ${Math.round(attention * 100)}%`

        ctx.font = '600 12px Inter, sans-serif'
        const textW = ctx.measureText(label).width
        const boxY = Math.max(2, minY - 24)
        ctx.fillStyle = accent
        ctx.beginPath()
        if (ctx.roundRect) {
          ctx.roundRect(minX, boxY, textW + 16, 20, 5)
        } else {
          ctx.rect(minX, boxY, textW + 16, 20)
        }
        ctx.fill()
        ctx.fillStyle = '#0b1220'
        ctx.fillText(label, minX + 8, boxY + 14)
      }
    }

    raf = requestAnimationFrame(draw)
    return () => {
      stopped = true
      if (raf) cancelAnimationFrame(raf)
    }
  }, [frameRef, videoRef, mirrored])

  return (
    <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
  )
}
