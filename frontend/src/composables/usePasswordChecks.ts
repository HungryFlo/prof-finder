import { computed, type Ref } from 'vue'

export function usePasswordChecks(password: Ref<string>) {
  const checks = computed(() => {
    const pwd = password.value
    return {
      minLength: pwd.length >= 6,
      maxLength: pwd.length <= 100,
    }
  })

  return { passwordChecks: checks }
}
