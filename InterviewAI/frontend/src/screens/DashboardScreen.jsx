import { useRef, useEffect, useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Clock, MessageCircle, AlertTriangle, RotateCw, TrendingUp, Activity,
  Loader2, ShieldCheck, Scale, Award, ChevronDown, RefreshCw, Eye, AudioLines,
  Download,
} from 'lucide-react'
import axios from 'axios'
import { summariseVision } from '../lib/vision'
import { summariseVoice } from '../lib/voice'

const RECOMMENDATION_STYLE = {
  strong_hire:  { bg: 'from-emerald-500 to-teal-500',   ring: 'text-emerald-600' },
  hire:         { bg: 'from-indigo-500 to-violet-500',  ring: 'text-indigo-600' },
  consider:     { bg: 'from-amber-500 to-orange-500',   ring: 'text-amber-600' },
  no_hire:      { bg: 'from-rose-500 to-red-500',       ring: 'text-rose-600' },
  disqualified: { bg: 'from-gray-700 to-gray-900',      ring: 'text-gray-700' },
}

const VERDICT_STYLE = {
  strong: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  weak:   'bg-amber-50 text-amber-700 border-amber-200',
  gap:    'bg-rose-50 text-rose-700 border-rose-200',
}

export default function DashboardScreen({ sessionData }) {
  /* Freeze the duration at mount — otherwise it ticks up while you read. */
  const [duration] = useState(() =>
    sessionData.startTime ? Math.floor((Date.now() - sessionData.startTime) / 1000) : 0
  )
  const [report, setReport] = useState(null)
  const [evalState, setEvalState] = useState('idle')  // idle | running | done | error
  const [evalError, setEvalError] = useState('')
  const [expandAll, setExpandAll] = useState(false)
  const startedRef = useRef(false)

  /**
   * Save as PDF through the browser's own print pipeline.
   *
   * Collapsed answer cards are expanded first, otherwise the PDF would omit
   * the per-answer detail that makes the report worth keeping. The print
   * stylesheet in globals.css strips the buttons and page chrome.
   */
  const downloadPdf = () => {
    setExpandAll(true)
    // Let React paint the expanded cards before the print dialog snapshots.
    setTimeout(() => {
      window.print()
      setExpandAll(false)
    }, 350)
  }

  const mins = Math.floor(duration / 60)
  const secs = duration % 60
  const candidateMsgs = sessionData.transcript.filter(t => t.role === 'candidate')

  /* ── Telemetry handed to M9 / M11 ────────────────────────────────── */
  const visionSummary = useMemo(() => summariseVision(sessionData.vision || []), [sessionData.vision])
  const voiceSummary = useMemo(() => summariseVoice(sessionData.voice || []), [sessionData.voice])

  const telemetry = useMemo(() => {
    const tabSwitches = sessionData.distractions.filter(d => d.type === 'tab_switch').length
    const otherEvents = sessionData.distractions.length - tabSwitches
    // Only used if the presence modules produced nothing.
    const fallbackEngagement = Math.max(0, Math.min(100, 100 - tabSwitches * 8 - otherEvents * 10))
    return {
      tab_switches: tabSwitches,
      distraction_count: sessionData.distractions.length,
      total_duration: duration || 300,
      duration_mins: Math.round((duration / 60) * 10) / 10,
      engagement_score: fallbackEngagement,
      vision: visionSummary,
      voice: voiceSummary,
    }
    }, [sessionData.distractions, duration, visionSummary, voiceSummary])

  const runEvaluation = async () => {
    setEvalState('running')
    setEvalError('')
    try {
      const res = await axios.post('/api/evaluate-session', {
        conversation: sessionData.transcript,
        telemetry,
      })
      setReport(res.data.data)
      setEvalState('done')
    } catch (e) {
      setEvalError(e.response?.data?.detail || e.message)
      setEvalState('error')
    }
  }

  useEffect(() => {
    if (startedRef.current) return
    startedRef.current = true
    if (sessionData.transcript.length >= 2) runEvaluation()
    else setEvalState('done')
  }, [])

  const qaPairs = useMemo(() => buildQaPairs(sessionData.transcript), [sessionData.transcript])

  return (
    <div className="h-screen overflow-y-auto gradient-bg print:h-auto print:overflow-visible">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 py-8 screen-enter print:max-w-none print:px-0">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
                    className="flex items-start gap-4 flex-wrap mb-8">
          <div className="flex-1 min-w-[260px]">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 border border-emerald-200 rounded-full text-xs text-emerald-600 mb-3">
              <span className="w-2 h-2 bg-emerald-500 rounded-full" />
              Interview Complete
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Interview Report</h1>
            <p className="text-gray-500 mt-1.5 text-sm">
              {new Date().toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              {' · '}{mins}m {secs}s · {sessionData.qCount} interviewer turns
            </p>
          </div>

          <div className="flex items-center gap-2 no-print">
            <button
              onClick={downloadPdf}
              disabled={!report}
              className="px-4 py-2.5 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-700 inline-flex items-center gap-2 shadow-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              title={report ? 'Save this report as a PDF' : 'Wait for scoring to finish'}
            >
              <Download className="w-4 h-4" /> Download PDF
            </button>
            <button
              onClick={() => location.reload()}
              className="px-4 py-2.5 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-600 inline-flex items-center gap-2 shadow-sm transition-all"
            >
              <RotateCw className="w-4 h-4" /> New Interview
            </button>
          </div>
        </motion.div>

        {/* ── Assessment ─────────────────────────────────────────────── */}
        {evalState === 'running' && <EvaluationRunning count={qaPairs.length} />}
        {evalState === 'error' && <EvaluationError message={evalError} onRetry={runEvaluation} />}
        {report && <Assessment report={report} expandAll={expandAll} />}

        {/* ── Session metrics ────────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
          <MetricCard icon={<MessageCircle className="w-5 h-5" />} value={qaPairs.length} label="Exchanges" color="indigo" />
          <MetricCard icon={<MessageCircle className="w-5 h-5" />} value={candidateMsgs.length} label="Answers" color="emerald" />
          <MetricCard icon={<Clock className="w-5 h-5" />} value={`${mins}m ${secs}s`} label="Duration" color="amber" />
          <MetricCard icon={<AlertTriangle className="w-5 h-5" />} value={sessionData.distractions.length} label="Distractions" color="red" />
        </div>

        <Card title="Interview Transcript" icon={<MessageCircle className="w-4 h-4 text-indigo-500" />}>
          <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
            {qaPairs.length > 0 ? qaPairs.map((qa, i) => (
              <TranscriptPair key={i} qa={qa} index={i} />
            )) : <Empty>No transcript recorded</Empty>}
          </div>
        </Card>

        <Card title="Distraction Events" icon={<AlertTriangle className="w-4 h-4 text-red-500" />}>
          {sessionData.distractions.length > 0 ? (
            <div className="space-y-2">
              {sessionData.distractions.map((ev, i) => {
                const sev = ev.severity || 'low'
                const sevColor = sev === 'high' ? 'bg-red-100 border-red-200 text-red-700'
                  : sev === 'medium' ? 'bg-amber-100 border-amber-200 text-amber-700'
                  : 'bg-gray-100 border-gray-200 text-gray-600'
                return (
                  <div key={i} className="flex items-center gap-3 p-2.5 bg-red-50/50 border border-red-100 rounded-xl">
                    <span className="text-xs text-gray-400 min-w-[50px] font-mono">{ev.time != null ? fmtTime(ev.time) : ''}</span>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase border ${sevColor}`}>{sev}</span>
                    <span className="text-sm text-gray-600">{ev.detail || ev.text || ev.type}</span>
                    {ev.count > 1 && (
                      <span className="text-[10px] text-gray-400 ml-auto">{ev.count} times</span>
                    )}
                  </div>
                )
              })}
            </div>
          ) : <p className="text-sm text-emerald-600">No distractions detected — excellent focus! 🎯</p>}
        </Card>

        <p className="text-center text-xs text-gray-400 pb-8">
          Generated by InterviewAI · scores are explained in full in the project documentation
        </p>
      </div>
    </div>
  )
}

/* ══ Assessment ═════════════════════════════════════════════════════ */

function Assessment({ report, expandAll }) {
  const style = RECOMMENDATION_STYLE[report.recommendation] || RECOMMENDATION_STYLE.consider
  const fusion = report.fusion || {}
  const reliability = report.judge_reliability || {}

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      {/* Headline recommendation */}
      <div className={`rounded-2xl p-6 mb-6 text-white bg-gradient-to-r ${style.bg} shadow-lg`}>
        <div className="flex items-center gap-6 flex-wrap">
          <div>
            <p className="text-xs uppercase tracking-wide opacity-80">Recommendation</p>
            <p className="text-2xl font-bold mt-0.5">{report.label}</p>
            <p className="text-xs opacity-80 mt-1 capitalize">{report.confidence} confidence</p>
          </div>
          <div className="ml-auto flex items-center gap-6">
            <div className="text-center">
              <p className="text-4xl font-bold">{report.overall_score}</p>
              <p className="text-[10px] uppercase tracking-wide opacity-80">Answer score</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold">{fusion.fusion_score ?? '—'}</p>
              <p className="text-[10px] uppercase tracking-wide opacity-80">Fused score</p>
            </div>
          </div>
        </div>
        <p className="text-sm opacity-95 mt-4 border-t border-white/25 pt-3">{report.summary_text}</p>
      </div>

      {/* Fusion weights — M11 */}
      <Card title="Score Breakdown (M11)" icon={<Scale className="w-4 h-4 text-indigo-500" />}>
        <div className="space-y-3.5">
          {Object.entries(fusion.components || {}).map(([key, comp]) => (
            <ScoreBar key={key} label={key.replace(/_/g, ' ')} value={comp.score} size="lg" />
          ))}
        </div>
        {(fusion.strengths?.length > 0 || fusion.concerns?.length > 0) && (
          <div className="grid md:grid-cols-2 gap-4 mt-5">
            <TagList title="Strengths" items={fusion.strengths} tone="emerald" />
            <TagList title="Concerns" items={fusion.concerns} tone="rose" />
          </div>
        )}
      </Card>

      {/* Presence — M7 / M8 / M10 */}
      <PresencePanel
        vision={fusion.vision_summary}
        voice={fusion.voice_summary}
        engagement={fusion.components?.engagement?.breakdown}
      />

      {/* Integrity — M9 */}
      {report.integrity && <IntegrityPanel integrity={report.integrity} />}

      {/* Judge self-consistency — how much to trust these scores */}
      <Card title="Scoring Reliability (M6)" icon={<Award className="w-4 h-4 text-violet-500" />}>
        <p className="text-xs text-gray-500 mb-4">
          Every answer is scored twice with the rubric criteria in a different order,
          to counter the positional bias LLM judges are known for. A small spread
          between the two scores means the judgement was stable.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <Stat label="Answers scored" value={reliability.n ?? 0} />
          <Stat label="Mean spread" value={fmtNum(reliability.mean_spread)} />
          <Stat label="Max spread" value={fmtNum(reliability.max_spread)} />
          <Stat label="Flagged" value={reliability.flagged_for_review ?? 0} />
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          {Object.entries(reliability.consistency_distribution || {}).map(([level, count]) => (
            <span key={level} className={`px-2.5 py-1 rounded-lg border ${
              level === 'high' ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
              : level === 'moderate' ? 'bg-amber-50 border-amber-200 text-amber-700'
              : 'bg-rose-50 border-rose-200 text-rose-700'
            }`}>
              {level} consistency: {count}
            </span>
          ))}
        </div>
        {reliability.note && <p className="text-xs text-gray-400 mt-3 italic">{reliability.note}</p>}
      </Card>

      {/* Per-skill */}
      {report.breakdown?.length > 0 && (
        <Card title="Skill Breakdown" icon={<TrendingUp className="w-4 h-4 text-indigo-500" />}>
          <div className="space-y-2">
            {report.breakdown.map(s => (
              <div key={s.skill} className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                <ScoreBar
                  label={s.skill}
                  value={s.avg_score}
                  size="lg"
                  note={`${s.questions_answered} ${s.questions_answered === 1 ? 'answer' : 'answers'}`}
                />
              </div>
            ))}
          </div>
          {report.skill_states?.never_probed?.length > 0 && (
            <p className="text-xs text-gray-400 mt-3">
              Not covered in this interview: {report.skill_states.never_probed.join(', ')}
            </p>
          )}
        </Card>
      )}

      {/* Per-answer detail */}
      {report.answers?.length > 0 && (
        <Card title="Answer-by-Answer Evaluation" icon={<MessageCircle className="w-4 h-4 text-indigo-500" />}>
          <div className="space-y-3">
            {report.answers.map((a, i) => (
              <AnswerCard key={i} answer={a} index={i} forceOpen={expandAll} />
            ))}
          </div>
        </Card>
      )}
    </motion.div>
  )
}

function PresencePanel({ vision, voice, engagement }) {
  if (!vision && !voice) {
    return (
      <Card title="Presence — Attention, Posture & Voice (M7 / M8 / M10)"
            icon={<Eye className="w-4 h-4 text-sky-500" />}>
        <Empty>
          No attention, posture or voice data was captured for this session — the
          engagement component fell back to an estimate from distraction events.
        </Empty>
      </Card>
    )
  }

  const pct = (v) => (v === null || v === undefined ? null : Math.round(v * 100))

  return (
    <Card title="Presence — Attention, Posture & Voice (M7 / M8 / M10)"
          icon={<Eye className="w-4 h-4 text-sky-500" />}>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        {vision?.avg_attention !== undefined && vision?.avg_attention !== null && (
          <Stat label="Avg attention" value={`${pct(vision.avg_attention)}%`} />
        )}
        {vision?.avg_posture !== undefined && vision?.avg_posture !== null && (
          <Stat label="Avg posture" value={`${pct(vision.avg_posture)}%`} />
        )}
        {vision?.looking_away_ratio !== undefined && (
          <Stat label="Looked away" value={`${pct(vision.looking_away_ratio)}%`} />
        )}
        {voice?.vocal_confidence !== undefined && (
          <Stat label="Vocal confidence" value={voice.vocal_confidence} />
        )}
      </div>

      {engagement && (
        <div className="bg-gray-50 border border-gray-100 rounded-xl p-3 mb-4">
          <p className="text-xs font-semibold text-gray-600 mb-2">
            What the engagement score is made of
            {!engagement.measured && ' (estimated — presence modules produced no data)'}
          </p>
          <div className="space-y-2.5">
            {Object.entries(engagement.sources || {}).map(([key, value]) => (
              <ScoreBar key={key} label={key} value={value} size="sm" tone="sky" />
            ))}
          </div>
          <p className="text-[11px] text-gray-500 mt-2">
            Combined engagement <strong className="text-gray-700">{engagement.score}%</strong>
            {engagement.distraction_penalty > 0 &&
              ` — reduced from ${engagement.before_penalty}% after distraction events`}
          </p>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-4">
        {voice && (
          <div className="border border-violet-100 bg-violet-50/40 rounded-xl p-3">
            <p className="text-xs font-semibold text-violet-700 mb-2 flex items-center gap-1.5">
              <AudioLines className="w-3.5 h-3.5" /> Vocal delivery
            </p>
            <div className="space-y-2.5">
              {Object.entries(voice.components || {}).map(([k, v]) => (
                <ScoreBar key={k} label={k} value={v * 100} size="sm" tone="violet" />
              ))}
            </div>
            <p className="text-[10px] text-gray-400 mt-2">
              Mean pitch {voice.avg_pitch_hz ?? '—'} Hz · variability {voice.pitch_variability ?? '—'} Hz
              {' · '}{voice.long_pauses ?? 0} long pauses
            </p>
            {voice.indicators?.length > 0 && (
              <ul className="mt-2 space-y-1">
                {voice.indicators.map((ind, i) => (
                  <li key={i} className="text-[11px] text-amber-700">• {ind}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {vision && (
          <div className="border border-sky-100 bg-sky-50/40 rounded-xl p-3">
            <p className="text-xs font-semibold text-sky-700 mb-2 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" /> Attention & posture
            </p>
            <p className="text-[11px] text-gray-600">
              {vision.samples} samples · lowest attention {pct(vision.min_attention)}%
              {' · '}blink rate {vision.avg_blink_rate}/min
            </p>
            {vision.posture_flags?.length > 0 ? (
              <ul className="mt-2 space-y-1">
                {vision.posture_flags.map((f, i) => (
                  <li key={i} className="text-[11px] text-amber-700">
                    • {f.flag} — {Math.round(f.ratio * 100)}% of the session
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-[11px] text-emerald-600 mt-2">Posture stable throughout.</p>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}

function IntegrityPanel({ integrity }) {
  const tone = integrity.verdict === 'normal' ? 'emerald'
    : integrity.verdict === 'suspicious' ? 'amber' : 'rose'
  const toneClass = {
    emerald: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    amber: 'bg-amber-50 border-amber-200 text-amber-700',
    rose: 'bg-rose-50 border-rose-200 text-rose-700',
  }[tone]

  return (
    <Card title="Behavioural Integrity (M9)" icon={<ShieldCheck className="w-4 h-4 text-emerald-500" />}>
      <div className="flex items-center gap-4 flex-wrap mb-4">
        <span className={`px-3 py-1.5 rounded-lg text-sm font-semibold border capitalize ${toneClass}`}>
          {integrity.verdict}
        </span>
        <span className="text-sm text-gray-600">
          Integrity score <strong className="text-gray-900">{integrity.integrity_score}</strong>/100
        </span>
        <span className="text-xs text-gray-400">
          Isolation Forest anomaly score {integrity.anomaly_score}
        </span>
      </div>

      {integrity.risk_factors?.length > 0 ? (
        <ul className="space-y-1.5 mb-4">
          {integrity.risk_factors.map((rf, i) => (
            <li key={i} className="text-sm text-amber-700 flex items-start gap-2">
              <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />{rf}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-emerald-600 mb-4">No behavioural risk factors detected.</p>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {Object.entries(integrity.features || {}).map(([key, value]) => (
          <div key={key} className="bg-gray-50 border border-gray-100 rounded-lg p-2">
            <p className="text-[10px] text-gray-400 capitalize">{key.replace(/_/g, ' ')}</p>
            <p className="text-sm font-semibold text-gray-700">{value}</p>
          </div>
        ))}
      </div>
    </Card>
  )
}

function AnswerCard({ answer, index, forceOpen }) {
  const [open, setOpen] = useState(false)
  const isOpen = open || forceOpen
  const verdictClass = VERDICT_STYLE[answer.verdict] || 'bg-gray-50 text-gray-600 border-gray-200'
  const judge = answer.judge || {}

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left print:hover:bg-gray-50"
      >
        <span className="text-[10px] font-bold text-gray-400 uppercase w-7">Q{index + 1}</span>
        <span className="text-sm text-gray-700 flex-1 truncate">{answer.question}</span>
        {answer.skill && (
          <span className="text-[10px] px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-600 border border-indigo-100 hidden sm:inline">
            {answer.skill}
          </span>
        )}
        {answer.flagged && (
          <span className="text-[10px] px-2 py-0.5 rounded-md bg-amber-100 text-amber-700 border border-amber-200">
            review
          </span>
        )}
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-md border capitalize ${verdictClass}`}>
          {answer.final_score != null ? answer.final_score : '—'}
        </span>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform no-print ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="p-4 bg-white space-y-4">
          <Field label="Candidate answer">{answer.answer}</Field>
          {answer.reference_answer && <Field label="Reference answer">{answer.reference_answer}</Field>}

          <div className="border border-indigo-100 bg-indigo-50/40 rounded-xl p-3">
            <p className="text-xs font-semibold text-indigo-700 mb-2">
              Rubric breakdown — <span className="font-bold">{fmtNum(judge.score)}%</span> overall
            </p>
            {judge.criterion_scores && (
              <div className="space-y-2.5">
                {Object.entries(judge.criterion_scores).map(([k, v]) => (
                  <ScoreBar key={k} label={k.replace(/_/g, ' ')} value={(v / 25) * 100}
                            size="sm" tone="indigo" />
                ))}
              </div>
            )}
            {judge.feedback && <p className="text-[11px] text-gray-500 mt-2 leading-relaxed">{judge.feedback}</p>}
          </div>

          {judge.call_scores && (
            <p className="text-xs text-gray-500">
              Scored twice under different rubric orderings:{' '}
              <strong>{judge.call_scores.join(' and ')}</strong>
              {' — spread '}<strong>{judge.spread}</strong> points,{' '}
              <span className="capitalize">{judge.consistency}</span> consistency
              {answer.flagged && ' · flagged for human review'}
            </p>
          )}
          {answer.note && <p className="text-xs text-gray-400 italic">{answer.note}</p>}
          {answer.error && <p className="text-xs text-rose-600">Evaluation failed: {answer.error}</p>}
        </div>
      )}
    </div>
  )
}

/* ══ Small pieces ═══════════════════════════════════════════════════ */

function EvaluationRunning({ count }) {
  return (
    <div className="glass-card rounded-2xl p-8 mb-6 flex flex-col items-center text-center">
      <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-3" />
      <p className="font-semibold text-gray-800">Evaluating answers</p>
      <p className="text-sm text-gray-500 mt-1">
        Scoring {count} {count === 1 ? 'exchange' : 'exchanges'} against generated reference answers —
        this takes up to a minute.
      </p>
    </div>
  )
}

function EvaluationError({ message, onRetry }) {
  return (
    <div className="bg-rose-50 border border-rose-200 rounded-2xl p-5 mb-6 flex items-start gap-3">
      <AlertTriangle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="text-sm font-medium text-rose-700">Evaluation failed</p>
        <p className="text-xs text-gray-600 mt-1 break-words">{message}</p>
      </div>
      <button
        onClick={onRetry}
        className="px-3 py-1.5 bg-white border border-rose-200 rounded-lg text-xs font-medium text-rose-600 inline-flex items-center gap-1.5 flex-shrink-0"
      >
        <RefreshCw className="w-3 h-3" /> Retry
      </button>
    </div>
  )
}

function TranscriptPair({ qa, index }) {
  const qTime = qa.qTime != null ? fmtTime(qa.qTime) : ''
  const aTime = qa.aTime != null ? fmtTime(qa.aTime) : ''
  const responseTime = (qa.qTime != null && qa.aTime != null) ? qa.aTime - qa.qTime : null

  return (
    <div className="border border-gray-100 rounded-xl overflow-hidden">
      <div className="bg-indigo-50 border-b border-indigo-100 p-3">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] font-bold text-indigo-500 uppercase">Q{index + 1}</span>
          {qTime && <span className="text-[10px] text-gray-400">⏱ {qTime}</span>}
        </div>
        <p className="text-sm text-gray-700">{qa.question}</p>
      </div>
      {qa.answer ? (
        <div className="bg-white p-3">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold text-emerald-500 uppercase">Answer</span>
            {aTime && <span className="text-[10px] text-gray-400">⏱ {aTime}</span>}
            {responseTime != null && (
              <span className="text-[10px] text-gray-400 ml-auto">Response: {responseTime}s</span>
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
}

/**
 * The one bar used across the whole report.
 *
 * Two sizes only — `lg` for a section's headline figures, `sm` for the
 * nested detail inside a card. Everything else on the page reuses these, so
 * a percentage always reads the same way wherever it appears.
 */
function ScoreBar({ label, value, size = 'lg', tone = 'auto', note }) {
  const pct = Math.max(0, Math.min(100, Math.round(value ?? 0)))

  const fill = tone === 'auto'
    ? (pct >= 70 ? 'bg-gradient-to-r from-emerald-400 to-emerald-500'
      : pct >= 40 ? 'bg-gradient-to-r from-amber-400 to-amber-500'
      : 'bg-gradient-to-r from-rose-400 to-rose-500')
    : tone === 'indigo' ? 'bg-gradient-to-r from-indigo-400 to-violet-500'
    : tone === 'sky' ? 'bg-gradient-to-r from-sky-400 to-sky-500'
    : tone === 'violet' ? 'bg-gradient-to-r from-violet-400 to-violet-500'
    : 'bg-gray-400'

  const big = size === 'lg'

  return (
    <div className={`flex items-center ${big ? 'gap-4' : 'gap-3'}`}>
      <span className={`text-gray-600 capitalize truncate ${big ? 'text-sm w-48' : 'text-xs w-36'}`}
            title={label}>
        {label}
      </span>
      <div className={`flex-1 bg-gray-100 rounded-full overflow-hidden ${big ? 'h-4' : 'h-2.5'}`}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
          className={`h-full rounded-full ${fill}`}
        />
      </div>
      <span className={`font-semibold text-gray-800 text-right tabular-nums ${big ? 'text-sm w-14' : 'text-xs w-11'}`}>
        {pct}%
      </span>
      {note && <span className="text-[11px] text-gray-400 w-24 text-right hidden lg:block">{note}</span>}
    </div>
  )
}

function Card({ title, icon, children }) {
  return (
    <div className="glass-card rounded-2xl p-6 mb-6">
      <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">{icon} {title}</h3>
      {children}
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">{label}</p>
      <p className="text-sm text-gray-700 leading-relaxed">{children}</p>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="bg-gray-50 border border-gray-100 rounded-xl p-3 text-center">
      <p className="text-lg font-bold text-gray-800">{value}</p>
      <p className="text-[10px] text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}

function TagList({ title, items, tone }) {
  if (!items?.length) return null
  const cls = tone === 'emerald'
    ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
    : 'bg-rose-50 border-rose-200 text-rose-700'
  return (
    <div>
      <p className="text-xs font-semibold text-gray-600 mb-2">{title}</p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => (
          <span key={i} className={`px-2.5 py-1 rounded-lg text-xs border ${cls}`}>{item}</span>
        ))}
      </div>
    </div>
  )
}

function Empty({ children }) {
  return <p className="text-sm text-gray-400">{children}</p>
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


/* ══ Helpers ════════════════════════════════════════════════════════ */

function buildQaPairs(transcript) {
  const pairs = []
  let current = null
  for (const msg of transcript) {
    if (msg.role === 'agent') {
      if (current) pairs.push(current)
      current = { question: msg.text, answer: null, qTime: msg.time, aTime: null }
    } else if (msg.role === 'candidate' && current) {
      current.answer = current.answer ? `${current.answer} ${msg.text}` : msg.text
      current.aTime = msg.time
    }
  }
  if (current) pairs.push(current)
  return pairs
}

function fmtTime(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function fmtNum(value) {
  return value === null || value === undefined ? '—' : value
}
