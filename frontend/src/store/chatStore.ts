import { create } from 'zustand'
import type { ChatMessage } from '@/types'

type ChatModel = {
  id: string
  name: string
}

interface ChatStore {
  messages: ChatMessage[]
  isOpen: boolean
  isLoading: boolean
  conversationId: string | null
  currentModel: ChatModel | null
    setCurrentModel: (model: ChatModel | null) => void
  abortController: AbortController | null
  
  addMessage: (message: ChatMessage) => void
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void
  clearMessages: () => void
  setLoading: (loading: boolean) => void
  toggleChat: () => void
  setConversationId: (id: string) => void
  setAbortController: (controller: AbortController | null) => void
  stopGeneration: () => void
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  isOpen: true,
  isLoading: false,
  conversationId: null,
  abortController: null,
  currentModel: null,

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === id ? { ...message, ...updates } : message
      ),
    })),

  clearMessages: () => {
    const controller = get().abortController
    if (controller) {
      controller.abort()
    }
    set({ messages: [], conversationId: null, isLoading: false, abortController: null })
  },

  setLoading: (loading) => set({ isLoading: loading }),

  toggleChat: () => set((state) => ({ isOpen: !state.isOpen })),

  setConversationId: (id) => set({ conversationId: id }),
  setCurrentModel: (model) => set({ currentModel: model }),

  setAbortController: (controller) => set({ abortController: controller }),

  stopGeneration: () => {
    const controller = get().abortController
    if (controller) {
      controller.abort()
    }
    set({ isLoading: false, abortController: null })
  },
}))
