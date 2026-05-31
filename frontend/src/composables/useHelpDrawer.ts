import { ref } from 'vue'

const showHelp = ref(false)

export function useHelpDrawer() {
  function openHelp() {
    showHelp.value = true
  }

  function closeHelp() {
    showHelp.value = false
  }

  return { showHelp, openHelp, closeHelp }
}
