/**
 * The list of steps down the side of the screen, showing where you are.
 */
import { motion } from 'framer-motion'
import { CheckCircle2, Lock } from 'lucide-react'

export default function Sidebar({ steps, currentStep, onNavigate, canNavigate }) {
  const currentIdx = steps.findIndex(s => s.id === currentStep)

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shadow-sm">
      {/* Logo */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-md shadow-indigo-200">
            AI
          </div>
          <div>
            <h1 className="font-bold text-gray-900 text-sm">InterviewAI</h1>
            <p className="text-[10px] text-gray-400">Adaptive Interview Platform</p>
          </div>
        </div>
      </div>

      {/* Steps */}
      <nav className="flex-1 p-4 space-y-1">
        {steps.map((step, idx) => {
          const isActive = step.id === currentStep
          const isDone = idx < currentIdx
          const isLocked = !canNavigate(step.id)

          return (
            <button
              key={step.id}
              onClick={() => onNavigate(step.id)}
              disabled={isLocked}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all text-sm group
                ${isActive
                  ? 'bg-indigo-50 text-indigo-700 border border-indigo-200 shadow-sm'
                  : isDone
                    ? 'text-emerald-600 hover:bg-emerald-50'
                    : isLocked
                      ? 'text-gray-300 cursor-not-allowed'
                      : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                }
              `}
            >
              <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs flex-shrink-0
                ${isActive ? 'bg-indigo-100' : isDone ? 'bg-emerald-50' : 'bg-gray-100'}
              `}>
                {isDone ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : isLocked ? <Lock className="w-3 h-3" /> : step.icon}
              </span>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{step.label}</p>
                <p className="text-[10px] text-gray-400">Step {step.num}</p>
              </div>
              {isActive && (
                <motion.div
                  layoutId="activeIndicator"
                  className="w-1.5 h-1.5 bg-indigo-500 rounded-full"
                />
              )}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-100">
        <p className="text-[10px] text-gray-400 text-center">CMP7200 Dissertation Project</p>
      </div>
    </aside>
  )
}
