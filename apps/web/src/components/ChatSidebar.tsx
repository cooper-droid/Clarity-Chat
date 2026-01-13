'use client'

import { useState, useEffect } from 'react'
import { useTheme } from '@/contexts/ThemeContext'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Session {
  session_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

interface ChatSidebarProps {
  userId: string
  currentSessionId: string
  onSessionChange: (sessionId: string) => void
  onNewChat: () => void
}

export default function ChatSidebar({
  userId,
  currentSessionId,
  onSessionChange,
  onNewChat
}: ChatSidebarProps) {
  const { theme } = useTheme()
  const [sessions, setSessions] = useState<Session[]>([])
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSessions()
  }, [userId])

  const fetchSessions = async () => {
    try {
      const response = await fetch(`${API_URL}/sessions/${userId}`)
      if (response.ok) {
        const data = await response.json()
        setSessions(data)
      }
    } catch (error) {
      console.error('Error fetching sessions:', error)
    } finally {
      setLoading(false)
    }
  }

  const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Delete this chat?')) return

    try {
      const response = await fetch(`${API_URL}/sessions/${sessionId}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        setSessions(sessions.filter(s => s.session_id !== sessionId))
        if (sessionId === currentSessionId) {
          onNewChat()
        }
      }
    } catch (error) {
      console.error('Error deleting session:', error)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)

    if (diffInHours < 24) {
      return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    } else if (diffInHours < 48) {
      return 'Yesterday'
    } else if (diffInHours < 168) {
      return date.toLocaleDateString('en-US', { weekday: 'short' })
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }
  }

  if (isCollapsed) {
    return (
      <div className={`w-12 border-r flex flex-col items-center py-4 relative z-20 ${
        theme === 'dark' ? 'bg-gray-900 border-gray-800' : 'bg-gray-100 border-gray-200'
      }`}>
        <button
          onClick={() => setIsCollapsed(false)}
          className={`p-2 rounded-lg transition-colors ${
            theme === 'dark' ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-200 text-gray-600'
          }`}
          title="Expand sidebar"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M9 18l6-6-6-6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
        <button
          onClick={onNewChat}
          className={`mt-4 p-2 rounded-lg transition-colors ${
            theme === 'dark' ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-200 text-gray-600'
          }`}
          title="New chat"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M12 5v14m-7-7h14" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </button>
      </div>
    )
  }

  return (
    <div className={`w-64 border-r flex flex-col relative z-20 ${
      theme === 'dark' ? 'bg-gray-900 border-gray-800' : 'bg-gray-100 border-gray-200'
    }`}>
      {/* Header */}
      <div className={`p-4 border-b flex items-center justify-between ${
        theme === 'dark' ? 'border-gray-800' : 'border-gray-200'
      }`}>
        <button
          onClick={onNewChat}
          className={`flex-1 flex items-center gap-2 px-3 py-2 rounded-lg transition-colors text-sm ${
            theme === 'dark'
              ? 'bg-gray-800 hover:bg-gray-700 text-white'
              : 'bg-white hover:bg-gray-200 text-gray-900 border border-gray-300'
          }`}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M12 5v14m-7-7h14" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          New Chat
        </button>
        <button
          onClick={() => setIsCollapsed(true)}
          className={`ml-2 p-2 rounded-lg transition-colors ${
            theme === 'dark' ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-200 text-gray-600'
          }`}
          title="Collapse sidebar"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M15 18l-6-6 6-6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className={`p-4 text-center text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-700'}`}>Loading...</div>
        ) : sessions.length === 0 ? (
          <div className={`p-4 text-center text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-700'}`}>No chats yet</div>
        ) : (
          <div className="py-2">
            {sessions.map((session) => (
              <button
                key={session.session_id}
                onClick={() => onSessionChange(session.session_id)}
                className={`w-full px-4 py-3 text-left transition-colors group relative ${
                  theme === 'dark'
                    ? `hover:bg-gray-800 ${session.session_id === currentSessionId ? 'bg-gray-800' : ''}`
                    : `hover:bg-gray-200 ${session.session_id === currentSessionId ? 'bg-gray-200' : ''}`
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm truncate ${
                      theme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>{session.title}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {formatDate(session.updated_at)}
                    </div>
                  </div>
                  <button
                    onClick={(e) => deleteSession(session.session_id, e)}
                    className={`opacity-0 group-hover:opacity-100 p-1 rounded transition-all hover:text-red-400 ${
                      theme === 'dark' ? 'hover:bg-gray-700 text-gray-400' : 'hover:bg-gray-300 text-gray-600'
                    }`}
                    title="Delete chat"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path d="M18 6L6 18M6 6l12 12" strokeWidth="2" strokeLinecap="round"/>
                    </svg>
                  </button>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
