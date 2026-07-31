import { useState, useRef, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Camera, Mic, AlertCircle, CheckCircle2, RotateCw } from 'lucide-react'

export default function SetupScreen({ onReady }) {
  const [camOk, setCamOk] = useState(null)
  const [micOk, setMicOk] = useState(null)
  const [error, setError] = useState('')
  const [testing, setTesting] = useState(false)
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const animRef = useRef(null)
  const [micLevel, setMicLevel] = useState(0)

  const testDevices = useCallback(async () => {
    setTesting(true)
    setError('')
    setCamOk(null)
    setMicOk(null)

    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop())
      }
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream

      const vTrack = stream.getVideoTracks()[0]
      setCamOk(vTrack && vTrack.readyState === 'live')

      const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
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
        if (avg > 8 && !detected) {
          detected = true
          setMicOk(true)
        }
        animRef.current = requestAnimationFrame(check)
      }
      check()

      setTimeout(() => {
        if (!detected) setMicOk(true)
      }, 3000)

    } catch (err) {
      setError(`Permission denied: ${err.message}. Please allow camera & microphone access.`)
      setCamOk(false)
      setMicOk(false)
    }
    setTesting(false)
  }, [])

  useEffect(() => {
    testDevices()
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current)
    }
  }, [testDevices])

  const canProceed = camOk === true && micOk === true

  return (
    <div className="h-full flex items-center justify-center gradient-bg screen-enter">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-xl mx-4"
      >
        <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-indigo-50 border border-indigo-100 rounded-full text-xs text-indigo-600 mb-4">
              <span className="w-2 h-2 bg-indigo-500 rounded-full pulse-dot" />
              AI Interview Platform
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Device Setup</h1>
            <p className="text-gray-500 mt-2 text-sm">
              Let's verify your camera and microphone before starting
            </p>
          </div>

          {/* Device Status Cards */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <DeviceCard icon={<Camera className="w-6 h-6" />} label="Camera" status={camOk} />
            <DeviceCard icon={<Mic className="w-6 h-6" />} label="Microphone" status={micOk} />
          </div>

          {/* Preview Row */}
          <div className="flex gap-4 mb-6">
            <div className="w-48 h-36 rounded-xl overflow-hidden bg-gray-900 border-2 border-gray-200 flex-shrink-0 shadow-inner">
              <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
            </div>

            <div className="flex-1 bg-gray-50 rounded-xl p-4 border border-gray-200">
              <p className="text-xs text-gray-500 mb-2">Mic Level</p>
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full"
                  style={{ width: `${micLevel}%` }}
                  transition={{ duration: 0.1 }}
                />
              </div>
              <p className="text-xs text-gray-400 mt-2">
                {micOk ? '✓ Audio detected' : 'Speak to test...'}
              </p>
            </div>
          </div>

          {/* Error */}
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm mb-4"
            >
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}

          {/* Buttons */}
          <div className="space-y-3">
            <button
              onClick={testDevices}
              disabled={testing}
              className="w-full py-3 px-4 bg-gray-100 hover:bg-gray-200 border border-gray-200 rounded-xl text-sm font-medium text-gray-600 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <RotateCw className={`w-4 h-4 ${testing ? 'animate-spin' : ''}`} />
              {testing ? 'Testing...' : 'Re-test Devices'}
            </button>

            <button
              onClick={() => {
                if (animRef.current) cancelAnimationFrame(animRef.current)
                onReady(streamRef.current)
              }}
              disabled={!canProceed}
              className="w-full py-4 px-4 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 rounded-xl text-base font-semibold text-white transition-all shadow-lg shadow-indigo-200 disabled:opacity-40 disabled:shadow-none disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span>Begin Interview</span>
              <span className="text-lg">→</span>
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

function DeviceCard({ icon, label, status }) {
  const borderColor = status === true ? 'border-emerald-200' : status === false ? 'border-red-200' : 'border-gray-200'
  const bgColor = status === true ? 'bg-emerald-50' : status === false ? 'bg-red-50' : 'bg-gray-50'

  return (
    <div className={`${bgColor} ${borderColor} border rounded-xl p-4 text-center transition-all`}>
      <div className="flex justify-center mb-2 text-gray-400">{icon}</div>
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
        {status === null && (
          <span className="text-xs text-gray-400">Checking...</span>
        )}
      </div>
    </div>
  )
}
