import { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Clock, MessageCircle, AlertTriangle, Smile, RotateCw, TrendingUp, Activity } from 'lucide-react'

export default function DashboardScreen({ sessionData }) {
  const duration = sessionData.startTime ? Math.floor((Date.now() - sessionData.startTime) / 1000) : 0
  const mins = Math.floor(duration / 60)
  const secs = duration % 60
  const agentMsgs = sessionData.transcript.filter(t => t.role === 'agent')
  const candidateMsgs = sessionData.transcript.filter(t => t.role === 'candidate')

  // Emotion analysis
  const emotionCounts = {}
  for (const e of sessionData.emotions) {
    emotionCounts[e.emotion] = (emotionCounts[e.emotion] || 0) + 1
  }
  const totalEmotions = sessionData.emotions.length || 1
  const maxEmotionCount = Math.max(...Object.values(emotionCounts), 1)
  const emotionColors = { happy: '#10b981', sad: '#6366f1', angry: '#ef4444', surprised: '#f59e0b', fearful: '#8b5cf6', disgusted: '#64748b', neutral: '#94a3b8' }
  const sortedEmotions = Object.entries(emotionCounts).sort((a, b) => b[1] - a[1])
  const dominantEmotion = sortedEmotions.length > 0 ? sortedEmotions[0][0] : 'N/A'
  const dominantPct = sortedEmotions.length > 0 ? Math.round((sortedEmotions[0][1] / totalEmotions) * 100) : 0

  // Average confidence
  const avgConfidence = sessionData.emotions.length > 0
    ? Math.round(sessionData.emotions.reduce((s, e) => s + (e.confidence || 0), 0) / sessionData.emotions.length)
    : 0

  // Build Q&A pairs with timestamps
  const qaPairs = []
  let currentQ = null
  for (const msg of sessionData.transcript) {
    if (msg.role === 'agent') {
      if (currentQ) qaPairs.push(currentQ)
      currentQ = { question: msg.text, answer: null, qTime: msg.time, aTime: null }
    } else if (msg.role === 'candidate' && currentQ) {
      currentQ.answer = msg.text
      currentQ.aTime = msg.time
    }
  }
  if (currentQ) qaPairs.push(currentQ)

  return (
    <div className="h-full overflow-y-auto gradient-bg p-8">
      <div className="max-w-5xl mx-auto screen-enter">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-emerald-50 border border-emerald-200 rounded-full text-xs text-emerald-600 mb-4">
            <span className="w-2 h-2 bg-emerald-500 rounded-full" />
            Interview Complete
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Interview Report</h1>
          <p className="text-gray-500 mt-2">
            {new Date().toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            {' · '}{mins}m {secs}s · {sessionData.qCount} questions asked
          </p>
        </motion.div>

        {/* Metrics row */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-8">
          <MetricCard icon={<MessageCircle className="w-5 h-5" />} value={sessionData.qCount} label="Questions" color="indigo" />
          <MetricCard icon={<MessageCircle className="w-5 h-5" />} value={candidateMsgs.length} label="Answers" color="emerald" />
          <MetricCard icon={<Clock className="w-5 h-5" />} value={`${mins}m ${secs}s`} label="Duration" color="amber" />
          <MetricCard icon={<AlertTriangle className="w-5 h-5" />} value={sessionData.distractions.length} label="Distractions" color="red" />
          <MetricCard icon={<Smile className="w-5 h-5" />} value={dominantEmotion} label={`Dominant (${dominantPct}%)`} color="violet" />
          <MetricCard icon={<Activity className="w-5 h-5" />} value={`${avgConfidence}%`} label="Avg Confidence" color="indigo" />
        </div>

        {/* Emotion Timeline */}
        <div className="glass-card rounded-2xl p-6 mb-6">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-violet-500" /> Emotion Timeline
          </h3>
          {sessionData.emotions.length > 0 ? (
            <EmotionTimeline emotions={sessionData.emotions} colors={emotionColors} duration={duration} />
          ) : (
            <p className="text-sm text-gray-400">No emotion data captured</p>
          )}
        </div>

        {/* Emotion Distribution */}
        <div className="glass-card rounded-2xl p-6 mb-6">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Smile className="w-4 h-4 text-amber-500" /> Emotion Distribution
          </h3>
          {sortedEmotions.length > 0 ? (
            <div className="space-y-3">
              {sortedEmotions.map(([emotion, count]) => {
                const pct = Math.round((count / totalEmotions) * 100)
                return (
                  <div key={emotion} className="flex items-center gap-3">
                    <span className="text-sm text-gray-600 w-20 capitalize">{emotion}</span>
                    <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.6, delay: 0.1 }}
                        className="h-full rounded-full"
                        style={{ background: emotionColors[emotion] || '#94a3b8' }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 w-16 text-right">{pct}% ({count})</span>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-400">No emotion data captured</p>
          )}
        </div>

        {/* Q&A Transcript with timestamps */}
        <div className="glass-card rounded-2xl p-6 mb-6">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <MessageCircle className="w-4 h-4 text-indigo-500" /> Interview Transcript
          </h3>
          <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
            {qaPairs.length > 0 ? qaPairs.map((qa, i) => {
              const qTime = qa.qTime != null ? fmtTime(qa.qTime) : ''
              const aTime = qa.aTime != null ? fmtTime(qa.aTime) : ''
              const responseTime = (qa.qTime != null && qa.aTime != null) ? qa.aTime - qa.qTime : null
              return (
                <div key={i} className="border border-gray-100 rounded-xl overflow-hidden">
                  {/* Question */}
                  <div className="bg-indigo-50 border-b border-indigo-100 p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-bold text-indigo-500 uppercase">Q{i + 1}</span>
                      {qTime && <span className="text-[10px] text-gray-400">⏱ {qTime}</span>}
                    </div>
                    <p className="text-sm text-gray-700">{qa.question}</p>
                  </div>
                  {/* Answer */}
                  {qa.answer ? (
                    <div className="bg-white p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold text-emerald-500 uppercase">Answer</span>
                        {aTime && <span className="text-[10px] text-gray-400">⏱ {aTime}</span>}
                        {responseTime != null && (
                          <span className="text-[10px] text-gray-400 ml-auto">
                            Response: {responseTime}s
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700">{qa.answer}</p>
                    </div>
                  ) : (
                    <div className="bg-gray-50 p-3">
                      <p className="text-xs text-gray-400 italic">No answer recorded</p>
                    </div>
                  )}
                </div>
              )
            }) : (
              <p className="text-sm text-gray-400">No transcript recorded</p>
            )}
          </div>
        </div>

        {/* Distraction Events */}
        <div className="glass-card rounded-2xl p-6 mb-6">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-500" /> Distraction Events
          </h3>
          {sessionData.distractions.length > 0 ? (
            <div className="space-y-2">
              {sessionData.distractions.map((ev, i) => {
                const timeStr = ev.time != null ? fmtTime(ev.time) : ''
                const sev = ev.severity || 'low'
                const sevColor = sev === 'high' ? 'bg-red-100 border-red-200 text-red-700'
                  : sev === 'medium' ? 'bg-amber-100 border-amber-200 text-amber-700'
                  : 'bg-gray-100 border-gray-200 text-gray-600'
                return (
                  <div key={i} className="flex items-center gap-3 p-2.5 bg-red-50/50 border border-red-100 rounded-xl">
                    <span className="text-xs text-gray-400 min-w-[50px] font-mono">{timeStr}</span>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase border ${sevColor}`}>{sev}</span>
                    <span className="text-sm text-gray-600">{ev.detail || ev.text || ev.type}</span>
                    {ev.count > 1 && <span className="text-[10px] text-gray-400 ml-auto">×{ev.count}</span>}
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-sm text-emerald-600">No distractions detected — excellent focus! 🎯</p>
          )}
        </div>

        {/* Actions */}
        <div className="text-center pb-8">
          <button
            onClick={() => location.reload()}
            className="px-6 py-3 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-600 inline-flex items-center gap-2 transition-all shadow-sm"
          >
            <RotateCw className="w-4 h-4" /> Start New Interview
          </button>
        </div>
      </div>
    </div>
  )
}

function fmtTime(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function EmotionTimeline({ emotions, colors, duration }) {
  const canvasRef = useRef(null)
  const emotionMap = { happy: 6, surprised: 5, neutral: 4, sad: 3, fearful: 2, disgusted: 1, angry: 0 }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || emotions.length === 0) return
    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 2
    const w = canvas.offsetWidth
    const h = 160
    canvas.width = w * dpr
    canvas.height = h * dpr
    ctx.scale(dpr, dpr)
    canvas.style.height = `${h}px`

    const pad = { top: 20, bottom: 30, left: 70, right: 20 }
    const plotW = w - pad.left - pad.right
    const plotH = h - pad.top - pad.bottom
    const maxTime = Math.max(duration, emotions[emotions.length - 1]?.time || 60, 60)

    ctx.clearRect(0, 0, w, h)

    // Y-axis labels
    ctx.fillStyle = '#9ca3af'
    ctx.font = '9px Inter, sans-serif'
    ctx.textAlign = 'right'
    const labels = Object.keys(emotionMap)
    labels.forEach(label => {
      const y = pad.top + plotH - (emotionMap[label] / 6) * plotH
      ctx.fillText(label, pad.left - 8, y + 3)
      ctx.beginPath()
      ctx.moveTo(pad.left, y)
      ctx.lineTo(pad.left + plotW, y)
      ctx.strokeStyle = '#f3f4f6'
      ctx.lineWidth = 1
      ctx.stroke()
    })

    // X-axis time labels
    ctx.textAlign = 'center'
    const ticks = Math.min(6, Math.ceil(maxTime / 30))
    for (let i = 0; i <= ticks; i++) {
      const t = Math.round((i / ticks) * maxTime)
      const x = pad.left + (t / maxTime) * plotW
      ctx.fillStyle = '#9ca3af'
      ctx.fillText(`${Math.floor(t / 60)}:${(t % 60).toString().padStart(2, '0')}`, x, h - 8)
    }

    // Plot dots and lines
    if (emotions.length > 1) {
      ctx.beginPath()
      emotions.forEach((e, i) => {
        const x = pad.left + (e.time / maxTime) * plotW
        const yVal = emotionMap[e.emotion] ?? 4
        const y = pad.top + plotH - (yVal / 6) * plotH
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      })
      ctx.strokeStyle = '#8b5cf6'
      ctx.lineWidth = 1.5
      ctx.stroke()
    }

    emotions.forEach(e => {
      const x = pad.left + (e.time / maxTime) * plotW
      const yVal = emotionMap[e.emotion] ?? 4
      const y = pad.top + plotH - (yVal / 6) * plotH
      ctx.beginPath()
      ctx.arc(x, y, 4, 0, Math.PI * 2)
      ctx.fillStyle = colors[e.emotion] || '#94a3b8'
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 1.5
      ctx.stroke()
    })
  }, [emotions, colors, duration])

  return (
    <canvas ref={canvasRef} className="w-full rounded-lg bg-white border border-gray-100" style={{ height: '160px' }} />
  )
}

function MetricCard({ icon, value, label, color }) {
  const colors = {
    indigo: 'bg-indigo-50 border-indigo-100 text-indigo-600',
    emerald: 'bg-emerald-50 border-emerald-100 text-emerald-600',
    amber: 'bg-amber-50 border-amber-100 text-amber-600',
    red: 'bg-red-50 border-red-100 text-red-600',
    violet: 'bg-violet-50 border-violet-100 text-violet-600',
  }
  return (
    <div className={`${colors[color]} border rounded-2xl p-4 text-center`}>
      <div className="flex justify-center mb-2 opacity-60">{icon}</div>
      <p className="text-xl font-bold capitalize">{value}</p>
      <p className="text-[10px] text-gray-500 mt-1">{label}</p>
    </div>
  )
}
