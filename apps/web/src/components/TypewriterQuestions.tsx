'use client'

import { useState, useEffect, useRef } from 'react'
import { useTheme } from '@/contexts/ThemeContext'

interface QuestionCategory {
  title: string
  questions: string[]
}

const QUESTION_CATEGORIES: QuestionCategory[] = [
  {
    title: "🧭 I'm Not Sure Where to Start",
    questions: [
      "I feel like I've done everything I was supposed to do financially, but I'm still not confident about retirement. Is that normal?",
      "I'm close to retirement, but I don't even know what questions I should be asking. Where do people usually start?",
      "How do I know if I'm actually ready to retire, or just hoping I am?"
    ]
  },
  {
    title: "💸 Income, Taxes & Tradeoffs",
    questions: [
      "How do taxes really work in retirement, and why do people say they can actually go up?",
      "How should I think about using my 401(k), Roth, and cash together once I stop working?",
      "What are the biggest tax mistakes people make in the first few years of retirement?"
    ]
  },
  {
    title: "🕰 Social Security & Timing",
    questions: [
      "Everyone says I should wait until 70 for Social Security. How do people actually decide if that makes sense?",
      "How does Social Security fit into the rest of my retirement income, not just on its own?"
    ]
  },
  {
    title: "📉 Risk, Markets & Fear",
    questions: [
      "What happens if the market drops right after I retire, and how do people plan around that?",
      "How much risk is too much risk once you're close to retirement?",
      "Why does holding a lot of cash feel safe, but sometimes cause problems in retirement?"
    ]
  },
  {
    title: "🧩 Everything Feels Connected",
    questions: [
      "Why does every retirement decision seem connected, and how do people think through that without overcomplicating things?",
      "How do you make retirement decisions when there's no single 'right answer'?",
      "How do people balance optimal planning with real life in retirement?"
    ]
  },
  {
    title: "🧠 Education-First",
    questions: [
      "How do retirees move from information overload to confident decisions?",
      "What does a realistic retirement plan actually look like in real life?",
      "What are the tradeoffs most people don't realize until they're already retired?"
    ]
  }
]

interface TypewriterQuestionsProps {
  onQuestionClick?: (question: string) => void
}

export default function TypewriterQuestions({ onQuestionClick }: TypewriterQuestionsProps) {
  const { theme } = useTheme()
  const [displayText, setDisplayText] = useState('')
  const [isHighlighted, setIsHighlighted] = useState(false)
  const [expandedSection, setExpandedSection] = useState<number | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState('')

  // Track which questions have been used per category
  const [usedQuestionsPerCategory, setUsedQuestionsPerCategory] = useState<number[][]>(
    QUESTION_CATEGORIES.map(() => [])
  )
  const [currentCategoryIndex, setCurrentCategoryIndex] = useState(0)

  // Refs for animation state
  const animationRef = useRef<{
    currentQuestion: string
    charIndex: number
    isDeleting: boolean
    categoryIndex: number
  }>({
    currentQuestion: '',
    charIndex: 0,
    isDeleting: false,
    categoryIndex: 0
  })

  // Get next question following the sequential category order
  const getNextQuestion = () => {
    const state = animationRef.current
    const category = QUESTION_CATEGORIES[state.categoryIndex]
    const usedQuestions = usedQuestionsPerCategory[state.categoryIndex]

    // Find available questions in current category
    const availableIndices = category.questions
      .map((_, idx) => idx)
      .filter(idx => !usedQuestions.includes(idx))

    let questionIndex: number

    if (availableIndices.length > 0) {
      // Pick random from available questions
      questionIndex = availableIndices[Math.floor(Math.random() * availableIndices.length)]
    } else {
      // All questions used in this category, reset it
      const newUsedQuestions = [...usedQuestionsPerCategory]
      newUsedQuestions[state.categoryIndex] = []
      setUsedQuestionsPerCategory(newUsedQuestions)
      questionIndex = Math.floor(Math.random() * category.questions.length)
    }

    // Mark question as used
    const newUsedQuestions = [...usedQuestionsPerCategory]
    newUsedQuestions[state.categoryIndex] = [...usedQuestions, questionIndex]
    setUsedQuestionsPerCategory(newUsedQuestions)

    // Move to next category for next iteration
    state.categoryIndex = (state.categoryIndex + 1) % QUESTION_CATEGORIES.length

    return category.questions[questionIndex]
  }

  // Continuous typing animation loop
  useEffect(() => {
    // Don't run animation if user is editing
    if (isEditing) return

    let timeoutId: NodeJS.Timeout

    const animate = () => {
      const state = animationRef.current

      // Initialize first question if empty
      if (!state.currentQuestion) {
        state.currentQuestion = getNextQuestion()
        state.charIndex = 0
        state.isDeleting = false
        setIsHighlighted(false)
      }

      if (!state.isDeleting) {
        // Typing forward
        if (state.charIndex <= state.currentQuestion.length) {
          setDisplayText(state.currentQuestion.slice(0, state.charIndex))
          state.charIndex++
          timeoutId = setTimeout(animate, 60) // Typing speed
        } else {
          // Finished typing, wait then highlight and delete
          timeoutId = setTimeout(() => {
            // Highlight the text
            setIsHighlighted(true)
            setTimeout(() => {
              // Delete all at once (like pressing delete)
              setDisplayText('')
              setIsHighlighted(false)
              state.isDeleting = true
              state.charIndex = 0
              animate()
            }, 600) // Show highlight for 600ms (slower)
          }, 2000) // Pause after typing completes (2 seconds)
        }
      } else {
        // Finished deleting, get next question and continue loop
        timeoutId = setTimeout(() => {
          state.currentQuestion = getNextQuestion()
          state.charIndex = 0
          state.isDeleting = false
          animate()
        }, 100) // Brief pause before next question
      }
    }

    animate()

    return () => clearTimeout(timeoutId)
  }, [usedQuestionsPerCategory, isEditing])

  const handleCategorySelect = (question: string) => {
    if (onQuestionClick) {
      onQuestionClick(question)
    }
  }

  const toggleSection = (index: number) => {
    setExpandedSection(expandedSection === index ? null : index)
  }

  const handleBoxClick = () => {
    setIsEditing(true)
    setEditValue('') // Clear the text when clicking
  }

  const handleSubmit = () => {
    if (editValue.trim() && onQuestionClick) {
      onQuestionClick(editValue)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="w-full space-y-6">
      {/* Typewriter Display / Editable Input */}
      <div
        className={`w-full border rounded-xl transition-colors relative ${
          theme === 'dark'
            ? 'bg-gray-900 border-gray-800'
            : 'bg-gray-50 border-gray-300'
        }`}
      >
        {isEditing ? (
          <div className="relative">
            <textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
              rows={3}
              placeholder="Type your question here..."
              className={`w-full px-4 py-3.5 pr-12 rounded-xl resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors text-[15px] ${
                theme === 'dark'
                  ? 'bg-gray-900 text-white placeholder-gray-500'
                  : 'bg-gray-50 text-gray-900 placeholder-gray-400'
              }`}
              style={{
                minHeight: '100px',
              }}
            />
            <button
              onClick={handleSubmit}
              disabled={!editValue.trim()}
              className={`absolute bottom-3 right-3 h-8 px-4 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm font-medium ${
                theme === 'dark'
                  ? 'bg-white text-black hover:bg-gray-200'
                  : 'bg-black text-white hover:bg-gray-800'
              }`}
            >
              <span>Get Started</span>
              <svg
                width="16"
                height="16"
                viewBox="0 0 20 20"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="text-blue-600"
              >
                <path
                  d="M3 10L17 3L10 17L8.5 11.5L3 10Z"
                  fill="currentColor"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        ) : (
          <div className="relative">
            <div
              onClick={handleBoxClick}
              className="px-4 py-3.5 pr-12 cursor-text"
              style={{ minHeight: '100px' }}
            >
              <div className="flex items-start">
                <span className={`text-[15px] ${
                  isHighlighted
                    ? theme === 'dark'
                      ? 'bg-blue-600 text-white'
                      : 'bg-blue-500 text-white'
                    : theme === 'dark'
                      ? 'text-white'
                      : 'text-gray-900'
                }`}>
                  {displayText}
                </span>
                {!isHighlighted && (
                  <span className={`inline-block w-0.5 h-5 ml-1 animate-pulse ${
                    theme === 'dark' ? 'bg-gray-400' : 'bg-gray-600'
                  }`}></span>
                )}
              </div>
            </div>
            <button
              onClick={() => {
                if (displayText.trim() && onQuestionClick) {
                  onQuestionClick(displayText)
                }
              }}
              disabled={!displayText.trim()}
              className={`absolute bottom-3 right-3 h-8 px-4 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm font-medium ${
                theme === 'dark'
                  ? 'bg-white text-black hover:bg-gray-200'
                  : 'bg-black text-white hover:bg-gray-800'
              }`}
            >
              <span>Get Started</span>
              <svg
                width="16"
                height="16"
                viewBox="0 0 20 20"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="text-blue-600"
              >
                <path
                  d="M3 10L17 3L10 17L8.5 11.5L3 10Z"
                  fill="currentColor"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Expandable Sections */}
      <div className="w-full space-y-2">
        <p className={`text-sm font-medium mb-3 ${
          theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
        }`}>
          Start here - choose a question:
        </p>

        {QUESTION_CATEGORIES.map((category, categoryIndex) => (
          <div
            key={categoryIndex}
            className={`border rounded-xl overflow-hidden transition-colors backdrop-blur-sm ${
              theme === 'dark'
                ? 'border-gray-800 bg-black/60'
                : 'border-gray-300 bg-gray-50/80'
            }`}
          >
            {/* Section Header */}
            <button
              onClick={() => toggleSection(categoryIndex)}
              className={`w-full px-4 py-3 flex items-center justify-between transition-colors ${
                theme === 'dark'
                  ? 'hover:bg-gray-800/50'
                  : 'hover:bg-gray-50'
              }`}
            >
              <span className={`text-sm font-medium ${
                theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
              }`}>
                {category.title}
              </span>
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                className={`transition-transform ${
                  expandedSection === categoryIndex ? 'rotate-180' : ''
                } ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}
              >
                <path d="M6 9l6 6 6-6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>

            {/* Expanded Questions */}
            {expandedSection === categoryIndex && (
              <div className={`border-t ${
                theme === 'dark' ? 'border-gray-800' : 'border-gray-200'
              }`}>
                {category.questions.map((question, questionIndex) => (
                  <button
                    key={questionIndex}
                    onClick={() => handleCategorySelect(question)}
                    className={`w-full text-left px-4 py-2.5 text-sm transition-colors border-b last:border-b-0 ${
                      theme === 'dark'
                        ? 'text-gray-300 hover:bg-gray-800/50 border-gray-800'
                        : 'text-gray-700 hover:bg-gray-50 border-gray-200'
                    }`}
                  >
                    {question}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
