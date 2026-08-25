/**
 * Step 1. Upload a CV and paste the job advert.
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Upload, FileText, Briefcase, Loader2, CheckCircle2, ArrowRight, Sparkles } from 'lucide-react'
import axios from 'axios'

export default function UploadStep({ session, updateSession, onNext }) {
  const [cvFile, setCvFile] = useState(null)
  const [cvText, setCvText] = useState('')
  const [jdText, setJdText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const analyzeAll = async () => {
    setLoading(true)
    setError('')
    try {
      // Parse CV
      const formData = new FormData()
      if (cvFile) {
        formData.append('file', cvFile)
      } else {
        formData.append('text', cvText)
      }
      const cvRes = await axios.post('/api/parse-cv', formData)
      updateSession({ cvData: cvRes.data.data })

      // Parse JD
      const jdRes = await axios.post('/api/parse-jd', { text: jdText })
      updateSession({ jdData: jdRes.data.data })
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    }
    setLoading(false)
  }

  const canAnalyze = (cvFile || cvText.trim()) && jdText.trim()
  const bothDone = session.cvData && session.jdData

  return (
    <div className="h-full overflow-y-auto gradient-bg p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Upload & Analyze</h2>
          <p className="text-gray-500 mt-1">Upload your CV and paste the job description, then click Analyze</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* CV Section */}
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center">
                <FileText className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">Candidate CV</h3>
                <p className="text-xs text-gray-400">Upload PDF or paste text</p>
              </div>
              {session.cvData && <CheckCircle2 className="w-5 h-5 text-emerald-500 ml-auto" />}
            </div>

            {/* File upload */}
            <div
              className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center mb-4 hover:border-indigo-300 hover:bg-indigo-50/30 transition-all cursor-pointer"
              onClick={() => document.getElementById('cv-input').click()}
              onDrop={(e) => {
                e.preventDefault()
                const f = e.dataTransfer.files[0]
                if (f) setCvFile(f)
              }}
              onDragOver={(e) => e.preventDefault()}
            >
              <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500">
                {cvFile ? <span className="text-indigo-600 font-medium">{cvFile.name}</span> : 'Drop PDF here or click to upload'}
              </p>
              <input
                id="cv-input"
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => setCvFile(e.target.files[0])}
              />
            </div>

            <div className="relative mb-4">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-200" /></div>
              <div className="relative flex justify-center"><span className="bg-white px-3 text-xs text-gray-400">or paste text</span></div>
            </div>

            <textarea
              value={cvText}
              onChange={(e) => setCvText(e.target.value)}
              placeholder="Paste CV text here..."
              className="w-full h-28 bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 transition-all"
            />

            {session.cvData && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl">
                <p className="text-xs text-emerald-700 font-medium mb-1">✓ {session.cvData.name || 'Candidate'}</p>
                <p className="text-xs text-gray-500">Skills: {(session.cvData.skills || []).slice(0, 6).join(', ')}</p>
              </motion.div>
            )}
          </div>

          {/* JD Section */}
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 bg-violet-50 rounded-xl flex items-center justify-center">
                <Briefcase className="w-5 h-5 text-violet-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">Job Description</h3>
                <p className="text-xs text-gray-400">Paste the full JD text</p>
              </div>
              {session.jdData && <CheckCircle2 className="w-5 h-5 text-emerald-500 ml-auto" />}
            </div>

            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the complete job description here..."
              className="w-full h-72 bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-violet-200 focus:border-violet-300 transition-all"
            />

            {session.jdData && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl">
                <p className="text-xs text-emerald-700 font-medium mb-1">✓ {session.jdData.job_title || 'Role'}</p>
                <p className="text-xs text-gray-500">Required: {(session.jdData.required_skills || []).slice(0, 6).join(', ')}</p>
              </motion.div>
            )}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Action buttons */}
        <div className="mt-8 flex items-center justify-between">
          {!bothDone ? (
            <button
              onClick={analyzeAll}
              disabled={loading || !canAnalyze}
              className="px-8 py-3.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl font-semibold text-white flex items-center gap-2 shadow-lg shadow-indigo-200 transition-all"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {loading ? 'Analyzing...' : 'Analyze CV & JD'}
            </button>
          ) : (
            <div className="flex items-center gap-3">
              <span className="text-sm text-emerald-600 font-medium flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" /> Both analyzed successfully
              </span>
              <button
                onClick={analyzeAll}
                disabled={loading || !canAnalyze}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-xs text-gray-600 transition-all"
              >
                Re-analyze
              </button>
            </div>
          )}

          {bothDone && (
            <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}>
              <button
                onClick={onNext}
                className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 rounded-xl font-semibold text-white flex items-center gap-2 shadow-lg shadow-indigo-200 transition-all"
              >
                Build Skill Graph <ArrowRight className="w-4 h-4" />
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}
