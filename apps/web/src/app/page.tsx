'use client'

import { useState, useEffect } from 'react'
import ChatInterface from '@/components/ChatInterface'
import ChatSidebar from '@/components/ChatSidebar'
import LandingPage from '@/components/LandingPage'
import { getUserId } from '@/utils/userId'
import { useTheme } from '@/contexts/ThemeContext'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const { theme } = useTheme()
  const [userId, setUserId] = useState<string>('')
  const [sessionId, setSessionId] = useState<string>('')
  const [showChat, setShowChat] = useState(false)
  const [initialQuestion, setInitialQuestion] = useState<string>('')

  useEffect(() => {
    // Get or create user ID
    const id = getUserId()
    setUserId(id)

    // Create initial session
    createNewSession(id)
  }, [])

  const createNewSession = async (uid?: string) => {
    try {
      const response = await fetch(`${API_URL}/sessions/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: uid || userId })
      })

      if (response.ok) {
        const data = await response.json()
        setSessionId(data.session_id)
      }
    } catch (error) {
      console.error('Error creating session:', error)
      // Fallback to client-side ID if API fails
      const fallbackId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      setSessionId(fallbackId)
    }
  }

  const handleGetStarted = (question?: string) => {
    if (question) {
      setInitialQuestion(question)
    }
    setShowChat(true)
  }

  const handleSessionChange = async (newSessionId: string) => {
    setSessionId(newSessionId)
    setInitialQuestion('')
  }

  const handleNewChat = async () => {
    await createNewSession()
    setInitialQuestion('')
  }

  if (!sessionId || !userId) {
    return (
      <div className={`flex items-center justify-center min-h-screen ${
        theme === 'dark' ? 'bg-black' : 'bg-white'
      }`}>
        <div className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Loading...</div>
      </div>
    )
  }

  if (!showChat) {
    return <LandingPage onGetStarted={handleGetStarted} />
  }

  return (
    <main className={`h-screen flex ${theme === 'dark' ? 'bg-black' : 'bg-white'}`}>
      <ChatSidebar
        userId={userId}
        currentSessionId={sessionId}
        onSessionChange={handleSessionChange}
        onNewChat={handleNewChat}
      />
      <div className="flex-1">
        <ChatInterface
          key={sessionId}
          sessionId={sessionId}
          userId={userId}
          initialQuestion={initialQuestion}
        />
      </div>
    </main>
  )
}
