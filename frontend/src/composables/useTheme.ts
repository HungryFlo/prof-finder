import { ref, watch } from 'vue'

const STORAGE_KEY = 'prof-finder-theme'

const isDark = ref(false)

// Initialize from localStorage
function initTheme() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'dark') {
    isDark.value = true
  }
  syncClass()
}

function syncClass() {
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// Persist and sync class on changes
watch(isDark, (val) => {
  localStorage.setItem(STORAGE_KEY, val ? 'dark' : 'light')
  syncClass()
})

// Run init immediately on first import
initTheme()

export function useTheme() {
  function toggleTheme() {
    isDark.value = !isDark.value
  }

  return {
    isDark,
    toggleTheme,
  }
}
