import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, clearToken, getToken } from '../api'

export default function Chat() {
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef()
  const navigate = useNavigate()

  useEffect(() => { loadConversations() }, [])
  useEffect(() => { if (activeId) loadMessages(activeId) }, [activeId])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function loadConversations() {
    const res = await apiFetch('/api/v1/conversations')
    if (res && res.ok) setConversations(await res.json())
  }

  async function loadMessages(convId) {
    const res = await apiFetch(`/api/v1/conversations/${convId}/messages`)
    if (res && res.ok) setMessages(await res.json())
  }

  async function newConversation() {
    const res = await apiFetch('/api/v1/conversations', {
      method: 'POST',
      body: JSON.stringify({ title: 'New conversation' }),
    })
    if (res && res.ok) {
      const conv = await res.json()
      setConversations((prev) => [conv, ...prev])
      setActiveId(conv.conversation_id)
      setMessages([])
    }
  }

  async function sendMessage(e) {
    e.preventDefault()
    if (!input.trim() || !activeId || streaming) return
    const userMsg = input
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setStreaming(true)

    const assistantPlaceholder = { role: 'assistant', content: '' }
    setMessages((prev) => [...prev, assistantPlaceholder])

    try {
      const res = await fetch(`/api/v1/conversations/${activeId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ content: userMsg }),
      })

      if (!res.ok || !res.body) {
        setStreaming(false)
        return
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') continue
          setMessages((prev) => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: updated[updated.length - 1].content + data,
            }
            return updated
          })
        }
      }
    } finally {
      setStreaming(false)
    }
  }

  async function deleteConversation(convId, e) {
    e.stopPropagation()
    await apiFetch(`/api/v1/conversations/${convId}`, { method: 'DELETE' })
    setConversations((prev) => prev.filter((c) => c.conversation_id !== convId))
    if (activeId === convId) { setActiveId(null); setMessages([]) }
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <button
            onClick={newConversation}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded px-3 py-2 text-sm font-medium"
          >
            + New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {conversations.map((c) => (
            <div
              key={c.conversation_id}
              onClick={() => setActiveId(c.conversation_id)}
              className={`flex justify-between items-center px-4 py-3 cursor-pointer hover:bg-gray-800 text-sm ${
                activeId === c.conversation_id ? 'bg-gray-800' : ''
              }`}
            >
              <span className="truncate">{c.title}</span>
              <button
                onClick={(e) => deleteConversation(c.conversation_id, e)}
                className="text-gray-500 hover:text-red-400 ml-2 flex-shrink-0"
              >
                &times;
              </button>
            </div>
          ))}
        </div>
        <div className="p-4 border-t border-gray-700 flex gap-2">
          <button
            onClick={() => navigate('/admin')}
            className="flex-1 text-xs text-gray-400 hover:text-white"
          >
            Admin
          </button>
          <button
            onClick={() => { clearToken(); navigate('/login') }}
            className="flex-1 text-xs text-gray-400 hover:text-white"
          >
            Sign Out
          </button>
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {!activeId ? (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <p className="text-lg">Select a conversation or start a new one</p>
              <button
                onClick={newConversation}
                className="mt-4 bg-indigo-600 text-white rounded px-6 py-2 text-sm hover:bg-indigo-700"
              >
                New Chat
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-2xl rounded-lg px-4 py-3 text-sm whitespace-pre-wrap ${
                      m.role === 'user'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white border shadow-sm text-gray-800'
                    }`}
                  >
                    {m.content || (streaming && i === messages.length - 1 ? '▌' : '')}
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            <form onSubmit={sendMessage} className="p-4 border-t bg-white flex gap-3">
              <input
                className="flex-1 border rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                placeholder="Ask a question…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={streaming}
              />
              <button
                type="submit"
                disabled={streaming || !input.trim()}
                className="bg-indigo-600 text-white rounded-lg px-5 py-2 text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                {streaming ? '…' : 'Send'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
