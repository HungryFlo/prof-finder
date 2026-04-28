<script setup lang="ts">
import { watch } from 'vue'
import { useNotification } from 'naive-ui'
import { useTaskStore } from '@/stores/tasks'

const taskStore = useTaskStore()
const notification = useNotification()

watch(
  () => taskStore.taskEvents.length,
  () => {
    for (const event of taskStore.consumeTaskEvents()) {
      if (event.status === 'completed') {
        notification.success({
          title: '任务已完成',
          content: event.taskName,
          meta: event.message,
          duration: 5000,
        })
      } else {
        notification.error({
          title: '任务失败',
          content: event.taskName,
          meta: event.message,
          duration: 8000,
        })
      }
    }
  }
)
</script>

<template>
  <span style="display: none" />
</template>
