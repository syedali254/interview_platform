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
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const w = canvas.width = canvas.offsetWidth * 2
    const h = canvas.height = 500
    ctx.scale(2, 2)
    const cw = w / 2, ch = h / 2

    // Build nodes from graph data
    const matched = graph.gaps?.matched_required || []
    const missing = graph.gaps?.missing_required || []
    const topics = graph.topics || []

    const centerNode = { x: cw / 2, y: ch / 2, label: 'Role', type: 'center', r: 24 }
    const nodes = [centerNode]
    const edges = []

    // Matched skills (green) — arranged in an arc to the left
    matched.forEach((skill, i) => {
      const angle = (-Math.PI / 3) + (i / Math.max(matched.length - 1, 1)) * (Math.PI * 0.6)
      const dist = 100 + Math.random() * 30
      const node = {
        x: cw / 2 + Math.cos(angle) * dist,
        y: ch / 2 + Math.sin(angle) * dist,
        label: skill.length > 14 ? skill.slice(0, 12) + '..' : skill,
        type: 'matched', r: 16
      }
      nodes.push(node)
      edges.push({ from: centerNode, to: node })
    })

    // Missing skills (red) — arranged in an arc to the right
    missing.forEach((skill, i) => {
      const angle = (Math.PI / 6) + (i / Math.max(missing.length - 1, 1)) * (Math.PI * 0.5)
      const dist = 120 + Math.random() * 20
      const node = {
        x: cw / 2 + Math.cos(angle) * dist,
        y: ch / 2 + Math.sin(angle) * dist,
        label: skill.length > 14 ? skill.slice(0, 12) + '..' : skill,
        type: 'gap', r: 16
      }
      nodes.push(node)
      edges.push({ from: centerNode, to: node })
    })

    // Topic connections (purple) — arranged below
    topics.forEach((topic, i) => {
      const angle = (Math.PI * 0.6) + (i / Math.max(topics.length - 1, 1)) * (Math.PI * 0.5)
      const dist = 140 + Math.random() * 20
      const existing = nodes.find(n => n.label === topic.skill || n.label === (topic.skill.length > 14 ? topic.skill.slice(0, 12) + '..' : topic.skill))
      if (existing) {
        existing.isTopic = true
        return
      }
      const node = {
        x: cw / 2 + Math.cos(angle) * dist,
        y: ch / 2 + Math.sin(angle) * dist,
        label: topic.skill.length > 14 ? topic.skill.slice(0, 12) + '..' : topic.skill,
        type: 'topic', r: 14
      }
      nodes.push(node)
      edges.push({ from: centerNode, to: node })
    })

    // Draw
    ctx.clearRect(0, 0, cw, ch)

    // Edges
    edges.forEach(({ from, to }) => {
      ctx.beginPath()
      ctx.moveTo(from.x, from.y)
      ctx.lineTo(to.x, to.y)
      ctx.strokeStyle = to.type === 'gap' ? '#fca5a5' : to.type === 'matched' ? '#86efac' : '#c4b5fd'
      ctx.lineWidth = 1.5
      ctx.stroke()
    })

    // Nodes
    nodes.forEach(node => {
      ctx.beginPath()
      ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2)
      if (node.type === 'center') {
        ctx.fillStyle = '#6366f1'
      } else if (node.type === 'matched') {
        ctx.fillStyle = '#10b981'
      } else if (node.type === 'gap') {
        ctx.fillStyle = '#ef4444'
      } else {
        ctx.fillStyle = '#8b5cf6'
      }
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.stroke()

      // Label
      ctx.fillStyle = '#374151'
      ctx.font = node.type === 'center' ? 'bold 11px Inter, sans-serif' : '10px Inter, sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(node.label, node.x, node.y + node.r + 14)
    })

    // Legend
    const legendY = ch / 2 - 10
    const legends = [
      { color: '#10b981', label: 'Matched' },
      { color: '#ef4444', label: 'Gap' },
      { color: '#8b5cf6', label: 'Topic' },
    ]
    legends.forEach((l, i) => {
      const lx = 20
      const ly = legendY + i * 22
      ctx.beginPath()
      ctx.arc(lx, ly, 6, 0, Math.PI * 2)
      ctx.fillStyle = l.color
      ctx.fill()
      ctx.fillStyle = '#6b7280'
      ctx.font = '10px Inter, sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(l.label, lx + 12, ly + 4)
    })
  }, [graph])

  return (
    <canvas
      ref={canvasRef}
      className="w-full rounded-xl bg-gradient-to-br from-gray-50 to-indigo-50/30 border border-gray-100"
      style={{ height: '250px' }}
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
