<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { computed } from 'vue'

interface Props {
  class?: HTMLAttributes['class']
}

const props = defineProps<Props>()

const classes = computed(() => cn(
  /* min-w-0: allow flex children to shrink below CJK min-content (prevents 1-char-wide columns after wrap) */
  'flex w-full min-w-0 flex-col gap-8 p-4',
  props.class,
))
</script>

<template>
  <div :class="classes">
    <slot />
  </div>
</template>
