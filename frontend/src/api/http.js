const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const detail = data.detail || {}
    const message = typeof detail === 'string' ? detail : (detail.message || '请求失败')
    const error = new Error(message)
    if (typeof detail === 'object' && detail !== null) {
      Object.assign(error, detail)
    }
    throw error
  }

  return response.json()
}

export const http = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) })
}
