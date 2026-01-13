'use client'

import { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble'
import LeadForm from './LeadForm'
import ChatInput from './ChatInput'
import AnimatedBackground from './AnimatedBackground'
import ThemeToggle from './ThemeToggle'
import { useTheme } from '@/contexts/ThemeContext'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  citations?: Array<{ title: string; date: string; url: string }>
  showLeadForm?: boolean
  isStreaming?: boolean
  metadata?: {
    files?: Array<{ filename: string; content_type?: string; size?: number }>
  }
}

interface ChatInterfaceProps {
  sessionId: string
  userId: string
  initialQuestion?: string
}

export default function ChatInterface({ sessionId, userId, initialQuestion }: ChatInterfaceProps) {
  const { theme } = useTheme()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'assistant',
      content: "Hi! I'm here to help with your retirement planning questions. What would you like to know?",
    },
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [showLeadGate, setShowLeadGate] = useState(false)
  const [leadCaptured, setLeadCaptured] = useState(false)
  const [bookingUrl, setBookingUrl] = useState<string | null>(null)
  const [pendingMessage, setPendingMessage] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const initialQuestionSentRef = useRef(false)
  const [showScrollPrompt, setShowScrollPrompt] = useState(false)

  // Check if user is at the bottom of the scroll container
  const isAtBottom = () => {
    const container = messagesContainerRef.current
    if (!container) return true
    return container.scrollHeight - container.scrollTop - container.clientHeight < 100
  }

  // Detect when user scrolls
  useEffect(() => {
    const container = messagesContainerRef.current
    if (!container) return

    const handleScroll = () => {
      // Hide scroll prompt if user scrolls to bottom
      if (isAtBottom()) {
        setShowScrollPrompt(false)
      }
    }

    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      container.removeEventListener('scroll', handleScroll)
    }
  }, [])

  // Load existing messages when session changes
  useEffect(() => {
    loadSessionMessages()
  }, [sessionId])

  const loadSessionMessages = async () => {
    setLoadingHistory(true)
    try {
      const response = await fetch(`${API_URL}/sessions/${sessionId}/messages`)
      if (response.ok) {
        const data = await response.json()
        if (data.length > 0) {
          // Session has existing messages, load them
          setMessages(data)
        } else {
          // New session, show welcome message
          setMessages([
            {
              id: '0',
              role: 'assistant',
              content: "Hi! I'm here to help with your retirement planning questions. What would you like to know?",
            },
          ])
        }
      }
    } catch (error) {
      console.error('Error loading messages:', error)
      // On error, show welcome message
      setMessages([
        {
          id: '0',
          role: 'assistant',
          content: "Hi! I'm here to help with your retirement planning questions. What would you like to know?",
        },
      ])
    } finally {
      setLoadingHistory(false)
    }
  }

  // Send initial question if provided
  useEffect(() => {
    if (initialQuestion && !initialQuestionSentRef.current) {
      initialQuestionSentRef.current = true
      // Small delay to let the component mount
      setTimeout(() => {
        sendMessage(initialQuestion)
      }, 100)
    }
  }, [initialQuestion])

  const sendMessage = async (content: string, files?: File[]) => {
    if ((!content.trim() && (!files || files.length === 0)) || isLoading) return

    // Prepare message content - use default if only files provided
    const messageText = content.trim() || (files && files.length > 0 ? 'Please analyze this file.' : '')

    // Prepare display content with file info
    let displayContent = messageText
    if (files && files.length > 0) {
      displayContent += '\n\n📎 ' + files.map(f => f.name).join(', ')
    }

    // Add user message immediately
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: displayContent,
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    // Add empty assistant message for streaming
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      isStreaming: true,
    }
    setMessages((prev) => [...prev, assistantMessage])

    try {
      // Create FormData for file upload
      const formData = new FormData()
      formData.append('session_id', sessionId)
      formData.append('user_id', userId)
      formData.append('message', messageText)

      if (files && files.length > 0) {
        files.forEach((file) => {
          formData.append('files', file)
        })
      }

      const response = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No reader available')
      }

      let buffer = ''
      let fullContent = ''
      let citations: any[] = []
      let lastUpdateTime = 0
      const THROTTLE_MS = 50 // Update UI every 50ms for smoother rendering

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'content') {
              fullContent += data.content

              // Throttle UI updates to reduce jerkiness
              const now = Date.now()
              if (now - lastUpdateTime > THROTTLE_MS) {
                lastUpdateTime = now
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: fullContent, isStreaming: true }
                      : msg
                  )
                )
              }
            } else if (data.type === 'citations') {
              citations = data.citations
            } else if (data.type === 'done') {
              // Final update with complete content
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: fullContent, isStreaming: false, citations }
                    : msg
                )
              )

              // Show scroll prompt if user is not at bottom
              setTimeout(() => {
                if (!isAtBottom()) {
                  setShowScrollPrompt(true)
                }
              }, 100)
            } else if (data.type === 'lead_gate') {
              setPendingMessage(content.trim())
              setShowLeadGate(true)
              setMessages((prev) => [
                ...prev.filter((msg) => msg.id !== assistantMessageId),
                {
                  id: assistantMessageId,
                  role: 'assistant',
                  content: data.content,
                  showLeadForm: true,
                },
              ])
            } else if (data.type === 'error') {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: `Error: ${data.error}`, isStreaming: false }
                    : msg
                )
              )
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: 'Sorry, I encountered an error. Please try again.',
                isStreaming: false,
              }
            : msg
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleLeadSubmit = async (data: {
    firstName: string
    email: string
    phone: string
  }) => {
    try {
      const response = await fetch(`${API_URL}/lead`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          first_name: data.firstName,
          email: data.email,
          phone: data.phone,
          ip_address: '',
          user_agent: navigator.userAgent,
          page_url: window.location.href,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to submit contact info')
      }

      const leadData = await response.json()

      // Mark lead as captured
      setLeadCaptured(true)
      setShowLeadGate(false)
      setBookingUrl(leadData.booking_url)

      // Add confirmation message
      const confirmMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Thank you, ${data.firstName}! I've saved your information. Let's continue our conversation.`,
      }
      setMessages((prev) => [...prev, confirmMessage])

      // If there was a pending message, send it now
      if (pendingMessage) {
        setTimeout(() => {
          sendMessage(pendingMessage)
          setPendingMessage('')
        }, 500)
      }
    } catch (error) {
      console.error('Error submitting lead:', error)
      alert('There was an error submitting your information. Please try again.')
    }
  }

  const openSchedulingLink = () => {
    if (bookingUrl) {
      window.open(bookingUrl, '_blank')
    }
  }

  return (
    <div className={`flex flex-col h-full relative ${theme === 'dark' ? 'bg-black' : 'bg-gray-50'}`}>
      <AnimatedBackground isActive={false} targetElement={null} />

      {/* Header */}
      <div className={`flex items-center justify-between px-6 py-4 border-b relative z-10 ${
        theme === 'dark' ? 'bg-black border-gray-800' : 'bg-gray-50 border-gray-200'
      }`}>
        <div className="w-full max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img
              src={theme === 'dark' ? "/Clarity-logo-full.png" : "/clarity full logo balck.png"}
              alt="Clarity"
              className="h-8 w-auto object-contain"
            />
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            {leadCaptured && bookingUrl && (
              <button
                onClick={openSchedulingLink}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  theme === 'dark'
                    ? 'bg-white text-black hover:bg-gray-200'
                    : 'bg-black text-white hover:bg-gray-800'
                }`}
              >
                Schedule Call
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-6 py-6 relative z-10">
        <div className="w-full max-w-3xl mx-auto space-y-4">
          <div className="pt-32"></div>
          {messages.map((message) => (
            <div key={message.id} className="animate-fadeIn">
              <MessageBubble
                role={message.role}
                content={message.content}
                citations={message.citations}
                isLoading={message.isStreaming}
              />
              {message.showLeadForm && !leadCaptured && (
                <div className="mt-4 animate-slideUp">
                  <LeadForm onSubmit={handleLeadSubmit} />
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Scroll Down Prompt */}
        {showScrollPrompt && (
          <div className="fixed bottom-36 left-1/2 -translate-x-1/2 z-20 animate-fadeIn">
            <button
              onClick={() => {
                messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
                setShowScrollPrompt(false)
              }}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-full shadow-lg transition-all hover:scale-105 ${
                theme === 'dark'
                  ? 'bg-gray-800 text-gray-200 hover:bg-gray-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <span className="text-sm font-medium">Scroll down to view</span>
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                className="animate-bounce"
              >
                <path
                  d="M12 5v14m-7-7l7 7 7-7"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Input */}
      <div className={`border-t px-6 py-4 relative z-10 ${
        theme === 'dark' ? 'border-gray-800 bg-black' : 'border-gray-200 bg-gray-50'
      }`}>
        <div className="w-full max-w-3xl mx-auto">
          <ChatInput
            onSend={sendMessage}
            disabled={isLoading || (showLeadGate && !leadCaptured)}
            placeholder={
              showLeadGate && !leadCaptured
                ? 'Please provide your contact information above to continue...'
                : 'Message Clarity...'
            }
          />
          <p className={`text-xs text-center mt-3 ${
            theme === 'dark' ? 'text-gray-500' : 'text-gray-600'
          }`}>
            Educational information only. Not personalized financial, tax, or legal advice.
          </p>
        </div>
      </div>
    </div>
  )
}
