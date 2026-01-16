'use client'

import { useTheme } from '@/contexts/ThemeContext'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import ThinkingAnimation from './ThinkingAnimation'

interface Citation {
  title: string
  date: string
  url: string
}

interface MessageBubbleProps {
  role: 'user' | 'assistant' | 'system'
  content: string
  citations?: Citation[]
  isLoading?: boolean
}

export default function MessageBubble({
  role,
  content,
  citations,
  isLoading = false,
}: MessageBubbleProps) {
  const { theme } = useTheme()

  if (role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-full bg-blue-600 text-white rounded-2xl px-5 py-3.5">
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-full">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 overflow-hidden bg-white">
            <img
              src="/Brand Mark black.png"
              alt="Clarity"
              className="w-full h-full object-cover"
            />
          </div>
          <div className="flex-1">
            <div className={`rounded-2xl px-5 py-3.5 ${
              theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50 border border-gray-300'
            }`}>
              {isLoading && content === '' ? (
                <ThinkingAnimation />
              ) : (
                <>
                  <div className={`text-[15px] leading-relaxed prose prose-sm max-w-none ${
                    theme === 'dark'
                      ? 'prose-invert prose-headings:text-gray-100 prose-p:text-gray-200 prose-strong:text-white prose-table:text-gray-200 text-gray-200'
                      : 'prose-headings:text-gray-900 prose-p:text-gray-900 prose-strong:text-black prose-table:text-gray-900 text-gray-900'
                  }`}>
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        table: ({ node, ...props }) => (
                          <div className="overflow-x-auto my-4">
                            <table className={`min-w-full border-collapse ${
                              theme === 'dark' ? 'border-gray-700' : 'border-gray-300'
                            }`} {...props} />
                          </div>
                        ),
                        thead: ({ node, ...props }) => (
                          <thead className={theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'} {...props} />
                        ),
                        th: ({ node, ...props }) => (
                          <th className={`border px-4 py-2 text-left font-semibold ${
                            theme === 'dark' ? 'border-gray-600 text-gray-100' : 'border-gray-400 text-black'
                          }`} {...props} />
                        ),
                        td: ({ node, ...props }) => (
                          <td className={`border px-4 py-2 ${
                            theme === 'dark' ? 'border-gray-600 text-gray-200' : 'border-gray-400 text-gray-900'
                          }`} {...props} />
                        ),
                        h1: ({ node, ...props }) => (
                          <h1 className={`text-2xl font-bold mt-6 mb-3 ${
                            theme === 'dark' ? 'text-gray-100' : 'text-gray-900'
                          }`} {...props} />
                        ),
                        h2: ({ node, ...props }) => (
                          <h2 className={`text-xl font-bold mt-5 mb-2 ${
                            theme === 'dark' ? 'text-gray-100' : 'text-gray-900'
                          }`} {...props} />
                        ),
                        h3: ({ node, ...props }) => (
                          <h3 className={`text-lg font-semibold mt-4 mb-2 ${
                            theme === 'dark' ? 'text-gray-100' : 'text-gray-900'
                          }`} {...props} />
                        ),
                        p: ({ node, ...props }) => (
                          <p className={`mb-3 ${
                            theme === 'dark' ? 'text-gray-200' : 'text-gray-900'
                          }`} {...props} />
                        ),
                        ul: ({ node, ...props }) => (
                          <ul className={`list-disc list-inside mb-3 space-y-1 ${
                            theme === 'dark' ? 'text-gray-200' : 'text-gray-900'
                          }`} {...props} />
                        ),
                        ol: ({ node, ...props }) => (
                          <ol className={`list-decimal list-inside mb-3 space-y-1 ${
                            theme === 'dark' ? 'text-gray-200' : 'text-gray-900'
                          }`} {...props} />
                        ),
                        li: ({ node, ...props }) => (
                          <li className={theme === 'dark' ? 'text-gray-200' : 'text-gray-900'} {...props} />
                        ),
                        em: ({ node, ...props }) => (
                          <em className={theme === 'dark' ? 'text-gray-200' : 'text-gray-900'} {...props} />
                        ),
                        strong: ({ node, ...props }) => (
                          <strong className={`font-semibold ${
                            theme === 'dark' ? 'text-white' : 'text-black'
                          }`} {...props} />
                        ),
                        code: ({ node, ...props }) => (
                          <code className={`px-1.5 py-0.5 rounded ${
                            theme === 'dark' ? 'bg-gray-700 text-gray-200' : 'bg-gray-100 text-gray-900'
                          }`} {...props} />
                        ),
                      }}
                    >
                      {content}
                    </ReactMarkdown>
                    {isLoading && (
                      <span className={`inline-block w-1.5 h-4 animate-pulse ml-0.5 ${
                        theme === 'dark' ? 'bg-gray-400' : 'bg-gray-600'
                      }`}></span>
                    )}
                  </div>

                {citations && citations.length > 0 && (
                  <div className={`mt-4 pt-3 border-t ${
                    theme === 'dark' ? 'border-gray-700' : 'border-gray-300'
                  }`}>
                    <p className={`text-sm font-semibold mb-2 ${
                      theme === 'dark' ? 'text-blue-400' : 'text-blue-600'
                    }`}>Related Resources:</p>
                    <div className="space-y-1.5">
                      {citations.map((citation, idx) => {
                        // Check if URL is a PowerPoint file
                        const isPowerPoint = citation.url && (
                          citation.url.toLowerCase().endsWith('.ppt') ||
                          citation.url.toLowerCase().endsWith('.pptx') ||
                          citation.title.toLowerCase().includes('.ppt')
                        )

                        // Only show link if it's a valid URL and not a PowerPoint
                        const showLink = citation.url && !isPowerPoint &&
                          (citation.url.startsWith('http://') || citation.url.startsWith('https://'))

                        return (
                          <div key={idx} className="text-sm">
                            {showLink ? (
                              <a
                                href={citation.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={`hover:underline transition-colors ${
                                  theme === 'dark' ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-700'
                                }`}
                              >
                                • {citation.title}
                              </a>
                            ) : (
                              <span className={theme === 'dark' ? 'text-blue-400' : 'text-blue-600'}>
                                • {citation.title}
                              </span>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </>
            )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
