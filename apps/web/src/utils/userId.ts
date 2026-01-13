/**
 * Simple user identification system using localStorage
 * Generates a persistent user ID for tracking chat sessions
 */

const USER_ID_KEY = 'clarity_user_id'

export function getUserId(): string {
  if (typeof window === 'undefined') {
    return ''
  }

  let userId = localStorage.getItem(USER_ID_KEY)

  if (!userId) {
    // Generate a simple unique ID
    userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    localStorage.setItem(USER_ID_KEY, userId)
  }

  return userId
}

export function clearUserId(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(USER_ID_KEY)
  }
}
