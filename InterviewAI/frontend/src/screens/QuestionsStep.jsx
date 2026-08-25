/**
 * Step 3. Shows the questions the system has written, with the missing
 * skills ordered first.
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Loader2, ArrowRight, MessageSquare, Sparkles } from 'lucide-react'
import axios from 'axios'

export default function QuestionsStep({ session, updateSession, onNext }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await axios.post('/api/generate-questions')
      updateSession({ questions: res.data.data })
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  const questions = session.questions

  return (
    <div className="h-full overflow-y-auto gradient-bg p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Interview Questions</h2>
          <p className="text-gray-500 mt-1">AI-generated questions tailored to the role and candidate profile</p>
        </div>

        {!questions ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 bg-violet-50 rounded-2xl flex items-center justify-center mb-6">
              <Sparkles className="w-10 h-10 text-violet-500" />
            </div>
            <p className="text-gray-500 mb-2">Generate adaptive interview questions using Gemini AI</p>
            <p className="text-xs text-gray-400 mb-6">Based on skill graph topics, role level, and candidate profile</p>
            {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
            <button
              onClick={generate}
              disabled={loading}
              className="px-8 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 rounded-xl font-semibold text-white flex items-center gap-2 shadow-lg shadow-violet-200 transition-all"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {loading ? 'Generating (~30s)...' : 'Generate Questions'}
            </button>
          </div>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {/* Stats */}
            <div className="flex gap-4 mb-6">
              <div className="px-4 py-2 bg-indigo-50 border border-indigo-100 rounded-xl">
                <span className="text-lg font-bold text-indigo-600">{questions.total_questions}</span>
                <span className="text-xs text-gray-500 ml-2">questions</span>
              </div>
              <div className="px-4 py-2 bg-amber-50 border border-amber-100 rounded-xl">
                <span className="text-lg font-bold text-amber-600">{questions.estimated_duration_mins || '?'}</span>
                <span className="text-xs text-gray-500 ml-2">est. minutes</span>
              </div>
            </div>

            {/* Question sections */}
            {['opening', 'technical', 'behavioural', 'closing'].map(section => {
              const qs = questions[section] || []
              if (qs.length === 0) return null
              const colors = {
                opening: { bg: 'bg-emerald-50', border: 'border-emerald-100', text: 'text-emerald-700' },
                technical: { bg: 'bg-indigo-50', border: 'border-indigo-100', text: 'text-indigo-700' },
                behavioural: { bg: 'bg-violet-50', border: 'border-violet-100', text: 'text-violet-700' },
                closing: { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-600' },
              }
              const c = colors[section]
              return (
                <div key={section} className={`${c.bg} ${c.border} border rounded-2xl p-5 mb-4`}>
                  <h3 className={`font-semibold ${c.text} capitalize mb-3 flex items-center gap-2`}>
                    <MessageSquare className="w-4 h-4" />
                    {section} ({qs.length})
                  </h3>
                  <div className="space-y-3">
                    {qs.map((q, i) => (
                      <div key={i} className="bg-white rounded-xl p-3 border border-gray-100 shadow-sm">
                        <p className="text-sm text-gray-800">{q.question}</p>
                        <div className="flex gap-2 mt-2">
                          {q.skill && <span className="text-[10px] px-2 py-0.5 bg-gray-100 rounded-lg text-gray-500">{q.skill}</span>}
                          {q.difficulty && <span className="text-[10px] px-2 py-0.5 bg-gray-100 rounded-lg text-gray-500">{q.difficulty}</span>}
                          {q.competency && <span className="text-[10px] px-2 py-0.5 bg-gray-100 rounded-lg text-gray-500">{q.competency}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}

            <div className="flex justify-between items-center mt-8">
              <button
                onClick={generate}
                disabled={loading}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm text-gray-600 flex items-center gap-2 transition-all"
              >
                {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                Regenerate
              </button>
              <button
                onClick={onNext}
                className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 rounded-xl font-semibold text-white flex items-center gap-2 shadow-lg shadow-indigo-200 transition-all"
              >
                Start Interview <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}
