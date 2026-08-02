import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Sidebar from './components/Sidebar'
import UploadStep from './screens/UploadStep'
import GraphStep from './screens/GraphStep'
import QuestionsStep from './screens/QuestionsStep'
import SetupScreen from './screens/SetupScreen'
import InterviewScreen from './screens/InterviewScreen'
import DashboardScreen from './screens/DashboardScreen'

const STEPS = [
  { id: 'upload', label: 'Upload & Parse', icon: '📄', num: 1 },
  { id: 'graph', label: 'Skill Graph', icon: '🧠', num: 2 },
  { id: 'questions', label: 'Questions', icon: '❓', num: 3 },
  { id: 'setup', label: 'Device Setup', icon: '🎤', num: 4 },
  { id: 'interview', label: 'Live Interview', icon: '🎧', num: 5 },
  { id: 'dashboard', label: 'Report', icon: '📊', num: 6 },
]

export default function App() {
  const [step, setStep] = useState('upload')
  const [session, setSession] = useState({
    cvData: null,
    jdData: null,
    graphData: null,
    questions: null,
    interviewUrl: null,
  })
  const [mediaStream, setMediaStream] = useState(null)
  const [interviewData, setInterviewData] = useState({
    transcript: [],
    emotions: [],
    distractions: [],
    vision: [],        // M7/M8 attention + posture samples
    voice: [],         // M10 prosody samples
    startTime: null,
    qCount: 0,
    maxQuestions: 15,
    phase: 'setup',
    duration: 0,
  })

  const updateSession = useCallback((updates) => {
    setSession(prev => ({ ...prev, ...updates }))
  }, [])

  const canNavigate = (targetStep) => {
    const idx = STEPS.findIndex(s => s.id === targetStep)
    if (idx <= 0) return true
    if (idx === 1) return session.cvData && session.jdData
    if (idx === 2) return session.graphData
    if (idx >= 3) return session.questions
    return true
  }

  // The live interview takes the whole viewport — a call UI with a wizard
  // sidebar next to it reads as a form, not a meeting.
  if (step === 'interview') {
    return (
      <InterviewScreen
        mediaStream={mediaStream}
        sessionData={interviewData}
        setSessionData={setInterviewData}
        onEnd={() => setStep('dashboard')}
      />
    )
  }

  // The report is the deliverable — it gets the full page, and the wizard
  // sidebar would only reappear in the printed PDF.
  if (step === 'dashboard') {
    return <DashboardScreen sessionData={interviewData} />
  }

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50">
      <Sidebar
        steps={STEPS}
        currentStep={step}
        onNavigate={(id) => canNavigate(id) && setStep(id)}
        canNavigate={canNavigate}
      />

      <main className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.25 }}
            className="h-full"
          >
            {step === 'upload' && (
              <UploadStep
                session={session}
                updateSession={updateSession}
                onNext={() => setStep('graph')}
              />
            )}
            {step === 'graph' && (
              <GraphStep
                session={session}
                updateSession={updateSession}
                onNext={() => setStep('questions')}
              />
            )}
            {step === 'questions' && (
              <QuestionsStep
                session={session}
                updateSession={updateSession}
                onNext={() => setStep('setup')}
              />
            )}
            {step === 'setup' && (
              <SetupScreen
                onReady={(stream) => {
                  setMediaStream(stream)
                  setStep('interview')
                }}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  )
}
