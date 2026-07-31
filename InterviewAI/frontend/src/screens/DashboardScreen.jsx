import { motion } from 'framer-motion'
import { Clock, MessageCircle, AlertTriangle, Smile, RotateCw } from 'lucide-react'

export default function DashboardScreen({ sessionData }) {
  const duration = sessionData.startTime ? Math.floor((Date.now() - sessionData.startTime) / 1000) : 0
  const mins = Math.floor(duration / 60)
  const agentMsgs = sessionData.transcript.filter(t => t.role === 'agent')
  const candidateMsgs = sessionData.transcript.filter(t => t.role === 'candidate')

  const emotionCounts = {}
  for (const e of sessionData.emotions) {
    emotionCounts[e.emotion] = (emotionCounts[e.emotion] || 0) + 1
  }
  const maxEmotionCount = Math.max(...Object.values(emotionCounts), 1)
  const emotionColors = { happy: '#10b981', sad: '#6366f1', angry: '#ef4444', surprised: '#f59e0b', fearful: '#8b5cf6', disgusted: '#64748b', neutral: '#94a3b8' }

  return (
    <div className="h-full overflow-y-auto gradient-bg p-8">
      <div className="max-w-5xl mx-auto screen-enter">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-emerald-50 border border-emerald-200 rounded-full text-xs text-emerald-600 mb-4">
            <span className="w-2 h-2 bg-emerald-500 rounded-full" />
            Interview Complete
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Interview Summary</h1>
          <p className="text-gray-500 mt-2">
            Duration: {mins} min · {sessionData.qCount} questions · {new Date().toLocaleDateString()}
          </p>
        </motion.div>

        {/* Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <MetricCard icon={<MessageCircle className="w-5 h-5" />} value={sessionData.qCount} label="Questions" color="indigo" />
          <MetricCard icon={<MessageCircle className="w-5 h-5" />} value={candidateMsgs.length} label="Answers" color="emerald" />
          <MetricCard icon={<Clock className="w-5 h-5" />} value={`${mins}m`} label="Duration" color="amber" />
          <MetricCard icon={<AlertTriangle className="w-5 h-5" />} value={sessionData.distractions.length} label="Distractions" color="red" />
          <MetricCard icon={<Smile className="w-5 h-5" />} value={sessionData.emotions.length} label="Emotion Samples" color="violet" />
        </div>

        {/* Transcript */}
        <div className="glass-card rounded-2xl p-6 mb-6">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <MessageCircle className="w-4 h-4 text-indigo-500" /> Full Transcript
          </h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {sessionData.transcript.length > 0 ? sessionData.transcript.map((msg, i) => {
              const timeStr = msg.time != null ? `${Math.floor(msg.time / 60)}:${(msg.time % 60).toString().padStart(2, '0')}` : ''
              return (
                <div key={i} className={`p-3 rounded-xl border ${
                  msg.role === 'agent' ? 'bg-indigo-50 border-indigo-100' : 'bg-emerald-50 border-emerald-100'
                }`}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-semibold text-gray-400 uppercase">
                      {msg.role === 'agent' ? '🤖 Interviewer' : '🧑 Candidate'}
                    </span>
                    {timeStr && <span className="text-[10px] text-gray-400">{timeStr}</span>}
                  </div>
                  <p className="text-sm text-gray-700">{msg.text}</p>
                </div>
              )
            }) : (
              <p className="text-sm text-gray-400">No transcript recorded</p>
            )}
          </div>
        </div>

        {/* Emotion Chart */}
        <div className="glass-card rounded-2xl p-6 mb-6">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Smile className="w-4 h-4 text-amber-500" /> Emotion Distribution
          </h3>
          {Object.keys(emotionCounts).length > 0 ? (
            <div className="flex items-end gap-3 h-40">
              {Object.entries(emotionCounts).sort((a, b) => b[1] - a[1]).map(([emotion, count]) => {
                const height = Math.max((count / maxEmotionCount) * 120, 8)
                return (
                  <div key={emotion} className="flex-1 flex flex-col items-center gap-2">
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height }}
                      transition={{ duration: 0.5, delay: 0.1 }}
                      className="w-full rounded-t-lg"
                      style={{ background: emotionColors[emotion] || '#94a3b8' }}
                    />
                    <span className="text-[10px] text-gray-500 text-center">{emotion}</span>
                    <span className="text-[10px] text-gray-400">{count}</span>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-400">No emotion data captured</p>
          )}
        </div>

        {/* Distraction Events */}
        <div className="glass-card rounded-2xl p-6 mb-6">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-500" /> Distraction & Warning Events
          </h3>
          {sessionData.distractions.length > 0 ? (
            <div className="space-y-2">
              {sessionData.distractions.map((ev, i) => {
                const timeStr = ev.time != null ? `${Math.floor(ev.time / 60)}:${(ev.time % 60).toString().padStart(2, '0')}` : ''
                return (
                  <div key={i} className="flex items-center gap-3 p-2 bg-red-50 border border-red-100 rounded-xl">
                    <span className="text-xs text-gray-400 min-w-[50px]">{timeStr}</span>
                    <span className="text-sm text-gray-600">⚠️ {ev.detail || ev.text || ev.type}</span>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-sm text-emerald-600">No distractions — great focus! 🎯</p>
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
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-[10px] text-gray-500 mt-1">{label}</p>
    </div>
  )
}
