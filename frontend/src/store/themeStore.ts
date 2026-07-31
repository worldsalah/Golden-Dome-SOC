import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'dark' | 'light'

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

function applyTheme(theme: Theme) {
  const root = document.documentElement
  root.classList.remove('dark', 'light')
  root.classList.add(theme)
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'dark',
      setTheme: (theme) => {
        applyTheme(theme)
        set({ theme })
      },
      toggleTheme: () => {
        const next = get().theme === 'dark' ? 'light' : 'dark'
        applyTheme(next)
        set({ theme: next })
      },
    }),
    {
      name: 'theme-storage',
      onRehydrateStorage: () => (state) => {
        applyTheme(state?.theme ?? 'dark')
      },
      deserialize: (str) => {
        if (!str) return undefined as any
        try {
          return JSON.parse(str)
        } catch {
          return undefined as any
        }
      },
    },
  ),
)

applyTheme(useThemeStore.getState().theme)
