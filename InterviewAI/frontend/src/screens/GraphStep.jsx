import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { Loader2, ArrowRight, GitBranch, Target, AlertTriangle, List, Network } from 'lucide-react'
import axios from 'axios'

/* Status vocabulary shared by the graph, the legend and the list view. */
const STATUS = {
  matched:       { label: 'Matched',   color: '#10b981', hint: 'On the CV and required by the role' },
  missing:       { label: 'Gap',       color: '#ef4444', hint: 'Required by the role, not on the CV' },
  bonus:         { label: 'Bonus',     color: '#8b5cf6', hint: 'Nice-to-have the candidate already has' },
  bonus_missing: { label: 'Bonus gap', color: '#f59e0b', hint: 'Nice-to-have the candidate lacks' },
  extra:         { label: 'Extra',     color: '#64748b', hint: 'On the CV, not asked for by the role' },
}
const STATUS_ORDER = ['matched', 'missing', 'bonus', 'bonus_missing', 'extra']

export default function GraphStep({ session, updateSession, onNext }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [visible, setVisible] = useState(() => new Set(STATUS_ORDER))
  const [view, setView] = useState('graph')

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

  const toggleStatus = (key) => {
    setVisible(prev => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      // Never allow an empty selection — it would blank the whole view.
      return next.size ? next : prev
    })
  }

  /* Drop hidden statuses, then drop clusters left with nothing in them. */
  const clusters = useMemo(() => {
    const all = graph?.graph?.clusters || []
    return all
      .map(c => ({ ...c, skills: c.skills.filter(s => visible.has(s.status)) }))
      .filter(c => c.skills.length > 0)
  }, [graph, visible])

  if (!graph) {
    return (
      <div className="h-full overflow-y-auto gradient-bg p-8">
        <div className="max-w-6xl mx-auto">
          <Header />
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
              {loading ? 'Analysing skills...' : 'Build Graph'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  const s = graph.summary || {}
  const stats = graph.stats || {}

  return (
    <div className="h-full overflow-y-auto gradient-bg p-8">
      <div className="max-w-6xl mx-auto">
        <Header />

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {/* Headline numbers */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-5">
            <StatCard label="Skills in play" value={s.total_skills ?? 0} color="indigo" />
            <StatCard label="Matched" value={s.matched ?? 0} color="emerald" />
            <StatCard label="Gaps" value={s.gaps ?? 0} color="red" />
            <StatCard label="Bonus" value={s.bonus ?? 0} color="violet" />
            <StatCard label="Extra" value={s.extra ?? 0} color="slate" />
          </div>

          {/* Requirement coverage */}
          <div className="glass-card rounded-2xl p-5 mb-5">
            <div className="flex items-baseline justify-between mb-2">
              <h3 className="font-semibold text-gray-800 text-sm">Requirement coverage</h3>
              <span className="text-2xl font-bold text-gray-900">{s.match_percentage ?? 0}%</span>
            </div>
            <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(100, s.match_percentage ?? 0)}%` }}
                transition={{ duration: 0.7, ease: 'easeOut' }}
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-emerald-500"
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {s.matched ?? 0} of {stats.job_required ?? 0} required skills found on the CV
              {stats.taxonomy_size ? ` · matched against ${stats.taxonomy_size.toLocaleString()} taxonomy concepts` : ''}
            </p>
          </div>

          {/* Graph */}
          <div className="glass-card rounded-2xl p-6 mb-5">
            <div className="flex flex-wrap items-center gap-3 mb-4">
              <h3 className="font-semibold text-gray-800 flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-indigo-500" /> Skill Knowledge Graph
              </h3>
              <div className="ml-auto flex items-center gap-1 bg-gray-100 rounded-lg p-0.5">
                <ViewToggle active={view === 'graph'} onClick={() => setView('graph')} icon={<Network className="w-3.5 h-3.5" />} label="Graph" />
                <ViewToggle active={view === 'list'} onClick={() => setView('list')} icon={<List className="w-3.5 h-3.5" />} label="List" />
              </div>
            </div>

            {/* Legend doubles as a filter */}
            <div className="flex flex-wrap gap-2 mb-5">
              {STATUS_ORDER.map(key => {
                const on = visible.has(key)
                const meta = STATUS[key]
                const count = graph.graph?.counts?.[key] || 0
                return (
                  <button
                    key={key}
                    onClick={() => toggleStatus(key)}
                    title={meta.hint}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
                      on ? 'bg-white border-gray-200 text-gray-700' : 'bg-gray-50 border-gray-100 text-gray-300'
                    }`}
                  >
                    <span
                      className="w-2.5 h-2.5 rounded-full transition-opacity"
                      style={{ background: meta.color, opacity: on ? 1 : 0.25 }}
                    />
                    {meta.label}
                    <span className={on ? 'text-gray-400' : 'text-gray-300'}>{count}</span>
                  </button>
                )
              })}
            </div>

            {clusters.length === 0 ? (
              <p className="text-sm text-gray-400 py-8 text-center">No skills match the selected filters</p>
            ) : view === 'graph' ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {clusters.map(c => <ClusterGraph key={c.category} cluster={c} />)}
              </div>
            ) : (
              <SkillList clusters={clusters} />
            )}
          </div>

          {/* Interview topics */}
          <div className="glass-card rounded-2xl p-6 mb-5">
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
                  <span className="text-xs text-gray-400 ml-auto text-right">{topic.reason}</span>
                </div>
              ))}
            </div>
          </div>

          {s.gaps > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-6 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-amber-700 font-medium">Skill gaps detected</p>
                <p className="text-xs text-gray-500 mt-1">
                  {s.gaps} required {s.gaps === 1 ? 'skill was' : 'skills were'} not found on the candidate's CV.
                  These are prioritised as high-priority interview topics.
                </p>
              </div>
            </div>
          )}

          <div className="flex justify-end pb-4">
            <button
              onClick={onNext}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 rounded-xl font-semibold text-white flex items-center gap-2 shadow-lg shadow-indigo-200 transition-all"
            >
              Generate Questions <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

function Header() {
  return (
    <div className="mb-8">
      <h2 className="text-2xl font-bold text-gray-900">Skill Graph Analysis</h2>
      <p className="text-gray-500 mt-1">
        Candidate skills and role requirements mapped onto the ESCO taxonomy
      </p>
    </div>
  )
}

/**
 * One category rendered as a hub-and-spoke graph: the category node on the
 * left, its skills stacked on the right, joined by curved edges.
 *
 * Height is derived from the number of skills, so nodes and labels can never
 * collide however many skills a category holds.
 */
function ClusterGraph({ cluster }) {
  const VB_W = 340        // viewBox width; the SVG scales to its container
  const ROW = 26          // vertical space per skill node
  const PAD = 14
  const HUB_X = 24
  const NODE_X = 104
  const LABEL_X = 116

  const n = cluster.skills.length
  const height = n * ROW + PAD * 2
  const hubY = height / 2

  return (
    <div className="border border-gray-200 rounded-xl bg-white/70 p-3">
      <div className="flex items-baseline gap-2 mb-1 px-1">
        <h4 className="text-xs font-semibold text-gray-700 truncate" title={cluster.category}>
          {cluster.category}
        </h4>
        <span className="text-[10px] text-gray-400 ml-auto flex-shrink-0">
          {n} {n === 1 ? 'skill' : 'skills'}
        </span>
      </div>

      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${VB_W} ${height}`}
        preserveAspectRatio="xMinYMid meet"
        role="img"
        aria-label={`${cluster.category}: ${cluster.skills.map(s => s.label).join(', ')}`}
      >
        {/* Edges first so nodes sit on top */}
        {cluster.skills.map((skill, i) => {
          const y = PAD + i * ROW + ROW / 2
          const midX = (HUB_X + NODE_X) / 2
          return (
            <path
              key={`e-${skill.id}`}
              d={`M ${HUB_X + 9} ${hubY} C ${midX} ${hubY}, ${midX} ${y}, ${NODE_X - 6} ${y}`}
              fill="none"
              stroke={STATUS[skill.status]?.color || '#94a3b8'}
              strokeOpacity="0.35"
              strokeWidth="1.4"
            />
          )
        })}

        {/* Category hub */}
        <circle cx={HUB_X} cy={hubY} r="9" fill="#4f46e5" fillOpacity="0.12" stroke="#4f46e5" strokeWidth="1.6" />
        <circle cx={HUB_X} cy={hubY} r="3" fill="#4f46e5" />

        {/* Skill nodes */}
        {cluster.skills.map((skill, i) => {
          const y = PAD + i * ROW + ROW / 2
          const color = STATUS[skill.status]?.color || '#94a3b8'
          return (
            <g key={skill.id}>
              <title>{`${skill.label} — ${STATUS[skill.status]?.hint || skill.status}`}</title>
              <circle cx={NODE_X} cy={y} r="5.5" fill={color} fillOpacity="0.22" stroke={color} strokeWidth="1.6" />
              <text
                x={LABEL_X}
                y={y}
                dominantBaseline="central"
                fontSize="11"
                fill="#374151"
                fontFamily="Inter, sans-serif"
              >
                {skill.label}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

function SkillList({ clusters }) {
  /* Regroup by status so the list answers "what's missing?" directly. */
  const byStatus = {}
  for (const c of clusters) {
    for (const s of c.skills) {
      (byStatus[s.status] ||= []).push({ ...s, category: c.category })
    }
  }

  return (
    <div className="space-y-4">
      {STATUS_ORDER.filter(k => byStatus[k]?.length).map(key => {
        const meta = STATUS[key]
        const items = byStatus[key].sort((a, b) => a.label.localeCompare(b.label))
        return (
          <div key={key}>
            <h4 className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: meta.color }} />
              {meta.label} ({items.length})
              <span className="font-normal text-gray-400">— {meta.hint}</span>
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {items.map(s => (
                <span
                  key={s.id}
                  title={s.category}
                  className="px-2.5 py-1 rounded-lg text-xs font-medium border"
                  style={{ color: meta.color, borderColor: `${meta.color}33`, background: `${meta.color}12` }}
                >
                  {s.label}
                </span>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function ViewToggle({ active, onClick, icon, label }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
        active ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
      }`}
    >
      {icon}{label}
    </button>
  )
}

function StatCard({ label, value, color }) {
  const colors = {
    indigo: 'text-indigo-600 bg-indigo-50 border-indigo-100',
    emerald: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    red: 'text-red-600 bg-red-50 border-red-100',
    violet: 'text-violet-600 bg-violet-50 border-violet-100',
    slate: 'text-slate-600 bg-slate-50 border-slate-200',
  }
  return (
    <div className={`${colors[color]} border rounded-2xl p-4 text-center`}>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  )
}
