import { create } from 'zustand'
import type { User } from '@/types'
import { STORAGE_KEYS, UserRole } from '@/config/constants'

interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
  updateUser: (user: Partial<User>) => void
  hasPermission: (permission: string) => boolean
}

const getStoredAuth = () => {
  if (typeof window === 'undefined') {
    return { user: null, token: null }
  }

  const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN)
  const rawUser = localStorage.getItem(STORAGE_KEYS.USER_INFO)

  if (!token || !rawUser) {
    return { user: null, token: null }
  }

  try {
    return { user: JSON.parse(rawUser) as User, token }
  } catch (error) {
    console.warn('Failed to parse stored user info:', error)
    localStorage.removeItem(STORAGE_KEYS.USER_INFO)
    return { user: null, token: null }
  }
}

const storedAuth = getStoredAuth()

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: storedAuth.user,
  token: storedAuth.token,
  isAuthenticated: Boolean(storedAuth.user && storedAuth.token),

  login: (token, user) => {
    set({ token, user, isAuthenticated: true })
    localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token)
    localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(user))
  },

  logout: () => {
    set({ token: null, user: null, isAuthenticated: false })
    localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER_INFO)
  },

  updateUser: (userData) => {
    const currentUser = get().user
    if (currentUser) {
      const updated = { ...currentUser, ...userData }
      set({ user: updated })
      localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(updated))
    }
  },

  hasPermission: (permission) => {
    const user = get().user
    if (!user) return false
    if (user.role === UserRole.ADMIN) return true
    return user.permissions?.includes(permission) ?? false
  },
}))
