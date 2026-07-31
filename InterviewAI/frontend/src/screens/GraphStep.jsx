import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Loader2, ArrowRight, GitBranch, Target, AlertTriangle } from 'lucide-react'
import axios from 'axios'

export default function GraphStep({ session, updateSession, onNext }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const buildGraph = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await axios.post('/api/build-graph')
      updateSession({ graphData: res.data.data })
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  const graph = session.graphData

  return (
    <div className="h-full overflow-y-auto gradient-bg p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Skill Graph Analysis</h2>
          <p className="text-gray-500 mt-1">ESCO-based skill graph mapping candidate skills to job requirements</p>
        </div>

        {!graph ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-indigo-50 rounded-2xl flex items-center justify-center mb-6">
              <GitBranch className="w-10 h-10 text-indigo-500" />
            </div>
            <p className="text-gray-500 mb-6">Build the skill knowledge graph from your CV and JD data</p>
            {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
            <button
              onClick={buildGraph}
              disabled={loading}
              className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 rounded-xl font-semibold text-white flex items-center gap-2 shadow-lg shadow-indigo-200 transition-all"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitBranch className="w-4 h-4" />}
              {loading ? 'Analyzing skills...' : 'Build Graph'}
            </button>
          </div>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {/* Summary cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard label="Total Skills" value={graph.summary?.total_skills || graph.topics?.length || 0} color="indigo" />
              <StatCard label="Matched" value={graph.summary?.matched || 0} color="emerald" />
              <StatCard label="Gaps" value={graph.summary?.gaps || 0} color="red" />
              <StatCard label="Interview Topics" value={graph.topics?.length || 0} color="violet" />
            </div>

            {/* Visual Skill Graph */}
            <div className="glass-card rounded-2xl p-6 mb-6">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-indigo-500" /> Skill Relationship Graph
              </h3>
              <SkillGraphCanvas graph={graph} />
            </div>

            {/* Topics list */}
            <div className="glass-card rounded-2xl p-6 mb-6">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Target className="w-4 h-4 text-indigo-500" /> Interview Topics
              </h3>
              <div className="space-y-2">
                {(graph.topics || []).map((topic, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
                    <span className={`px-2.5 py-0.5 rounded-lg text-xs font-medium ${
                      topic.priority === 'high' ? 'bg-red-50 text-red-600 border border-red-100' :
                      topic.priority === 'medium' ? 'bg-amber-50 text-amber-600 border border-amber-100' :
                      'bg-gray-100 text-gray-500'
                    }`}>
                      {topic.priority}
                    </span>
                    <span className="text-sm text-gray-800 font-medium">{topic.skill}</span>
                    <span className="text-xs text-gray-400 ml-auto">{topic.reason}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Skill gap warnings */}
            {graph.summary?.gaps > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-6 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-amber-700 font-medium">Skill Gaps Detected</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {graph.summary.gaps} required skills not found in candidate's profile. These will be tested during the interview.
                  </p>
                </div>
              </div>
            )}

            <div className="flex justify-end">
              <button
                onClick={onNext}
                className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 rounded-xl font-semibold text-white flex items-center gap-2 shadow-lg shadow-indigo-200 transition-all"
              >
                Generate Questions <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}

function SkillGraphCanvas({ graph }) {
  const matched = graph.gaps?.matched_required || []
  const missing = graph.gaps?.missing_required || []
  const extra = graph.gaps?.extra_skills || []

  return (
    <div className="space-y-6">
      {/* Graph 1: Matched Skills */}
      <div className="bg-emerald-50/50 border border-emerald-100 rounded-xl p-4">
        <h4 className="text-sm font-semibold text-emerald-700 mb-3 flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-emerald-500" /> Matched Skills ({matched.length})
          <span className="text-xs font-normal text-gray-500 ml-auto">Candidate has ✓ Job requires ✓</span>
        </h4>
        {matched.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {matched.map((skill, i) => (
              <span key={i} className="px-3 py-1.5 bg-emerald-100 border border-emerald-200 text-emerald-700 rounded-lg text-xs font-medium">
                ✓ {skill}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-400">No matched skills found</p>
        )}
        <SingleGraphCanvas skills={matched} color="#10b981" label="Matched" />
      </div>

      {/* Graph 2: Missing / Gap Skills */}
      <div className="bg-red-50/50 border border-red-100 rounded-xl p-4">
        <h4 className="text-sm font-semibold text-red-700 mb-3 flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-red-500" /> Missing Skills ({missing.length})
          <span className="text-xs font-normal text-gray-500 ml-auto">Job requires ✓ Candidate lacks ✗</span>
        </h4>
        {missing.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {missing.map((skill, i) => (
              <span key={i} className="px-3 py-1.5 bg-red-100 border border-red-200 text-red-700 rounded-lg text-xs font-medium">
                ✗ {skill}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-emerald-600">No gaps — candidate covers all requirements! 🎯</p>
        )}
        <SingleGraphCanvas skills={missing} color="#ef4444" label="Gap" />
      </div>

      {/* Graph 3: Extra Skills */}
      <div className="bg-violet-50/50 border border-violet-100 rounded-xl p-4">
        <h4 className="text-sm font-semibold text-violet-700 mb-3 flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-violet-500" /> Extra Skills ({extra.length})
          <span className="text-xs font-normal text-gray-500 ml-auto">Candidate has ✓ Job doesn't require</span>
        </h4>
        {extra.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {extra.map((skill, i) => (
              <span key={i} className="px-3 py-1.5 bg-violet-100 border border-violet-200 text-violet-700 rounded-lg text-xs font-medium">
                + {skill}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-400">No extra skills detected</p>
        )}
        <SingleGraphCanvas skills={extra} color="#8b5cf6" label="Extra" />
      </div>
    </div>
  )
}

function SingleGraphCanvas({ skills, color, label }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || skills.length === 0) return
    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 2
    const w = canvas.offsetWidth
    const h = 180
    canvas.width = w * dpr
    canvas.height = h * dpr
    ctx.scale(dpr, dpr)
    canvas.style.height = `${h}px`

    const cx = w / 2
    const cy = h / 2
    const radius = Math.min(cx, cy) - 40

    ctx.clearRect(0, 0, w, h)

    // Center node
    ctx.beginPath()
    ctx.arc(cx, cy, 18, 0, Math.PI * 2)
    ctx.fillStyle = color
    ctx.fill()
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()
    ctx.fillStyle = '#fff'
    ctx.font = 'bold 9px Inter, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(label, cx, cy)

    // Skill nodes in a circle
    const count = skills.length
    skills.forEach((skill, i) => {
      const angle = (i / count) * Math.PI * 2 - Math.PI / 2
      const nx = cx + Math.cos(angle) * radius
      const ny = cy + Math.sin(angle) * radius

      // Edge
      ctx.beginPath()
      ctx.moveTo(cx, cy)
      ctx.lineTo(nx, ny)
      ctx.strokeStyle = color + '40'
      ctx.lineWidth = 1.5
      ctx.stroke()

      // Node
      ctx.beginPath()
      ctx.arc(nx, ny, 10, 0, Math.PI * 2)
      ctx.fillStyle = color + '20'
      ctx.fill()
      ctx.strokeStyle = color
      ctx.lineWidth = 1.5
      ctx.stroke()

      // Label
      ctx.fillStyle = '#374151'
      ctx.font = '9px Inter, sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      const displaySkill = skill.length > 16 ? skill.slice(0, 14) + '..' : skill
      ctx.fillText(displaySkill, nx, ny + 14)
    })
  }, [skills, color, label])

  if (skills.length === 0) return null

  return (
    <canvas
      ref={canvasRef}
      className="w-full rounded-lg bg-white/50 border border-gray-100 mt-3"
      style={{ height: '180px' }}
    />
  )
}

function StatCard({ label, value, color }) {
  const colors = {
    indigo: 'text-indigo-600 bg-indigo-50 border-indigo-100',
    emerald: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    red: 'text-red-600 bg-red-50 border-red-100',
    violet: 'text-violet-600 bg-violet-50 border-violet-100',
  }
  return (
    <div className={`${colors[color]} border rounded-2xl p-4 text-center`}>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  )
}
