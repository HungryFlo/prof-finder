<script setup lang="ts">
import { h, watch } from 'vue'
import { NButton, useNotification } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useTaskStore } from '@/stores/tasks'
import { useErrorDetailStore } from '@/stores/errorDetail'

const taskStore = useTaskStore()
const errorDetail = useErrorDetailStore()
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
        const friendly = event.message || t('task.taskFailed')
        const detail = event.detail || ''
        notification.error({
          title: t('task.taskFailed'),
          content: friendly,
          meta: event.taskName,
          duration: 8000,
          action: detail
            ? () =>
                h(
                  NButton,
                  {
                    text: true,
                    type: 'primary',
                    size: 'small',
                    onClick: () =>
                      errorDetail.openRaw({
                        friendlyMessage: friendly,
                        detail,
                      }),
                  },
                  { default: () => t('common.errorDetails') },
                )
            : undefined,
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
