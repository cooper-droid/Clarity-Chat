'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Setting {
  value: any
  type: string
  description: string
}

export default function AdminSettings() {
  const [settings, setSettings] = useState<Record<string, Setting>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    console.log('useEffect triggered')
    fetchSettings()
  }, [])

  // Backup: Also fetch on mount
  useEffect(() => {
    const timer = setTimeout(() => {
      if (Object.keys(settings).length === 0 && !error) {
        console.log('Backup fetch triggered after 1s')
        fetchSettings()
      }
    }, 1000)
    return () => clearTimeout(timer)
  }, [])

  const fetchSettings = async () => {
    console.log('=== FETCH SETTINGS CALLED ===')
    console.log('API_URL:', API_URL)

    try {
      console.log('Fetching from:', `${API_URL}/admin/settings`)
      const response = await fetch(`${API_URL}/admin/settings`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      })

      console.log('Response status:', response.status)
      console.log('Response ok:', response.ok)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log('Fetched settings count:', Object.keys(data).length)
      console.log('Fetched settings:', data)
      setSettings(data)
      setError('')
    } catch (error) {
      console.error('Error fetching settings:', error)
      const errorMsg = error instanceof Error ? error.message : 'Unknown error'
      setError(`Failed to load settings: ${errorMsg}. Make sure the API server is running on port 8000.`)
    } finally {
      console.log('Setting loading to false')
      setLoading(false)
    }
  }

  const updateSetting = async (key: string, value: any) => {
    try {
      const response = await fetch(`${API_URL}/admin/settings/${key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          value,
          type: settings[key].type,
        }),
      })

      if (response.ok) {
        setSettings((prev) => ({
          ...prev,
          [key]: { ...prev[key], value },
        }))
        setMessage(`✓ ${key} updated successfully`)
        setTimeout(() => setMessage(''), 3000)
      }
    } catch (error) {
      console.error('Error updating setting:', error)
      setMessage(`✗ Error updating ${key}`)
    }
  }

  const saveAllSettings = async () => {
    setSaving(true)
    setMessage('Saving all settings...')

    try {
      for (const [key, setting] of Object.entries(settings)) {
        await fetch(`${API_URL}/admin/settings/${key}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            value: setting.value,
            type: setting.type,
          }),
        })
      }
      setMessage('✓ All settings saved successfully')
    } catch (error) {
      console.error('Error saving settings:', error)
      setMessage('✗ Error saving settings')
    } finally {
      setSaving(false)
      setTimeout(() => setMessage(''), 3000)
    }
  }

  const resetSettings = async () => {
    if (!confirm('Are you sure you want to reset all settings to defaults?')) {
      return
    }

    try {
      const response = await fetch(`${API_URL}/admin/settings/reset`, {
        method: 'POST',
      })
      const data = await response.json()
      setSettings(data.settings)
      setMessage('✓ Settings reset to defaults')
      setTimeout(() => setMessage(''), 3000)
    } catch (error) {
      console.error('Error resetting settings:', error)
      setMessage('✗ Error resetting settings')
    }
  }

  const renderSettingInput = (key: string, setting: Setting) => {
    const handleChange = (value: any) => {
      setSettings((prev) => ({
        ...prev,
        [key]: { ...prev[key], value },
      }))
    }

    if (setting.type === 'boolean') {
      return (
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={setting.value}
            onChange={(e) => handleChange(e.target.checked)}
            className="w-4 h-4"
          />
          <span className="text-sm">{setting.value ? 'Enabled' : 'Disabled'}</span>
        </label>
      )
    }

    if (setting.type === 'number') {
      return (
        <input
          type="number"
          value={setting.value}
          onChange={(e) => handleChange(parseFloat(e.target.value))}
          step={key === 'temperature' ? 0.1 : 1}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white text-gray-900"
        />
      )
    }


    return (
      <input
        type="text"
        value={setting.value}
        onChange={(e) => handleChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 bg-white text-gray-900"
      />
    )
  }

  console.log('Admin page render - loading:', loading, 'error:', error, 'settings count:', Object.keys(settings).length)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="text-gray-500 text-xl mb-4">Loading settings...</div>
          <div className="text-gray-400 text-sm">API URL: {API_URL}</div>
          <div className="text-gray-400 text-sm mt-2">Check browser console (F12) for logs</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 p-6">
        <div className="max-w-2xl w-full bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <div className="text-red-600 text-center">
            <h2 className="text-xl font-semibold mb-4">Error Loading Settings</h2>
            <p className="text-sm mb-6">{error}</p>
            <button
              onClick={() => {
                setLoading(true)
                setError('')
                fetchSettings()
              }}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Group settings by category
  const openAISettings = ['openai_api_key', 'openai_prompt_id', 'openai_prompt_version']
  const ragSettings = ['enable_rag', 'rag_chunk_limit', 'enable_citations']
  const leadSettings = ['enable_lead_gate', 'lead_gate_message']
  const uiSettings = ['chat_title', 'chat_subtitle', 'welcome_message', 'schedule_button_text']

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-5xl mx-auto px-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {/* Header */}
          <div className="px-8 py-6 border-b border-gray-200 bg-gradient-to-r from-primary-600 to-primary-700">
            <div className="flex items-center gap-3">
              <img src="/clarity-logo-icon.png" alt="Clarity" className="h-8 w-auto" />
              <div>
                <h1 className="text-2xl font-bold text-white">Admin Settings</h1>
                <p className="text-primary-100 mt-1">Configure your ChatGPT integration and chatbot behavior</p>
              </div>
            </div>
          </div>

          {/* Message */}
          {message && (
            <div className={`px-8 py-3 ${message.includes('✓') ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
              {message}
            </div>
          )}

          <div className="p-8 space-y-8">
            {/* OpenAI Configuration */}
            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">OpenAI Responses API Configuration</h2>
              <div className="space-y-4">
                {openAISettings.map((key) => settings[key] && (
                  <div key={key} className="space-y-2">
                    <label className="block">
                      <span className="text-sm font-medium text-gray-700">
                        {key === 'openai_prompt_id' ? 'Prompt ID' :
                         key === 'openai_prompt_version' ? 'Prompt Version' :
                         key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </span>
                      <p className="text-xs text-gray-500 mt-1">{settings[key].description}</p>
                    </label>
                    {renderSettingInput(key, settings[key])}
                  </div>
                ))}
              </div>
            </section>

            {/* RAG Settings */}
            <section className="pt-6 border-t border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Knowledge Base (RAG)</h2>
              <div className="space-y-4">
                {ragSettings.map((key) => settings[key] && (
                  <div key={key} className="space-y-2">
                    <label className="block">
                      <span className="text-sm font-medium text-gray-700">
                        {key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </span>
                      <p className="text-xs text-gray-500 mt-1">{settings[key].description}</p>
                    </label>
                    {renderSettingInput(key, settings[key])}
                  </div>
                ))}
              </div>
            </section>

            {/* Lead Capture */}
            <section className="pt-6 border-t border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Lead Capture</h2>
              <div className="space-y-4">
                {leadSettings.map((key) => settings[key] && (
                  <div key={key} className="space-y-2">
                    <label className="block">
                      <span className="text-sm font-medium text-gray-700">
                        {key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </span>
                      <p className="text-xs text-gray-500 mt-1">{settings[key].description}</p>
                    </label>
                    {renderSettingInput(key, settings[key])}
                  </div>
                ))}
              </div>
            </section>

            {/* UI Customization */}
            <section className="pt-6 border-t border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">UI Customization</h2>
              <div className="space-y-4">
                {uiSettings.map((key) => settings[key] && (
                  <div key={key} className="space-y-2">
                    <label className="block">
                      <span className="text-sm font-medium text-gray-700">
                        {key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </span>
                      <p className="text-xs text-gray-500 mt-1">{settings[key].description}</p>
                    </label>
                    {renderSettingInput(key, settings[key])}
                  </div>
                ))}
              </div>
            </section>


            {/* Actions */}
            <div className="pt-6 border-t border-gray-200 flex items-center justify-between">
              <button
                onClick={resetSettings}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Reset to Defaults
              </button>
              <div className="flex gap-3">
                <a
                  href="/"
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Back to Chat
                </a>
                <button
                  onClick={saveAllSettings}
                  disabled={saving}
                  className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save All Settings'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">OpenAI Responses API Configuration</h3>
          <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
            <li>Add your <strong>OpenAI API Key</strong> in the field above</li>
            <li>Enter your <strong>Prompt ID</strong> (e.g., pmpt_xxxxx) from the OpenAI platform</li>
            <li>Set the <strong>Prompt Version</strong> (usually "2" for the latest)</li>
            <li>Click <strong>Save All Settings</strong> to apply changes</li>
            <li>Return to the chat to test your configuration</li>
          </ol>
          <div className="mt-4 pt-4 border-t border-blue-200">
            <p className="text-xs text-blue-700">
              <strong>Note:</strong> This application uses the OpenAI Responses API with custom prompts.
              The prompt controls the AI's behavior, system instructions, and model selection.
              To update the AI's behavior or use a different model, modify your prompt in the OpenAI platform,
              then update the Prompt Version here to use the latest version.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
