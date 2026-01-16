'use client'

import { useState, useEffect } from 'react'
import { useTheme } from '@/contexts/ThemeContext'

const THINKING_PHRASES = [
  "Thinking....",
  "Grabbing Fiat Educational Resources.....",
  "Searching the Web....."
]

export default function ThinkingAnimation() {
  const { theme } = useTheme()
  const [currentPhrase, setCurrentPhrase] = useState(THINKING_PHRASES[0])
  const [isFading, setIsFading] = useState(false)

  useEffect(() => {
    const interval = setInterval(() => {
      setIsFading(true)

      setTimeout(() => {
        // Pick a random phrase
        const randomIndex = Math.floor(Math.random() * THINKING_PHRASES.length)
        setCurrentPhrase(THINKING_PHRASES[randomIndex])
        setIsFading(false)
      }, 300) // Half of fade duration

    }, 3000) // Change phrase every 3 seconds

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex items-center gap-1 py-2">
      {currentPhrase.split('').map((char, index) => (
        <span
          key={`${currentPhrase}-${index}`}
          className={`inline-block transition-opacity duration-300 ${
            isFading ? 'opacity-0' : 'opacity-100'
          } ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}
          style={{
            animation: 'gentleWave 2s ease-in-out infinite',
            animationDelay: `${index * 0.05}s`
          }}
        >
          {char === ' ' ? '\u00A0' : char}
        </span>
      ))}
    </div>
  )
}
