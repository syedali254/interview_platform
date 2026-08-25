/**
 * Step 5, typed version. Same interview and same questions, answered in a
 * chat box. Produces the same transcript shape as the spoken version, so
 * everything after the interview works identically.
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, PhoneOff, Clock, MessageSquare, AlertTriangle, Eye, Activity,
  Bot, User, CheckCircle2, ScanFace, Video, VideoOff, Loader2, Keyboard,
} from 'lucide-react'
import axios from 'axios'
import { createVisionAnalyzer } from '../lib/vision'
import LandmarkOverlay from '../components/LandmarkOverlay'

/**
 * Typed interview mode.
 *
 * Deliberately the same session as the voice mode in every respect that
 * reaches the report: the same interviewer, the same question budget, the
 * same attention and posture tracking, the same tab-switch monitoring, and
 * the same transcript shape. Only the transport differs — answers are typed
 * and posted rather than spoken.
 *
 * Vocal delivery (M10) has no equivalent here, so it is simply absent. The
 * fusion engine renormalises the engagement weights over whichever presence
 * signals actually arrived, so a typed interview still produces a complete
 * report rather than one with a hole in it.
 */
export default function TextInterviewScreen({ mediaStream, setSessionData, onEnd }) {
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [thinking, setThinking] = useState(false)
  const [starting, setStarting] = useState(true)
  const [error, setError] = useState('')
  const [elapsed, setElapsed] = useState(0)
  const [tabSwitchCount, setTabSwitchCount] = useState(0)
  const [tabWarningVisible, setTabWarningVisible] = useState(false)
  const [ending, setEnding] = useState(null)
  const [camOn, setCamOn] = useState(true)
  const [showLandmarks, setShowLandmarks] = useState(true)
  const [live, setLive] = useState({ attention: null, posture: null })
  const [qInfo, setQInfo] = useState({ count: 0, max: 15 })

  const videoRef = useRef(null)
  const visionRef = useRef(null)
  const visionFrameRef = useRef(null)
  const timerRef = useRef(null)
  const scrollEndRef = useRef(null)
  const inputRef = useRef(null)
  const tabSwitchRef = useRef(0)
  const visibilityHandlerRef = useRef(null)
  const startedRef = useRef(false)
  const endedRef = useRef(false)

  // Typing telemetry — how the answer was produced, not just what it says.
  const typingRef = useRef({ keystrokes: 0, pasted: false, startedAt: null })

  /* ── Lifecycle ─────────────────────────────────────────────────────── */

  useEffect(() => {
    if (startedRef.current) return
    startedRef.current = true
    if (videoRef.current && mediaStream) videoRef.current.srcObject = mediaStream
    beginInterview()
    return teardown
  }, [])

  const teardown = () => {
    if (timerRef.current) clearInterval(timerRef.current)
    visionRef.current?.stop()
    if (visibilityHandlerRef.current) {
      document.removeEventListener('visibilitychange', visibilityHandlerRef.current)
      visibilityHandlerRef.current = null
    }
  }

  const finish = (reason) => {
    if (endedRef.current) return
    endedRef.current = true
    setEnding(reason || 'completed')
    teardown()
    setTimeout(onEnd, 2600)
  }

  const beginInterview = async () => {
    try {
      const { data } = await axios.post('/api/text-interview/start')
      const first = data.data
      setSessionData(prev => ({ ...prev, startTime: Date.now(), phase: 'greeting', mode: 'text' }))
      pushAgent(first)
      setStarting(false)
      timerRef.current = setInterval(() => setElapsed(p => p + 1), 1000)
      startVisionAnalysis()
      startTabTracking()
      setTimeout(() => inputRef.current?.focus(), 200)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
      setStarting(false)
    }
  }

  const stamp = (prev) => Math.floor((Date.now() - (prev.startTime || Date.now())) / 1000)

  const pushAgent = (payload) => {
    const text = payload.message
    setMessages(prev => [...prev, { role: 'agent', text }])
    setQInfo({ count: payload.q_count || 0, max: payload.max_questions || 15 })
    setSessionData(prev => ({
      ...prev,
      transcript: [...prev.transcript, { role: 'agent', text, time: stamp(prev) }],
      qCount: payload.q_count ?? prev.qCount,
      maxQuestions: payload.max_questions ?? prev.maxQuestions,
      phase: payload.finished ? 'closing' : 'interviewing',
    }))
    if (payload.finished) {
      // Let the closing line land before switching to the report.
      setTimeout(() => finish(payload.end_reason), 1600)
    }
  }

  const sendAnswer = async () => {
    const answer = draft.trim()
    if (!answer || thinking || ending) return

    const typing = typingRef.current
    setMessages(prev => [...prev, { role: 'candidate', text: answer }])
    setSessionData(prev => ({
      ...prev,
      transcript: [...prev.transcript, { role: 'candidate', text: answer, time: stamp(prev) }],
    }))
    setDraft('')
    setThinking(true)

    // A pasted answer is a genuine integrity signal in a typed interview.
    if (typing.pasted) {
      recordDistraction('paste', 'Answer contained pasted text')
    }
    typingRef.current = { keystrokes: 0, pasted: false, startedAt: null }

    try {
      const { data } = await axios.post('/api/text-interview/answer', { answer })
      pushAgent(data.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setThinking(false)
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  const endInterview = async () => {
    try {
      const { data } = await axios.post('/api/text-interview/end')
      if (data?.data?.message) {
        setMessages(prev => [...prev, { role: 'agent', text: data.data.message }])
      }
    } catch { /* closing anyway */ }
    finish('candidate_request')
  }

  /* ── Telemetry ─────────────────────────────────────────────────────── */

  const lastDistractionRef = useRef(0)
  const distractionCountRef = useRef({})

  const recordDistraction = (type, detail) => {
    const now = Date.now()
    if (type !== 'paste' && now - lastDistractionRef.current < 15000) return
    lastDistractionRef.current = now

    distractionCountRef.current[type] = (distractionCountRef.current[type] || 0) + 1
    const count = distractionCountRef.current[type]
    const severity = count >= 3 ? 'high' : count >= 2 ? 'medium' : 'low'

    setSessionData(prev => ({
      ...prev,
      distractions: [...prev.distractions, { type, detail, severity, count, time: stamp(prev) }],
    }))
  }

  const startVisionAnalysis = async () => {
    try {
      visionRef.current = await createVisionAnalyzer({
        video: videoRef.current,
        onFrame: (frame) => { visionFrameRef.current = frame },
        onSample: (sample) => {
          setLive({ attention: sample.attention, posture: sample.posture })
          if (sample.calibrating) return
          setSessionData(prev => ({ ...prev, vision: [...(prev.vision || []), sample] }))
        },
        onEvent: (event) => recordDistraction(event.type, event.detail),
      })
    } catch (err) {
      console.warn('[vision] failed to start:', err?.message)
    }
  }

  const startTabTracking = () => {
    const onVisibilityChange = () => {
      if (document.hidden) {
        tabSwitchRef.current += 1
        const count = tabSwitchRef.current
        setTabSwitchCount(count)
        const severity = count >= 5 ? 'high' : count >= 3 ? 'medium' : 'low'
        setSessionData(prev => ({
          ...prev,
          distractions: [...prev.distractions, {
            type: 'tab_switch', detail: `Tab switch #${count}`, severity, count, time: stamp(prev),
          }],
        }))
      } else {
        setTabWarningVisible(true)
        const count = tabSwitchRef.current
        setTimeout(() => setTabWarningVisible(false),
          count >= 5 ? 6000 : count >= 3 ? 4000 : 3000)
      }
    }
    visibilityHandlerRef.current = onVisibilityChange
    document.addEventListener('visibilitychange', onVisibilityChange)
  }

  const toggleCam = () => {
    const track = mediaStream?.getVideoTracks?.()[0]
    if (!track) return
    track.enabled = !track.enabled
    setCamOn(track.enabled)
  }

  /* ── Input handling ────────────────────────────────────────────────── */

  const onKeyDown = useCallback((e) => {
    typingRef.current.keystrokes++
    if (!typingRef.current.startedAt) typingRef.current.startedAt = Date.now()
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendAnswer()
    }
  }, [draft, thinking, ending])

  const onPaste = () => { typingRef.current.pasted = true }

  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  const mins = Math.floor(elapsed / 60)
  const secs = elapsed % 60

  /* ── Render ────────────────────────────────────────────────────────── */

  return (
    <div className="h-screen w-full flex flex-col bg-[#16181c] text-white overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center gap-3 px-5 py-2.5 border-b border-white/10 flex-shrink-0">
        <span className="flex items-center gap-2 text-sm font-semibold">
          <Keyboard className="w-4 h-4 text-indigo-400" />
          Text Interview
        </span>
        <Pill icon={<MessageSquare className="w-3 h-3" />}>Question {qInfo.count} / {qInfo.max}</Pill>
        <Pill icon={<Clock className="w-3 h-3" />}>{mins}:{secs.toString().padStart(2, '0')}</Pill>

        <div className="ml-auto flex items-center gap-2.5">
          <Meter icon={<Eye className="w-3.5 h-3.5" />} label="Attention" value={live.attention} />
          <Meter icon={<Activity className="w-3.5 h-3.5" />} label="Posture" value={live.posture} />
          {tabSwitchCount > 0 && (
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-400/30 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> {tabSwitchCount}
            </span>
          )}
        </div>
      </header>

      <div className="flex-1 flex min-h-0 gap-3 p-3">
        {/* Conversation — the main stage in this mode */}
        <div className="flex-1 flex flex-col min-w-0 rounded-2xl bg-[#1f2126] border border-white/10 overflow-hidden">
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {starting && (
              <div className="h-full flex flex-col items-center justify-center gap-3 text-white/40">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
                <p className="text-sm">Your interviewer is joining…</p>
              </div>
            )}

            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${msg.role === 'candidate' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.role === 'agent'
                    ? 'bg-gradient-to-br from-indigo-500 to-violet-600'
                    : 'bg-emerald-500/25 border border-emerald-400/30'
                }`}>
                  {msg.role === 'agent'
                    ? <Bot className="w-4 h-4 text-white" />
                    : <User className="w-4 h-4 text-emerald-300" />}
                </div>
                <div className={`max-w-[72%] ${msg.role === 'candidate' ? 'text-right' : ''}`}>
                  <p className={`text-[10px] mb-1 ${
                    msg.role === 'agent' ? 'text-indigo-300' : 'text-emerald-300'
                  }`}>
                    {msg.role === 'agent' ? 'Interviewer' : 'You'}
                  </p>
                  <div className={`inline-block p-3.5 rounded-2xl text-sm leading-relaxed text-left ${
                    msg.role === 'agent'
                      ? 'bg-indigo-500/10 border border-indigo-400/20 text-white/90'
                      : 'bg-emerald-500/10 border border-emerald-400/20 text-white/90'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              </motion.div>
            ))}

            {thinking && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="p-3.5 rounded-2xl bg-indigo-500/10 border border-indigo-400/20 flex items-center gap-1.5">
                  {[0, 1, 2].map(i => (
                    <span key={i} className="w-1.5 h-1.5 rounded-full bg-indigo-300 animate-bounce"
                          style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={scrollEndRef} />
          </div>

          {/* Composer */}
          <div className="border-t border-white/10 p-3">
            {error && (
              <p className="text-xs text-red-400 mb-2 px-1">{error}</p>
            )}
            <div className="flex items-end gap-2">
              <textarea
                ref={inputRef}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={onKeyDown}
                onPaste={onPaste}
                disabled={thinking || starting || Boolean(ending)}
                rows={2}
                placeholder={thinking ? 'Waiting for the interviewer…' : 'Type your answer, then press Enter to send'}
                className="flex-1 resize-none bg-[#16181c] border border-white/15 rounded-xl px-3.5 py-3 text-sm text-white/90 placeholder:text-white/25 focus:outline-none focus:border-indigo-400/60 disabled:opacity-50 max-h-40"
              />
              <button
                onClick={sendAnswer}
                disabled={!draft.trim() || thinking || starting || Boolean(ending)}
                title="Send answer"
                className="w-12 h-12 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center flex-shrink-0 transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            <p className="text-[10px] text-white/25 mt-1.5 px-1">
              Enter sends · Shift + Enter starts a new line
            </p>
          </div>
        </div>

        {/* Camera and controls */}
        <aside className="w-[300px] flex-shrink-0 hidden lg:flex flex-col gap-3">
          <div className="relative rounded-2xl overflow-hidden bg-black border border-white/10 aspect-[4/3]">
            <video ref={videoRef} autoPlay playsInline muted
                   className="w-full h-full object-cover -scale-x-100" />
            {showLandmarks && camOn && (
              <LandmarkOverlay frameRef={visionFrameRef} videoRef={videoRef} mirrored />
            )}
            {!camOn && (
              <div className="absolute inset-0 bg-[#24262b] flex items-center justify-center">
                <VideoOff className="w-9 h-9 text-white/30" />
              </div>
            )}
            <span className="absolute bottom-2 left-2 text-[10px] bg-black/60 backdrop-blur px-2 py-0.5 rounded">
              You
            </span>
          </div>

          <div className="rounded-2xl bg-[#1f2126] border border-white/10 p-4 text-xs text-white/50 space-y-2">
            <p className="text-white/70 font-medium text-sm mb-2">While you type</p>
            <p>Your attention and posture are tracked from the camera, exactly as in the voice interview.</p>
            <p>Tab switches and pasted answers are recorded and appear on your report.</p>
          </div>

          <div className="mt-auto flex items-center gap-2">
            <CircleButton onClick={toggleCam} danger={!camOn}
                          title={camOn ? 'Turn camera off' : 'Turn camera on'}>
              {camOn ? <Video className="w-5 h-5" /> : <VideoOff className="w-5 h-5" />}
            </CircleButton>
            <CircleButton onClick={() => setShowLandmarks(v => !v)} active={showLandmarks}
                          title={showLandmarks ? 'Hide tracking overlay' : 'Show tracking overlay'}>
              <ScanFace className="w-5 h-5" />
            </CircleButton>
            <button
              onClick={endInterview}
              className="flex-1 h-12 rounded-full bg-red-600 hover:bg-red-500 flex items-center justify-center gap-2 font-medium transition-colors"
            >
              <PhoneOff className="w-5 h-5" /> End
            </button>
          </div>
        </aside>
      </div>

      {/* Tab-switch overlay */}
      <AnimatePresence>
        {tabWarningVisible && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 z-[100] bg-black/75 flex items-center justify-center"
            onClick={() => setTabWarningVisible(false)}
          >
            <motion.div
              initial={{ scale: 0.85, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
              className="bg-white text-gray-900 rounded-2xl p-8 max-w-md mx-4 shadow-2xl text-center"
            >
              <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
                tabSwitchCount >= 5 ? 'bg-red-100' : tabSwitchCount >= 3 ? 'bg-orange-100' : 'bg-yellow-100'
              }`}>
                <AlertTriangle className={`w-8 h-8 ${
                  tabSwitchCount >= 5 ? 'text-red-600' : tabSwitchCount >= 3 ? 'text-orange-600' : 'text-yellow-600'
                }`} />
              </div>
              <h3 className="text-xl font-bold mb-2">
                {tabSwitchCount >= 5 ? 'Final warning'
                  : tabSwitchCount >= 3 ? 'Tab switching detected'
                  : 'Please stay on this tab'}
              </h3>
              <p className="text-2xl font-bold mb-2">Total switches: {tabSwitchCount}</p>
              <p className="text-gray-600 text-sm mb-4">
                Switching tabs during the interview is monitored and affects your integrity score.
              </p>
              <button
                onClick={() => setTabWarningVisible(false)}
                className="px-6 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm"
              >
                Continue interview
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Closing card */}
      <AnimatePresence>
        {ending && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="absolute inset-0 z-[200] bg-[#16181c] flex flex-col items-center justify-center gap-4"
          >
            <motion.div initial={{ scale: 0.8 }} animate={{ scale: 1 }}
              className="w-20 h-20 rounded-full bg-emerald-500/15 flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-emerald-400" />
            </motion.div>
            <h2 className="text-2xl font-bold">Thank you for your time</h2>
            <p className="text-white/60 text-sm">
              {ending === 'candidate_request'
                ? 'The interview was ended at your request.'
                : 'That completes the interview.'}
            </p>
            <p className="text-white/40 text-xs mt-2">Preparing your evaluation report…</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/* ── Small pieces ────────────────────────────────────────────────────── */

function Pill({ icon, children }) {
  return (
    <span className="px-2.5 py-1 rounded-full text-xs bg-white/10 text-white/70 flex items-center gap-1.5">
      {icon}{children}
    </span>
  )
}

function Meter({ icon, label, value }) {
  const has = value !== null && value !== undefined
  const pct = Math.round((value || 0) * 100)
  const colour = !has ? 'bg-white/20'
    : pct >= 70 ? 'bg-emerald-400'
    : pct >= 45 ? 'bg-amber-400'
    : 'bg-red-400'
  return (
    <span className="hidden md:flex items-center gap-1.5 text-xs text-white/45"
          title={has ? `${label}: ${pct}%` : `${label}: calibrating`}>
      {icon}
      <span className="w-14 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <span className={`block h-full ${colour} transition-all duration-500`}
              style={{ width: has ? `${pct}%` : '100%' }} />
      </span>
      <span className="w-8 tabular-nums">{has ? `${pct}%` : '···'}</span>
    </span>
  )
}

function CircleButton({ children, onClick, active, danger, title }) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
        danger ? 'bg-red-600 hover:bg-red-500'
          : active ? 'bg-indigo-500/80 hover:bg-indigo-500'
          : 'bg-white/10 hover:bg-white/20'
      }`}
    >
      {children}
    </button>
  )
}
