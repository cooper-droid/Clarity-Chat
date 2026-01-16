'use client'

import { useState, useEffect, useRef } from 'react'
import { useTheme } from '@/contexts/ThemeContext'

interface EnhancedChatBoxProps {
  onQuestionClick?: (question: string) => void
}

type Topic = 'Taxes' | 'Markets' | 'Education' | null

const TOPIC_PROMPTS = {
  Taxes: [
    "How do taxes really work in retirement?",
    "What are the 2026 tax brackets?",
    "Should I convert my 401(k) to a Roth IRA?"
  ],
  Markets: [
    "What happens if the market drops right after I retire?",
    "How should I allocate my portfolio in retirement?",
    "Is now a good time to invest?"
  ],
  Education: [
    "What is a Roth IRA and how does it work?",
    "What does a realistic retirement plan look like?",
    "How much do I need to retire comfortably?"
  ]
}

const TYPING_QUESTIONS = [
  "What are the 2026 tax brackets?",
  "How do I know if I'm ready to retire?",
  "What's the best age to take Social Security?",
  "How should I allocate my retirement portfolio?",
  "What are the biggest retirement planning mistakes?",
  "How much do I need saved for retirement?"
]

export default function EnhancedChatBox({ onQuestionClick }: EnhancedChatBoxProps) {
  const { theme } = useTheme()
  const [selectedTopic, setSelectedTopic] = useState<Topic>(null)
  const [displayText, setDisplayText] = useState('')
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [showTopicPrompts, setShowTopicPrompts] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState('')

  // Typewriter animation
  useEffect(() => {
    if (selectedTopic || isEditing) return // Stop animation when topic is selected or editing

    let charIndex = 0
    const currentQuestion = TYPING_QUESTIONS[currentQuestionIndex]

    const typeChar = () => {
      if (charIndex <= currentQuestion.length) {
        setDisplayText(currentQuestion.slice(0, charIndex))
        charIndex++
        return setTimeout(typeChar, 60)
      } else {
        // Wait, then delete and move to next question
        return setTimeout(() => {
          setDisplayText('')
          setCurrentQuestionIndex((prev) => (prev + 1) % TYPING_QUESTIONS.length)
        }, 2000)
      }
    }

    const timeoutId = typeChar()
    return () => clearTimeout(timeoutId)
  }, [currentQuestionIndex, selectedTopic, isEditing])

  const handleTopicSelect = (topic: Topic) => {
    setSelectedTopic(topic)
    setShowTopicPrompts(true)
  }

  const handlePromptClick = (question: string) => {
    if (onQuestionClick) {
      onQuestionClick(question)
    }
  }

  const handleInputClick = () => {
    setIsEditing(true)
    setEditValue('')
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
    <div className={`w-full border-2 rounded-3xl flex flex-col overflow-hidden ${
      theme === 'dark'
        ? 'bg-[#1a1a1a] border-gray-800'
        : 'bg-white border-gray-200'
    }`} style={{ aspectRatio: '1 / 0.67' }}>
      {/* Chat Messages Area - looks like actual chat */}
      <div className="flex-1 p-6 overflow-y-auto">
        {/* Initial greeting message */}
        <div className="flex items-start gap-3 mb-4">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
            theme === 'dark' ? 'bg-gray-800' : 'bg-gray-100'
          }`}>
            <span className="text-xs font-bold">CLR</span>
          </div>
          <div className={`rounded-2xl rounded-tl-sm px-4 py-3 max-w-[80%] ${
            theme === 'dark' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-900'
          }`}>
            <p className="text-sm">
              Hi! I'm here to help with your retirement planning questions. What would you like to know?
            </p>
          </div>
        </div>

        {/* Topic prompts (after topic selection) */}
        {showTopicPrompts && selectedTopic && (
          <div className="space-y-2 animate-slideUp">
            {TOPIC_PROMPTS[selectedTopic].map((prompt, index) => (
              <button
                key={index}
                onClick={() => handlePromptClick(prompt)}
                className={`w-full text-left px-4 py-3 rounded-xl transition-all hover:scale-[1.02] ${
                  theme === 'dark'
                    ? 'bg-gray-800 hover:bg-gray-750 text-white'
                    : 'bg-gray-50 hover:bg-gray-100 text-gray-900'
                }`}
              >
                <p className="text-sm">{prompt}</p>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Section */}
      <div className={`border-t p-4 space-y-3 ${
        theme === 'dark' ? 'border-gray-800' : 'border-gray-200'
      }`}>
        {/* Topic Selection Buttons */}
        <div className="flex items-center justify-center gap-2">
          <p className={`text-xs font-medium mr-2 ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
          }`}>
            Start here:
          </p>
          {(['Taxes', 'Markets', 'Education'] as const).map((topic) => (
            <button
              key={topic}
              onClick={() => handleTopicSelect(topic)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                selectedTopic === topic
                  ? theme === 'dark'
                    ? 'bg-blue-600 text-white'
                    : 'bg-blue-500 text-white'
                  : theme === 'dark'
                    ? 'bg-gray-800 text-gray-300 hover:bg-gray-750'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {topic}
            </button>
          ))}
        </div>

        {/* Input Box */}
        <div className="relative">
          {isEditing ? (
            <div className="relative">
              <textarea
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onKeyDown={handleKeyDown}
                autoFocus
                rows={2}
                placeholder="Type your question here..."
                className={`w-full px-4 py-3 pr-12 rounded-xl resize-none focus:ring-2 focus:ring-blue-500 focus:outline-none transition-colors text-sm ${
                  theme === 'dark'
                    ? 'bg-gray-800 text-white placeholder-gray-500'
                    : 'bg-gray-50 text-gray-900 placeholder-gray-400'
                }`}
              />
              <button
                onClick={handleSubmit}
                disabled={!editValue.trim()}
                className={`absolute bottom-2 right-2 w-8 h-8 rounded-lg flex items-center justify-center transition-colors disabled:opacity-40 ${
                  theme === 'dark'
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 20 20"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M3 10L17 3L10 17L8.5 11.5L3 10Z"
                    fill="currentColor"
                  />
                </svg>
              </button>
            </div>
          ) : (
            <div className="relative">
              <div
                onClick={handleInputClick}
                className={`px-4 py-3 pr-12 rounded-xl cursor-text transition-colors ${
                  theme === 'dark'
                    ? 'bg-gray-800 text-white'
                    : 'bg-gray-50 text-gray-900'
                }`}
              >
                <div className="flex items-center min-h-[24px]">
                  {!selectedTopic && (
                    <>
                      <span className="text-sm">{displayText}</span>
                      <span className={`inline-block w-0.5 h-4 ml-1 animate-pulse ${
                        theme === 'dark' ? 'bg-gray-400' : 'bg-gray-600'
                      }`}></span>
                    </>
                  )}
                  {selectedTopic && (
                    <span className={`text-sm ${
                      theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
                    }`}>
                      Type your question here...
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={handleInputClick}
                className={`absolute bottom-2 right-2 w-8 h-8 rounded-lg flex items-center justify-center transition-colors animate-gentle-pulse ${
                  theme === 'dark'
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 20 20"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M3 10L17 3L10 17L8.5 11.5L3 10Z"
                    fill="currentColor"
                  />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
