import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, clearToken } from '../api'

export default function Admin() {
  const [sources, setSources] = useState([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef()
  const navigate = useNavigate()

  async function loadSources() {
    const res = await apiFetch('/api/v1/sources')
    if (res && res.ok) setSources(await res.json())
  }

  useEffect(() => { loadSources() }, [])

  async function handleUpload(e) {
    e.preventDefault()
    const file = fileRef.current?.files[0]
    if (!file) return
    setUploading(true)
    setError('')
    const form = new FormData()
    form.append('file', file)
    const res = await fetch('/api/v1/sources', {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      body: form,
    })
    setUploading(false)
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      setError(body.detail || 'Upload failed')
    } else {
      fileRef.current.value = ''
      loadSources()
    }
  }

  async function handleDelete(sourceId) {
    await apiFetch(`/api/v1/sources/${sourceId}`, { method: 'DELETE' })
    setSources((prev) => prev.filter((s) => s.source_id !== sourceId))
  }

  return (
    <div className="max-w-3xl mx-auto py-10 px-4">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Knowledge Base</h1>
        <div className="flex gap-3">
          <button
            onClick={() => navigate('/chat')}
            className="text-sm text-indigo-600 hover:underline"
          >
            Go to Chat
          </button>
          <button
            onClick={() => { clearToken(); navigate('/login') }}
            className="text-sm text-gray-500 hover:underline"
          >
            Sign Out
          </button>
        </div>
      </div>

      <form onSubmit={handleUpload} className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="font-semibold mb-4">Upload Document</h2>
        <div className="flex gap-3 items-center">
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            className="text-sm text-gray-600"
          />
          <button
            type="submit"
            disabled={uploading}
            className="bg-indigo-600 text-white rounded px-4 py-2 text-sm hover:bg-indigo-700 disabled:opacity-50"
          >
            {uploading ? 'Uploading…' : 'Upload'}
          </button>
        </div>
        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      </form>

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b font-semibold">Sources ({sources.length})</div>
        {sources.length === 0 ? (
          <p className="px-6 py-8 text-gray-400 text-sm text-center">No documents uploaded yet.</p>
        ) : (
          <ul className="divide-y">
            {sources.map((s) => (
              <li key={s.source_id} className="px-6 py-4 flex justify-between items-center">
                <div>
                  <p className="font-medium text-sm">{s.filename}</p>
                  <p className="text-xs text-gray-400">
                    {s.chunk_count ?? 0} chunks · {s.status}
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(s.source_id)}
                  className="text-red-500 text-sm hover:underline"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
