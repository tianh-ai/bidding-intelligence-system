import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface LayoutStore {
  sidebarWidth: number
  aiChatWidth: number
  isSidebarCollapsed: boolean
  
  setSidebarWidth: (width: number) => void
  setAiChatWidth: (width: number) => void
  toggleSidebar: () => void
}

export const useLayoutStore = create<LayoutStore>()(
  persist(
    (set) => ({
      sidebarWidth: 240,
      aiChatWidth: 400,
      isSidebarCollapsed: false,

      setSidebarWidth: (width) => set({ sidebarWidth: width }),
      setAiChatWidth: (width) => set({ aiChatWidth: width }),
      toggleSidebar: () => set((state) => ({ 
        isSidebarCollapsed: !state.isSidebarCollapsed 
      })),
    }),
    {
      name: 'layout-storage',
    }
  )
)
