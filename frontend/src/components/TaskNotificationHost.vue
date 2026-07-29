<script setup lang="ts">
import { watch } from 'vue'
import { useNotification } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useTaskStore } from '@/stores/tasks'

const taskStore = useTaskStore()
const notification = useNotification()
const { t } = useI18n()

watch(
  () => taskStore.taskEvents.length,
  () => {
    for (const event of taskStore.consumeTaskEvents()) {
      if (event.status === 'completed') {
        notification.success({
          title: t('task.taskCompleted'),
          content: event.message,
          meta: event.taskName,
          duration: 5000,
        })
      } else if (event.status === 'failed') {
        notification.error({
          title: t('task.taskFailed'),
          content: event.message,
          meta: event.taskName,
          duration: 8000,
        })
      } else if (event.status === 'interrupted') {
        notification.warning({
          title: t('task.taskInterrupted'),
          content: event.message,
          meta: event.taskName,
          duration: 8000,
        })
      } else {
        notification.warning({
          title: t('task.taskCancelled'),
          content: event.message,
          meta: event.taskName,
          duration: 5000,
        })
      }
    }
  }
)
</script>

<template>
  <span style="display: none" />
</template>
