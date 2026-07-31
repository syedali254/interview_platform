import { useState, useEffect, useRef, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Room, RoomEvent } from 'livekit-client'
import { Mic, PhoneOff, Clock, MessageCircle, AlertTriangle } from 'lucide-react'
import axios from 'axios'

export default function InterviewScreen({ mediaStream, sessionData, setSessionData, onEnd }) {
  const [connected, setConnected] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState('Connecting...')
  const [transcript, setTranscript] = useState('Waiting for speech...')
  const [chatLog, setChatLog] = useState([])
  const [warning, setWarning] = useState('')
  const [emotion, setEmotion] = useState('neutral')
  const videoRef = useRef(null)
  const roomRef = useRef(null)
  const chatEndRef = useRef(null)
  const timerRef = useRef(null)
  const emotionRef = useRef(null)
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (videoRef.current && mediaStream) {
      videoRef.current.srcObject = mediaStream
    }
    launchAndConnect()
    return () => {
      if (roomRef.current) roomRef.current.disconnect()
      if (timerRef.current) clearInterval(timerRef.current)
      if (emotionRef.current) clearInterval(emotionRef.current)
    }
  }, [])

  const launchAndConnect = async () => {
    try {
      await axios.post('/api/launch-interview')
      const { data } = await axios.get('/token')
      const room = new Room({ adaptiveStream: true, dynacast: true })
      roomRef.current = room

      room.on(RoomEvent.DataReceived, (payload) => {
        try {
          const msg = JSON.parse(new TextDecoder().decode(payload))
          handleMessage(msg)
        } catch(e) {}
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
        setTimeout(onEnd, 2000)
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

      timerRef.current = setInterval(() => {
        setElapsed(prev => prev + 1)
      }, 1000)

      startEmotionDetection()
      startDistractionDetection(room)

    } catch (e) {
      console.error('Launch failed:', e)
      setCurrentQuestion('Connection failed: ' + e.message)
    }
  }

  const handleMessage = useCallback((msg) => {
    switch (msg.type) {
      case 'agent_speech':
        setCurrentQuestion(msg.text)
        setChatLog(prev => [...prev, { role: 'agent', text: msg.text }])
        setSessionData(prev => ({
          ...prev,
          transcript: [...prev.transcript, { role: 'agent', text: msg.text, time: Math.floor((Date.now() - (prev.startTime || Date.now())) / 1000) }],
          qCount: msg.q_count || prev.qCount,
          phase: msg.phase || prev.phase,
        }))
        break
      case 'transcript':
        setTranscript(msg.text)
        if (msg.is_final && msg.text?.trim()) {
          setChatLog(prev => [...prev, { role: 'candidate', text: msg.text }])
          setSessionData(prev => ({
            ...prev,
            transcript: [...prev.transcript, { role: 'candidate', text: msg.text, time: Math.floor((Date.now() - (prev.startTime || Date.now())) / 1000) }],
          }))
        }
        break
      case 'warning':
        showWarning(msg.text)
        setSessionData(prev => ({
          ...prev,
          distractions: [...prev.distractions, { type: 'warning', text: msg.text, time: Math.floor((Date.now() - (prev.startTime || Date.now())) / 1000) }],
        }))
        break
    }
  }, [setSessionData])

  const showWarning = (text) => {
    setWarning(text)
    setTimeout(() => setWarning(''), 4000)
  }

  const lastDistractionRef = useRef(0)
  const reportDistraction = (type, detail) => {
    const now = Date.now()
    if (now - lastDistractionRef.current < 5000) return
    lastDistractionRef.current = now
    setSessionData(prev => ({
      ...prev,
      distractions: [...prev.distractions, { type, detail, time: Math.floor((Date.now() - (prev.startTime || Date.now())) / 1000) }]
    }))
    if (roomRef.current) {
      try {
        roomRef.current.localParticipant.publishData(
          new TextEncoder().encode(JSON.stringify({ type: 'distraction', detail, severity: 'medium' }))
        )
      } catch(e) {}
    }
  }

  const modelsLoadedRef = useRef(false)
  const noFaceCountRef = useRef(0)

  const startEmotionDetection = async () => {
    const faceapi = window.faceapi
    if (!faceapi) {
      console.warn('face-api.js not loaded, retrying in 3s...')
      setTimeout(() => startEmotionDetection(), 3000)
      return
    }
    const MODEL_URL = 'https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/weights'
    try {
      await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL)
      await faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL)
      modelsLoadedRef.current = true
      console.log('Face-api models loaded successfully')
    } catch (e) {
      console.warn('Failed to load face-api models:', e)
      return
    }

    emotionRef.current = setInterval(async () => {
      if (!modelsLoadedRef.current) return
      try {
        const video = videoRef.current
        if (!video || video.readyState < 2 || video.videoWidth === 0) return
        const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.4 }))
          .withFaceExpressions()
        if (detections.length === 0) {
          noFaceCountRef.current++
          // Only report distraction after 5 consecutive misses (10+ seconds)
          if (noFaceCountRef.current >= 5) {
            setEmotion('no_face')
            if (noFaceCountRef.current === 5) {
              reportDistraction('no_face', 'No face detected for extended period')
            }
          }
          return
        }
        noFaceCountRef.current = 0
        if (detections.length > 1) {
          reportDistraction('multi_face', 'Multiple faces detected')
        }
        const expr = detections[0].expressions
        const dominant = Object.entries(expr).sort((a, b) => b[1] - a[1])[0]
        setEmotion(dominant[0])
        setSessionData(prev => ({
          ...prev,
          emotions: [...prev.emotions, { time: Math.floor((Date.now() - (prev.startTime || Date.now())) / 1000), emotion: dominant[0], confidence: Math.round(dominant[1] * 100) }]
        }))
      } catch (e) { /* ignore single frame failures */ }
    }, 2000)
  }

  const startDistractionDetection = (room) => {
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        reportDistraction('tab_switch', 'Switched tabs')
        showWarning('Please stay on this tab during the interview')
      }
    })
    window.addEventListener('blur', () => reportDistraction('window_blur', 'Window lost focus'))
  }

  const endInterview = () => {
    if (roomRef.current) roomRef.current.disconnect()
    else onEnd()
  }

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatLog])

  const mins = Math.floor(elapsed / 60)
  const secs = elapsed % 60

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Warning banner */}
      {warning && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute top-16 left-1/2 -translate-x-1/2 z-50 bg-red-500 text-white px-6 py-3 rounded-xl font-semibold shadow-lg flex items-center gap-2"
        >
          <AlertTriangle className="w-4 h-4" /> {warning}
        </motion.div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-200 shadow-sm">
        <h2 className="text-sm font-semibold text-indigo-600">Live Interview</h2>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 bg-indigo-50 border border-indigo-100 rounded-full text-xs text-indigo-600 capitalize">
            {sessionData.phase}
          </span>
          <span className="px-3 py-1 bg-amber-50 border border-amber-100 rounded-full text-xs text-amber-700 flex items-center gap-1">
            <Clock className="w-3 h-3" /> {mins}:{secs.toString().padStart(2, '0')}
          </span>
          <span className={`px-3 py-1 rounded-full text-xs flex items-center gap-1 ${connected ? 'bg-emerald-50 border border-emerald-100 text-emerald-600' : 'bg-red-50 border border-red-100 text-red-600'}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-500 pulse-dot' : 'bg-red-400'}`} />
            {connected ? 'Connected' : 'Connecting'}
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 flex gap-4 p-4 min-h-0">
        {/* Left: Video + transcript */}
        <div className="w-80 flex flex-col gap-3 flex-shrink-0">
          <div className="relative rounded-xl overflow-hidden bg-gray-900 aspect-[4/3] border-2 border-gray-200 shadow-md">
            <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
            <div className="absolute bottom-2 left-2 right-2 flex justify-between">
              <span className="bg-black/60 px-2 py-1 rounded text-[10px] text-white">You</span>
              <span className="bg-black/60 px-2 py-1 rounded text-[10px] text-amber-300">{emotion}</span>
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-xl p-3 shadow-sm">
            <p className="text-[10px] text-gray-400 uppercase mb-1">Live Transcription</p>
            <p className="text-sm text-gray-600 line-clamp-3">{transcript}</p>
          </div>
        </div>

        {/* Right: Question + Chat */}
        <div className="flex-1 flex flex-col gap-3 min-w-0">
          <div className="bg-gradient-to-r from-indigo-50 to-violet-50 border border-indigo-100 rounded-xl p-5 shadow-sm">
            <p className="text-[10px] text-indigo-500 uppercase mb-2 flex items-center gap-1">
              <MessageCircle className="w-3 h-3" /> Current Question (Q{sessionData.qCount})
            </p>
            <p className="text-gray-800 text-sm leading-relaxed">{currentQuestion}</p>
          </div>

          <div className="flex-1 bg-white border border-gray-200 rounded-xl p-4 overflow-y-auto space-y-2 shadow-sm">
            {chatLog.map((msg, i) => (
              <div key={i} className={`max-w-[85%] p-3 rounded-xl text-sm ${
                msg.role === 'agent'
                  ? 'bg-indigo-50 border border-indigo-100 text-gray-700 self-start'
                  : 'bg-emerald-50 border border-emerald-100 text-gray-700 ml-auto'
              }`}>
                <p className="text-[10px] text-gray-400 mb-1">{msg.role === 'agent' ? '🤖 Interviewer' : '🧑 You'}</p>
                <p>{msg.text}</p>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="px-6 py-3 bg-white border-t border-gray-200 flex items-center shadow-sm">
        <button
          onClick={endInterview}
          className="px-4 py-2 bg-red-500 hover:bg-red-600 rounded-lg text-sm font-medium text-white flex items-center gap-2 transition-all shadow-sm"
        >
          <PhoneOff className="w-4 h-4" /> End Interview
        </button>
        <div className="ml-auto flex items-center gap-2 text-xs text-gray-400">
          <Mic className="w-3 h-3" /> Listening
        </div>
      </div>
    </div>
  )
}
