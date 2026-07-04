const API_URL = 'http://localhost:8000'

/**
 * Login — sends form-data (username=email, password)
 * because the backend now uses OAuth2PasswordRequestForm.
 * Swagger also uses form-data, so both work identically.
 */
export async function login(email, password) {
  const body = new URLSearchParams()
  body.append('username', email)   // OAuth2 spec calls it "username"
  body.append('password', password)

  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Ошибка авторизации')
  }

  return response.json() // { access_token, token_type }
}

export async function getMe(token) {
  const response = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) return null
  return response.json()
}
