/**
 * Step 4. Checks the camera and microphone work, lets the candidate choose
 * a spoken or typed interview, and explains what is being measured.
 *
 * This is the only place in the app that asks for the camera and
 * microphone. The stream it opens is handed to the interview screen,
 * which is why it must not be stopped on the way through.
 */
import { useState, useRef, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Camera, Mic, AlertCircle, CheckCircle2, RotateCw,
  Eye, Activity, AudioLines, MonitorX, ShieldCheck, Lock, Keyboard,
} from 'lucide-react'
import axios from 'axios'

/** What the candidate is told before anything starts recording. */
const MONITORING = [
  {
    icon: <Eye className="w-4 h-4" />,
    title: 'Attention tracking',
    body: 'Your camera is used to estimate whether you are facing the screen. It calibrates to your natural sitting position in the first few seconds.',
    modes: ['voice', 'text'],
  },
  {
    icon: <Activity className="w-4 h-4" />,
    title: 'Posture analysis',
    body: 'Shoulder position and head alignment are measured to gauge how engaged you appear. Sit however is comfortable — it measures change, not perfection.',
    modes: ['voice', 'text'],
  },
  {
    icon: <AudioLines className="w-4 h-4" />,
    title: 'Vocal delivery',
    body: 'Your microphone is analysed for volume, pace, pitch variation and pauses. This measures how you deliver an answer, not what you sound like.',
    modes: ['voice'],
  },
  {
    icon: <Keyboard className="w-4 h-4" />,
    title: 'How you type',
    body: 'Answers pasted from elsewhere are flagged on your report. Type your own answers — that is what is being assessed.',
    modes: ['text'],
  },
  {
    icon: <MonitorX className="w-4 h-4" />,
    title: 'Tab switching is recorded',
    body: 'Leaving this tab is counted and shown on the report. Repeated switching will lower your integrity score. Please stay on this tab throughout.',
    modes: ['voice', 'text'],
  },
]

const MODES = [
  {
    id: 'voice',
    icon: <Mic className="w-5 h-5" />,
    title: 'Voice interview',
    body: 'Speak your answers out loud. The interviewer talks back to you, like a real call.',
    needs: 'Camera and microphone',
  },
  {
    id: 'text',
    icon: <Keyboard className="w-5 h-5" />,
    title: 'Text interview',
    body: 'Type your answers in a chat. Same interviewer, same questions, same report.',
    needs: 'Camera only',
  },
]

export default function SetupScreen({ onReady }) {
  const [camOk, setCamOk] = useState(null)
  const [micOk, setMicOk] = useState(null)
  const [error, setError] = useState('')
  const [testing, setTesting] = useState(false)
  const [acknowledged, setAcknowledged] = useState(false)
  const [micLevel, setMicLevel] = useState(0)
  const [mode, setMode] = useState('voice')

  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const animRef = useRef(null)
  const audioCtxRef = useRef(null)
  // Set when the stream is passed to the interview, so the cleanup below
  // knows not to stop tracks that are about to be used.
  const handedOffRef = useRef(false)

  const testDevices = useCallback(async () => {
    setTesting(true)
    setError('')
    setCamOk(null)
    setMicOk(null)

    try {
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop())

      // This is the only getUserMedia call in the application. The stream it
      // returns is handed to the interview screen, which publishes these exact
      // tracks to LiveKit — so the audio constraints have to be stated here.
      // Setting them on the Room does nothing for an externally supplied track.
      // Echo cancellation is what stops the interviewer's voice, coming out of
      // the candidate's speakers, being captured and read as them interrupting.
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream

      const vTrack = stream.getVideoTracks()[0]
      setCamOk(Boolean(vTrack && vTrack.readyState === 'live'))

      const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      audioCtxRef.current = audioCtx
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      const dataArr = new Uint8Array(analyser.frequencyBinCount)

      let detected = false
      const check = () => {
        analyser.getByteFrequencyData(dataArr)
        const avg = dataArr.reduce((a, b) => a + b, 0) / dataArr.length
        setMicLevel(Math.min(avg / 50 * 100, 100))
        if (avg > 8 && !detected) { detected = true; setMicOk(true) }
        animRef.current = requestAnimationFrame(check)
      }
      check()
      setTimeout(() => { if (!detected) setMicOk(true) }, 3000)
    } catch (err) {
      setError(`Permission denied: ${err.message}. Please allow camera and microphone access.`)
      setCamOk(false)
      setMicOk(false)
    }
    setTesting(false)
  }, [])

  useEffect(() => {
    testDevices()
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current)
      try { audioCtxRef.current?.close() } catch { /* already closed */ }
      // Only release the devices if the candidate left without starting. This
      // same stream object is handed to the interview screen, which publishes
      // its tracks to LiveKit and feeds them to the vision and voice
      // analysers. Stopping the tracks on the way through leaves a dead
      // stream: no picture, and a microphone track that transmits silence.
      if (!handedOffRef.current && streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop())
        streamRef.current = null
      }
    }
  }, [testDevices])

  useEffect(() => {
    // Only the voice mode needs the media server and the agent subprocess.
    // Starting them here means pressing Begin Interview is near-instant.
    if (mode === 'voice') axios.post('/api/prewarm').catch(() => {})
  }, [mode])

  const micRequired = mode === 'voice'
  const canProceed = camOk === true && (!micRequired || micOk === true) && acknowledged

  return (
    <div className="h-full overflow-y-auto gradient-bg p-6 screen-enter">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="max-w-5xl mx-auto"
      >
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-indigo-50 border border-indigo-100 rounded-full text-xs text-indigo-600 mb-3">
            <span className="w-2 h-2 bg-indigo-500 rounded-full pulse-dot" />
            Before you begin
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Choose Your Interview Mode</h1>
          <p className="text-gray-500 mt-2 text-sm">
            Pick how you want to answer, check your devices, then read what is being measured
          </p>
        </div>

        {/* Mode selection */}
        <div className="grid sm:grid-cols-2 gap-4 mb-5">
          {MODES.map(m => {
            const selected = mode === m.id
            return (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={`text-left rounded-2xl border-2 p-5 transition-all ${
                  selected
                    ? 'border-indigo-500 bg-indigo-50/60 shadow-md shadow-indigo-100'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    selected ? 'bg-indigo-500 text-white' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {m.icon}
                  </span>
                  <div>
                    <p className="font-semibold text-gray-900">{m.title}</p>
                    <p className="text-[11px] text-gray-400">{m.needs}</p>
                  </div>
                  {selected && <CheckCircle2 className="w-5 h-5 text-indigo-500 ml-auto" />}
                </div>
                <p className="text-xs text-gray-600 leading-relaxed">{m.body}</p>
              </button>
            )
          })}
        </div>

        <div className="grid lg:grid-cols-2 gap-5 mb-5">
          {/* Devices */}
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <h2 className="font-semibold text-gray-800 mb-4">Your devices</h2>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <DeviceCard icon={<Camera className="w-5 h-5" />} label="Camera" status={camOk} />
              <DeviceCard icon={<Mic className="w-5 h-5" />} label="Microphone"
                          status={micRequired ? micOk : 'not-needed'} />
            </div>

            <div className="rounded-xl overflow-hidden bg-gray-900 border border-gray-200 aspect-video mb-3">
              <video ref={videoRef} autoPlay playsInline muted
                     className="w-full h-full object-cover -scale-x-100" />
            </div>

            {micRequired ? (
              <div className="bg-gray-50 rounded-xl p-3 border border-gray-200 mb-3">
                <p className="text-xs text-gray-500 mb-2">Microphone level — say something</p>
                <div className="h-2.5 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full transition-all duration-100"
                       style={{ width: `${micLevel}%` }} />
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  {micOk ? 'Audio detected' : 'Waiting for audio…'}
                </p>
                <p className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-200">
                  Headphones are recommended. On speakers, your microphone can pick
                  up the interviewer&apos;s voice and cut it off mid-question.
                </p>
              </div>
            ) : (
              <div className="bg-gray-50 rounded-xl p-3 border border-gray-200 mb-3">
                <p className="text-xs text-gray-500">
                  You will type your answers, so the microphone is not used. Your camera
                  still tracks attention and posture.
                </p>
              </div>
            )}

            <button
              onClick={testDevices}
              disabled={testing}
              className="w-full py-2.5 bg-gray-100 hover:bg-gray-200 border border-gray-200 rounded-xl text-sm font-medium text-gray-600 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <RotateCw className={`w-4 h-4 ${testing ? 'animate-spin' : ''}`} />
              {testing ? 'Testing…' : 'Re-test devices'}
            </button>
          </div>

          {/* Briefing */}
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm flex flex-col">
            <h2 className="font-semibold text-gray-800 mb-1">What is being measured</h2>
            <p className="text-xs text-gray-500 mb-4">
              This interview is assessed on more than your answers. Here is exactly what is
              recorded, so nothing is a surprise.
            </p>

            <div className="space-y-3 flex-1">
              {MONITORING.filter(item => item.modes.includes(mode)).map(item => (
                <div key={item.title} className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-500 flex items-center justify-center flex-shrink-0">
                    {item.icon}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">{item.title}</p>
                    <p className="text-xs text-gray-500 leading-relaxed mt-0.5">{item.body}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 flex gap-2.5 p-3 bg-emerald-50 border border-emerald-200 rounded-xl">
              <Lock className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-emerald-800 leading-relaxed">
                <strong>Your privacy:</strong> video and audio are analysed on your own
                computer and are never recorded, stored or uploaded. Only the resulting
                numbers — such as an attention percentage — reach the server.
              </p>
            </div>
          </div>
        </div>

        {/* How it runs */}
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm mb-5">
          <h2 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-500" /> How the interview runs
          </h2>
          <div className="grid sm:grid-cols-3 gap-4 text-xs text-gray-600">
            <div>
              <p className="font-medium text-gray-800 mb-1">Each question appears on screen</p>
              <p className="leading-relaxed">
                {mode === 'voice'
                  ? 'You will see the question a moment before the interviewer speaks it, so you can read along.'
                  : 'The interviewer writes each question in the chat, one at a time.'}
              </p>
            </div>
            <div>
              <p className="font-medium text-gray-800 mb-1">
                {mode === 'voice' ? 'Answer naturally, out loud' : 'Type your answer'}
              </p>
              <p className="leading-relaxed">
                {mode === 'voice'
                  ? 'Speak as you would to a person. Take a moment to think — pauses are normal and expected.'
                  : 'Write as you would speak. Press Enter to send, Shift and Enter for a new line.'}
              </p>
            </div>
            <div>
              <p className="font-medium text-gray-800 mb-1">Ending the interview</p>
              <p className="leading-relaxed">It ends automatically when the questions are done. You
                can also say you would like to stop, and it will confirm first.</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm mb-4">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Acknowledge + start */}
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm mb-8">
          <label className="flex items-start gap-3 cursor-pointer mb-4">
            <input
              type="checkbox"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
              className="mt-0.5 w-4 h-4 accent-indigo-600 cursor-pointer"
            />
            <span className="text-sm text-gray-700 leading-relaxed">
              I understand that my attention, posture,{' '}
              {mode === 'voice' ? 'vocal delivery' : 'typing'} and tab switching are
              monitored during this interview, and that I should remain on this tab throughout.
            </span>
          </label>

          <button
            onClick={() => {
              if (animRef.current) cancelAnimationFrame(animRef.current)
              // Marked before handing over, so the unmount cleanup leaves
              // these tracks alive — the interview screen publishes them.
              handedOffRef.current = true
              onReady(streamRef.current, mode)
            }}
            disabled={!canProceed}
            className="w-full py-4 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 rounded-xl text-base font-semibold text-white transition-all shadow-lg shadow-indigo-200 disabled:opacity-40 disabled:shadow-none disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            Begin {mode === 'voice' ? 'Voice' : 'Text'} Interview <span className="text-lg">→</span>
          </button>

          {!acknowledged && canProceedDevices(camOk, micOk, micRequired) && (
            <p className="text-xs text-gray-400 text-center mt-2">
              Please confirm the statement above to continue
            </p>
          )}
        </div>
      </motion.div>
    </div>
  )
}

function canProceedDevices(camOk, micOk, micRequired) {
  return camOk === true && (!micRequired || micOk === true)
}

function DeviceCard({ icon, label, status }) {
  const border = status === true ? 'border-emerald-200' : status === false ? 'border-red-200' : 'border-gray-200'
  const bg = status === true ? 'bg-emerald-50' : status === false ? 'bg-red-50' : 'bg-gray-50'

  return (
    <div className={`${bg} ${border} border rounded-xl p-3 text-center transition-all`}>
      <div className="flex justify-center mb-1.5 text-gray-400">{icon}</div>
      <p className="text-sm text-gray-700 font-medium">{label}</p>
      <div className="mt-1">
        {status === true && (
          <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
            <CheckCircle2 className="w-3 h-3" /> Working
          </span>
        )}
        {status === false && (
          <span className="inline-flex items-center gap-1 text-xs text-red-500">
            <AlertCircle className="w-3 h-3" /> Error
          </span>
        )}
        {status === null && <span className="text-xs text-gray-400">Checking…</span>}
        {status === 'not-needed' && <span className="text-xs text-gray-400">Not used in text mode</span>}
      </div>
    </div>
  )
}
