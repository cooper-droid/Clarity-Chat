'use client'

import { useState } from 'react'
import AnimatedBackground from './AnimatedBackground'
import ThemeToggle from './ThemeToggle'
import EnhancedChatBox from './EnhancedChatBox'
import { useTheme } from '@/contexts/ThemeContext'

interface LandingPageProps {
  onGetStarted: (question?: string) => void
}

export default function LandingPage({ onGetStarted }: LandingPageProps) {
  const { theme } = useTheme()

  return (
    <div className={`relative min-h-screen overflow-hidden ${theme === 'dark' ? 'bg-black' : 'bg-gray-50'}`}>
      <AnimatedBackground isActive={false} targetElement={null} />

      {/* Top Right Controls */}
      <div className="absolute top-6 right-6 z-20 flex items-center gap-3">
        <button
          onClick={() => onGetStarted()}
          className={`px-6 py-2 text-sm font-medium rounded-lg transition-colors ${
            theme === 'dark'
              ? 'bg-white text-black hover:bg-gray-200'
              : 'bg-black text-white hover:bg-gray-800'
          }`}
        >
          Get Started
        </button>
        <ThemeToggle />
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-6 pt-16 md:pt-20">
        {/* Large Clarity Logo with Fog Effect */}
        <div className="mb-12 text-center relative">
          {/* Fog Effect */}
          <div className="absolute inset-0 -top-20 -left-20 -right-20 pointer-events-none">
            {/* Top fog */}
            <div
              className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[200px] blur-[80px] opacity-30"
              style={{
                background: theme === 'dark'
                  ? 'radial-gradient(ellipse at center, rgba(59, 130, 246, 0.3) 0%, transparent 70%)'
                  : 'radial-gradient(ellipse at center, rgba(96, 165, 250, 0.4) 0%, transparent 70%)'
              }}
            />
            {/* Left fog */}
            <div
              className="absolute top-10 left-0 w-[300px] h-[300px] blur-[60px] opacity-20"
              style={{
                background: theme === 'dark'
                  ? 'radial-gradient(circle at center, rgba(147, 51, 234, 0.3) 0%, transparent 70%)'
                  : 'radial-gradient(circle at center, rgba(168, 85, 247, 0.3) 0%, transparent 70%)'
              }}
            />
            {/* Right fog */}
            <div
              className="absolute top-10 right-0 w-[300px] h-[300px] blur-[60px] opacity-20"
              style={{
                background: theme === 'dark'
                  ? 'radial-gradient(circle at center, rgba(59, 130, 246, 0.3) 0%, transparent 70%)'
                  : 'radial-gradient(circle at center, rgba(96, 165, 250, 0.3) 0%, transparent 70%)'
              }}
            />
          </div>

          {/* Logo - in front of fog */}
          <div className="relative z-10">
            <img
              src={theme === 'dark' ? "/Clarity-logo-full.png" : "/clarity full logo balck.png"}
              alt="Clarity"
              className="w-auto h-[120px] md:h-[180px] lg:h-[220px] object-contain mx-auto"
            />
          </div>
        </div>

        {/* Enhanced Chat Box */}
        <div className="w-full max-w-2xl mb-12">
          <EnhancedChatBox onQuestionClick={(question) => onGetStarted(question)} />
        </div>

        {/* Bottom Section - Text and Icons */}
        <div className="absolute bottom-20 left-0 right-0 flex flex-col items-center gap-6 px-6">
          <p className={`text-2xl md:text-3xl font-bold text-center ${
            theme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>
            You have <span className="underline decoration-blue-500 decoration-2 underline-offset-4">retirement</span> questions, we have answers.
          </p>
          <p className={`text-base md:text-lg font-semibold text-center ${
            theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
          }`}>
            1m+ educational data points | Fiat's Retirement: Redefined Framework | Built for Retirement
          </p>

          {/* Icon Row */}
          <div className="flex items-center justify-center gap-4">
            {/* Lightning Bolt Icon */}
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-gray-100 border border-gray-300'
            }`}>
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="text-yellow-500"
              >
                <path
                  d="M13 2L3 14h8l-1 8 10-12h-8l1-8z"
                  fill="currentColor"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>

            {/* Fiat Tree Icon */}
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-gray-100 border border-gray-300'
            }`}>
              <img
                src="/FiatWM_Icon_White_outline.png"
                alt="Fiat"
                className={`w-6 h-6 object-contain ${
                  theme === 'dark' ? 'brightness-100' : 'brightness-0'
                }`}
              />
            </div>

            {/* Checkmark Icon */}
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-gray-100 border border-gray-300'
            }`}>
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="text-green-500"
              >
                <path
                  d="M20 6L9 17l-5-5"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Footer - positioned at the very bottom */}
      <div className="relative z-10 mt-auto pb-8">
        {/* Gradient Line */}
        <div className="w-full h-[1px] mb-3" style={{
          background: theme === 'dark'
            ? 'linear-gradient(to right, transparent 0%, white 20%, white 80%, transparent 100%)'
            : 'linear-gradient(to right, transparent 0%, black 20%, black 80%, transparent 100%)'
        }}></div>

        {/* Footer Content */}
        <div className="flex items-center justify-between px-6 max-w-7xl mx-auto">
          {/* Copyright Text */}
          <p className={`text-xs ${
            theme === 'dark' ? 'text-gray-500' : 'text-gray-600'
          }`}>
            All rights reserved by Fiat Labs, 2026
          </p>

          {/* Right Side Text */}
          <p className={`text-xs italic ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
          }`}>
            Built & Trained on Fiat's Wealth Management's Retirement Education platform.
          </p>
        </div>
      </div>
    </div>
  )
}
