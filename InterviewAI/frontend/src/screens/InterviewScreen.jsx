import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Room, RoomEvent } from 'livekit-client'
import {
  Mic, MicOff, Video, VideoOff, PhoneOff, Clock, MessageSquare,
  AlertTriangle, Eye, Activity, AudioLines, Bot, CheckCircle2,
  ScanFace, User,
} from 'lucide-react'
import axios from 'axios'
import { createVisionAnalyzer } from '../lib/vision'
import { createVoiceAnalyzer } from '../lib/voice'
import LandmarkOverlay from '../components/LandmarkOverlay'

export default function InterviewScreen({ mediaStream, sessionData, setSessionData, onEnd }) {
  const [connected, setConnected] = useState(false)
  const [countdown, setCountdown] = useState(3)
  const [currentQuestion, setCurrentQuestion] = useState('')
  const [interim, setInterim] = useState('')
  const [chatLog, setChatLog] = useState([])
  const [warning, setWarning] = useState('')
  const [tabSwitchCount, setTabSwitchCount] = useState(0)
  const [tabWarningVisible, setTabWarningVisible] = useState(false)
  const [micOn, setMicOn] = useState(true)
  const [camOn, setCamOn] = useState(true)
  const [showLandmarks, setShowLandmarks] = useState(true)
  const [elapsed, setElapsed] = useState(0)
  const [agentSpeaking, setAgentSpeaking] = useState(false)
  const [ending, setEnding] = useState(null)
  const [live, setLive] = useState({ attention: null, posture: null, voice: null })
  const [voiceInfo, setVoiceInfo] = useState({ provider: null, enabled: true })

  // Landmarks are held in a ref, not state: they arrive 5 times a second and
  // the overlay draws them on its own animation frame loop.
  const visionFrameRef = useRef(null)

  const videoRef = useRef(null)
  const roomRef = useRef(null)
  const chatEndRef = useRef(null)
  const timerRef = useRef(null)
  const speakingTimerRef = useRef(null)
  const visionRef = useRef(null)
  const voiceRef = useRef(null)
  const tabSwitchRef = useRef(0)
  const visibilityHandlerRef = useRef(null)
  const endedRef = useRef(false)

  const ready = connected && countdown <= 0

  /* ── Lifecycle ─────────────────────────────────────────────────────── */

  useEffect(() => {
    if (videoRef.current && mediaStream) videoRef.current.srcObject = mediaStream
    launchAndConnect()
    return () => {
      teardown()
      axios.post('/api/stop-interview').catch(() => {})
    }
  }, [])

  // 3 - 2 - 1 while the room connects in the background.
  useEffect(() => {
    if (countdown <= 0) return
    const t = setTimeout(() => setCountdown(c => c - 1), 800)
    return () => clearTimeout(t)
  }, [countdown])

  const teardown = () => {
    if (roomRef.current) { roomRef.current.disconnect(); roomRef.current = null }
    if (timerRef.current) clearInterval(timerRef.current)
    if (speakingTimerRef.current) clearTimeout(speakingTimerRef.current)
    visionRef.current?.stop()
    voiceRef.current?.stop()
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

  const launchAndConnect = async () => {
    try {
      // The setup screen already asked the server to warm LiveKit up, so
      // this usually returns immediately.
      await axios.post('/api/launch-interview')
      const { data } = await axios.get('/token')
      // The audio constraints are stated rather than left to the defaults.
      // Echo cancellation is what stops the agent's own voice, coming out of
      // the candidate's speakers, from being captured and treated as them
      // speaking — which cut the interviewer off mid-question.
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
        audioCaptureDefaults: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })
      roomRef.current = room

      room.on(RoomEvent.DataReceived, (payload) => {
        try { handleMessage(JSON.parse(new TextDecoder().decode(payload))) } catch { /* noise */ }
      })
      room.on(RoomEvent.TrackSubscribed, (track) => {
        if (track.kind === 'audio') {
          const el = track.attach()
          el.id = 'agent-audio'
          document.body.appendChild(el)
        }
      })
      room.on(RoomEvent.TrackUnsubscribed, (track) => {
        track.detach().forEach(el => el.remove())
      })
      room.on(RoomEvent.Disconnected, () => {
        setConnected(false)
        finish('disconnected')
      })

      await room.connect(data.url, data.token)

      if (mediaStream) {
        const micTrack = mediaStream.getAudioTracks()[0]
        const camTrack = mediaStream.getVideoTracks()[0]
        if (micTrack) await room.localParticipant.publishTrack(micTrack, { source: 'microphone' })
        if (camTrack) await room.localParticipant.publishTrack(camTrack, { source: 'camera' })
      }

      setConnected(true)
      setSessionData(prev => ({ ...prev, startTime: Date.now(), phase: 'greeting' }))
      timerRef.current = setInterval(() => setElapsed(p => p + 1), 1000)

      startVisionAnalysis()
      startVoiceAnalysis()
      startTabTracking()
    } catch (e) {
      console.error('Launch failed:', e)
      setCurrentQuestion('Connection failed: ' + e.message)
    }
  }

  /* ── Agent messages ────────────────────────────────────────────────── */

  const handleMessage = useCallback((msg) => {
    const stamp = (prev) => Math.floor((Date.now() - (prev.startTime || Date.now())) / 1000)

    switch (msg.type) {
      case 'agent_speech': {
        setCurrentQuestion(msg.text)
        setInterim('')
        setChatLog(prev => [...prev, { role: 'agent', text: msg.text, at: Date.now() }])
        setSessionData(prev => ({
          ...prev,
          transcript: [...prev.transcript, { role: 'agent', text: msg.text, time: stamp(prev) }],
          qCount: msg.q_count ?? prev.qCount,
          maxQuestions: msg.max_questions ?? prev.maxQuestions,
          phase: msg.phase || prev.phase,
        }))
        markAgentSpeaking(msg.text)
        break
      }
      case 'transcript': {
        setInterim(msg.text)
        if (msg.is_final && msg.text?.trim()) {
          setAgentSpeaking(false)
          setChatLog(prev => [...prev, { role: 'candidate', text: msg.text, at: Date.now() }])
          setSessionData(prev => ({
            ...prev,
            transcript: [...prev.transcript, { role: 'candidate', text: msg.text, time: stamp(prev) }],
          }))
        }
        break
      }
      case 'session_info':
        setVoiceInfo({ provider: msg.tts_provider, enabled: msg.voice_enabled })
        setSessionData(prev => ({ ...prev, maxQuestions: msg.max_questions ?? prev.maxQuestions }))
        if (!msg.voice_enabled) showWarning('Voice unavailable — questions will be shown as text only')
        break
      case 'wrap_up':
        showWarning(`Interview limit reached (${msg.reason}) — wrapping up`)
        setSessionData(prev => ({ ...prev, phase: 'closing' }))
        break
      case 'interview_ended':
        finish(msg.reason)
        break
      case 'warning':
        showWarning(msg.text)
        setSessionData(prev => ({
          ...prev,
          distractions: [...prev.distractions, { type: 'warning', text: msg.text, time: stamp(prev) }],
        }))
        break
    }
  }, [setSessionData])

  const markAgentSpeaking = (text) => {
    if (speakingTimerRef.current) clearTimeout(speakingTimerRef.current)
    const words = text.trim().split(/\s+/).length
    const seconds = Math.min(30, Math.max(2, words / 2.6))
    setTimeout(() => setAgentSpeaking(true), 450)
    speakingTimerRef.current = setTimeout(() => setAgentSpeaking(false), seconds * 1000 + 450)
  }

  const showWarning = (text) => {
    setWarning(text)
    setTimeout(() => setWarning(''), 4500)
  }

  const publishToAgent = (payload) => {
    try {
      roomRef.current?.localParticipant.publishData(
        new TextEncoder().encode(JSON.stringify(payload))
      )
    } catch { /* data channel not ready */ }
  }

  /* ── Telemetry ─────────────────────────────────────────────────────── */

  const lastDistractionRef = useRef(0)
  const distractionCountRef = useRef({})

  const reportDistraction = (type, detail) => {
    const now = Date.now()
    if (now - lastDistractionRef.current < 15000) return
    lastDistractionRef.current = now

    distractionCountRef.current[type] = (distractionCountRef.current[type] || 0) + 1
    const count = distractionCountRef.current[type]
    const severity = count >= 3 ? 'high' : count >= 2 ? 'medium' : 'low'

    setSessionData(prev => ({
      ...prev,
      distractions: [...prev.distractions, {
        type, detail, severity, count,
        time: Math.floor((Date.now() - (prev.startTime || Date.now())) / 1000),
      }],
    }))
    publishToAgent({ type: 'distraction', detail, severity, count })
  }

  const startVisionAnalysis = async () => {
    try {
      visionRef.current = await createVisionAnalyzer({
        video: videoRef.current,
        onFrame: (frame) => { visionFrameRef.current = frame },
        onSample: (sample) => {
          setLive(prev => ({ ...prev, attention: sample.attention, posture: sample.posture }))
          if (sample.calibrating) return
          setSessionData(prev => ({ ...prev, vision: [...(prev.vision || []), sample] }))
        },
        onEvent: (event) => reportDistraction(event.type, event.detail),
      })
      if (!visionRef.current) {
        console.info('[vision] unavailable — continuing without attention/posture')
      }
    } catch (err) {
      console.warn('[vision] failed to start:', err?.message)
    }
  }

  const startVoiceAnalysis = () => {
    try {
      voiceRef.current = createVoiceAnalyzer({
        stream: mediaStream,
        onSample: (sample) => {
          setLive(prev => ({ ...prev, voice: sample.rms }))
          setSessionData(prev => ({ ...prev, voice: [...(prev.voice || []), sample] }))
        },
      })
    } catch (err) {
      console.warn('[voice] failed to start:', err?.message)
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
            type: 'tab_switch', detail: `Tab switch #${count}`, severity, count,
            time: Math.floor((Date.now() - (prev.startTime || Date.now())) / 1000),
          }],
        }))
        publishToAgent({ type: 'distraction', detail: `Tab switch #${count}`, severity, count })
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

  /* ── Controls ──────────────────────────────────────────────────────── */

  const toggleMic = () => {
    const track = mediaStream?.getAudioTracks?.()[0]
    if (!track) return
    track.enabled = !track.enabled
    setMicOn(track.enabled)
  }

  const toggleCam = () => {
    const track = mediaStream?.getVideoTracks?.()[0]
    if (!track) return
    track.enabled = !track.enabled
    setCamOn(track.enabled)
  }

  const endInterview = () => {
    if (roomRef.current) roomRef.current.disconnect()
    else finish('candidate_request')
  }

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [chatLog, interim])

  const mins = Math.floor(elapsed / 60)
  const secs = elapsed % 60
  const qCount = sessionData.qCount || 0
  const maxQ = sessionData.maxQuestions || 15

  /* ── Render ────────────────────────────────────────────────────────── */

  return (
    <div className="h-screen w-full flex flex-col bg-[#16181c] text-white overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center gap-3 px-5 py-2.5 border-b border-white/10 flex-shrink-0">
        <span className="flex items-center gap-2 text-sm font-semibold">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-400 pulse-dot' : 'bg-red-400'}`} />
          Live Interview
        </span>
        <Pill icon={<MessageSquare className="w-3 h-3" />}>Question {qCount} / {maxQ}</Pill>
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

      {/* Stage + conversation */}
      <div className="flex-1 flex min-h-0 gap-3 p-3">
        {/* Main stage */}
        <div className="flex-1 flex flex-col gap-3 min-w-0">
          <div className="relative flex-1 rounded-2xl overflow-hidden bg-black border border-white/10 min-h-0">
            <video
              ref={videoRef}
              autoPlay playsInline muted
              className="w-full h-full object-cover -scale-x-100"
            />
            {showLandmarks && camOn && (
              <LandmarkOverlay frameRef={visionFrameRef} videoRef={videoRef} mirrored />
            )}

            {!camOn && (
              <div className="absolute inset-0 bg-[#24262b] flex flex-col items-center justify-center gap-3">
                <div className="w-24 h-24 rounded-full bg-white/10 flex items-center justify-center">
                  <User className="w-12 h-12 text-white/40" />
                </div>
                <p className="text-white/40 text-sm">Your camera is off</p>
              </div>
            )}

            {/* Name badge */}
            <div className="absolute bottom-3 left-3 flex items-center gap-2">
              <span className="text-xs bg-black/60 backdrop-blur px-2.5 py-1 rounded-md font-medium">You</span>
              {!micOn && (
                <span className="bg-red-600 p-1.5 rounded-md"><MicOff className="w-3 h-3" /></span>
              )}
            </div>

            {/* Interviewer tile */}
            <div className="absolute top-3 right-3 w-44 rounded-xl bg-[#2a2d33]/95 backdrop-blur border border-white/15 p-3 flex flex-col items-center gap-2 shadow-xl">
              <div className="relative">
                <div className={`w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center transition-transform ${agentSpeaking ? 'scale-110' : ''}`}>
                  <Bot className="w-7 h-7 text-white" />
                </div>
                {agentSpeaking && <span className="absolute inset-0 rounded-full border-2 border-indigo-400/70 animate-ping" />}
              </div>
              <p className="text-xs font-medium">AI Interviewer</p>
              <p className="text-[10px] text-white/40">
                {agentSpeaking ? 'Speaking…' : !voiceInfo.enabled ? 'Text only' : 'Listening'}
              </p>
            </div>
          </div>

          {/* Current question */}
          <div className="rounded-2xl bg-gradient-to-r from-indigo-600/20 to-violet-600/20 border border-indigo-400/25 px-5 py-4 flex-shrink-0">
            <p className="text-[10px] uppercase tracking-wide text-indigo-300 mb-1.5 flex items-center gap-1.5">
              <Bot className="w-3 h-3" /> Current question
            </p>
            <p className="text-base leading-relaxed text-white/95">
              {currentQuestion || 'Waiting for your interviewer…'}
            </p>
          </div>
        </div>

        {/* Conversation — always visible */}
        <aside className="w-[360px] flex-shrink-0 hidden lg:flex flex-col rounded-2xl bg-[#1f2126] border border-white/10 overflow-hidden">
          <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold">Conversation</h3>
            <span className="ml-auto text-[10px] text-white/30">{chatLog.length} messages</span>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {chatLog.length === 0 && (
              <p className="text-xs text-white/30 text-center py-8">
                The conversation will appear here as it happens.
              </p>
            )}

            {chatLog.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={msg.role === 'agent' ? '' : 'pl-6'}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  {msg.role === 'agent'
                    ? <Bot className="w-3 h-3 text-indigo-400" />
                    : <User className="w-3 h-3 text-emerald-400" />}
                  <span className={`text-[10px] font-medium ${msg.role === 'agent' ? 'text-indigo-300' : 'text-emerald-300'}`}>
                    {msg.role === 'agent' ? 'Interviewer' : 'You'}
                  </span>
                </div>
                <div className={`p-3 rounded-xl text-sm leading-relaxed ${
                  msg.role === 'agent'
                    ? 'bg-indigo-500/10 border border-indigo-400/20 text-white/85'
                    : 'bg-emerald-500/10 border border-emerald-400/20 text-white/90'
                }`}>
                  {msg.text}
                </div>
              </motion.div>
            ))}

            {/* Live partial transcript */}
            {interim && !agentSpeaking && (
              <div className="pl-6 opacity-60">
                <div className="flex items-center gap-1.5 mb-1">
                  <User className="w-3 h-3 text-emerald-400" />
                  <span className="text-[10px] font-medium text-emerald-300">You · speaking</span>
                </div>
                <div className="p-3 rounded-xl text-sm bg-white/5 border border-white/10 italic">
                  {interim}
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
        </aside>
      </div>

      {/* Controls */}
      <footer className="flex items-center justify-center gap-3 px-6 py-3.5 border-t border-white/10 flex-shrink-0 relative">
        <CircleButton onClick={toggleMic} danger={!micOn} title={micOn ? 'Mute' : 'Unmute'}>
          {micOn ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
        </CircleButton>
        <CircleButton onClick={toggleCam} danger={!camOn} title={camOn ? 'Turn camera off' : 'Turn camera on'}>
          {camOn ? <Video className="w-5 h-5" /> : <VideoOff className="w-5 h-5" />}
        </CircleButton>
        <CircleButton onClick={() => setShowLandmarks(v => !v)} active={showLandmarks}
          title={showLandmarks ? 'Hide tracking overlay' : 'Show tracking overlay'}>
          <ScanFace className="w-5 h-5" />
        </CircleButton>

        <button
          onClick={endInterview}
          className="ml-2 px-6 h-12 rounded-full bg-red-600 hover:bg-red-500 flex items-center gap-2 font-medium transition-colors"
        >
          <PhoneOff className="w-5 h-5" /> End
        </button>

        {live.voice !== null && live.voice !== undefined && (
          <span className="absolute right-6 flex items-center gap-1.5 text-xs text-white/40">
            <AudioLines className="w-3.5 h-3.5" />
            <span className="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
              <span className="block h-full bg-emerald-400 transition-all"
                style={{ width: `${Math.min(100, (live.voice || 0) * 1200)}%` }} />
            </span>
          </span>
        )}
      </footer>

      {/* Countdown / connecting */}
      <AnimatePresence>
        {!ready && !ending && (
          <motion.div
            initial={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.4 }}
            className="absolute inset-0 z-[150] bg-[#16181c] flex flex-col items-center justify-center gap-6"
          >
            {countdown > 0 ? (
              <motion.div
                key={countdown}
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 1.4, opacity: 0 }}
                className="w-32 h-32 rounded-full border-4 border-indigo-500/40 flex items-center justify-center"
              >
                <span className="text-6xl font-bold text-indigo-300">{countdown}</span>
              </motion.div>
            ) : (
              <div className="w-32 h-32 rounded-full border-4 border-indigo-500/40 border-t-indigo-400 animate-spin" />
            )}
            <div className="text-center">
              <p className="text-lg font-semibold">
                {countdown > 0 ? 'Your interview is about to begin' : 'Connecting to your interviewer…'}
              </p>
              <p className="text-sm text-white/40 mt-1">
                {connected ? 'Connected — starting now' : 'Setting up the secure session'}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Transient warning */}
      <AnimatePresence>
        {warning && (
          <motion.div
            initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
            className="absolute top-16 left-1/2 -translate-x-1/2 z-50 bg-red-500 text-white px-5 py-2.5 rounded-xl font-medium shadow-lg flex items-center gap-2"
          >
            <AlertTriangle className="w-4 h-4" /> {warning}
          </motion.div>
        )}
      </AnimatePresence>

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
                {tabSwitchCount >= 5
                  ? 'Repeated tab switching is recorded and will significantly affect your integrity score.'
                  : tabSwitchCount >= 3
                  ? 'This is being recorded and will affect your evaluation. Please remain on this tab.'
                  : 'Switching tabs during the interview is monitored. Please stay focused on this tab.'}
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
