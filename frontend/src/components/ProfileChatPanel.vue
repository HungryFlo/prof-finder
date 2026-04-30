<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NButton,
  NCard,
  NEmpty,
  NInput,
  NSpace,
  NSpin,
  NThing,
  useMessage,
} from 'naive-ui'
import { profilesApi } from '@/api/profiles'
import { useTaskStore } from '@/stores/tasks'
import type { ChatMessage } from '@/types'

const props = defineProps<{
  profileId: number
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'profile-refreshed'): void
}>()

const message = useMessage()
const taskStore = useTaskStore()
const { t } = useI18n()
const sending = ref(false)
const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const scrollContainer = ref<HTMLElement | null>(null)

watch(
  () => props.visible,
  async (nowVisible) => {
    if (nowVisible && messages.value.length === 0) {
      await sendMessage(t('chat.startPrompt'))
    }
  }
)

async function sendMessage(text?: string) {
  const content = (text ?? inputText.value).trim()
  if (!content) return

  messages.value.push({ role: 'user', content })

  if (!text) {
    inputText.value = ''
  }

  sending.value = true
  try {
    const history = messages.value.slice(0, -1)
    const res = await profilesApi.chat(props.profileId, content, history)
    messages.value.push({ role: 'assistant', content: res.reply })
    await nextTick()
    scrollToBottom()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    const errorMsg = err.response?.data?.detail || t('chat.errorAiFailed')
    messages.value.push({ role: 'assistant', content: t('chat.errorLine', { msg: errorMsg }) })
  } finally {
    sending.value = false
  }
}

async function handleRefine() {
  if (messages.value.length <= 1) {
    message.warning(t('chat.needChatFirst'))
    return
  }

  try {
    const { task_id, message: msg } = await profilesApi.refineFromChat(props.profileId, messages.value) as { task_id: string; message: string }
    message.success(msg || t('chat.refineTaskStarted'))
    taskStore.addTask(task_id, 'profile-refine', t('chat.refineTaskInPanel'), 4, () => {
      message.success(t('chat.refineCompleted'))
      emit('profile-refreshed')
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('chat.refineStartFailed'))
  }
}

function scrollToBottom() {
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
  }
}

function formatRole(role: string): string {
  return role === 'user' ? t('chat.roleMe') : t('chat.roleAi')
}
</script>

<template>
  <n-card :title="$t('chat.title')" size="small" v-if="visible">
    <template #header-extra>
      <n-button
        type="warning"
        size="small"
        @click="handleRefine"
      >
        {{ $t('chat.optimizeProfile') }}
      </n-button>
    </template>

    <div
      ref="scrollContainer"
      class="chat-message-list"
    >
      <n-empty
        v-if="messages.length === 0 && !sending"
        :description="$t('chat.emptyHint')"
        style="margin-top: 24px"
      />

      <n-thing
        v-for="(msg, index) in messages"
        :key="index"
        :class="['chat-message', msg.role === 'user' ? 'chat-user' : 'chat-ai']"
        :title="formatRole(msg.role)"
        :title-extra="msg.role === 'assistant' ? $t('chat.aiInterviewer') : ''"
      >
        <div class="chat-content">{{ msg.content }}</div>
      </n-thing>

      <n-spin v-if="sending" size="small" style="margin: 12px 0" />
    </div>

    <n-space style="margin-top: 12px" align="end">
      <n-input
        v-model:value="inputText"
        type="textarea"
        :rows="3"
        :placeholder="$t('chat.inputPlaceholder')"
        :disabled="sending"
        @keydown.enter.exact.prevent="sendMessage()"
        style="flex: 1"
      />
      <n-button
        type="primary"
        :loading="sending"
        :disabled="!inputText.trim()"
        @click="sendMessage()"
      >
        {{ $t('chat.send') }}
      </n-button>
    </n-space>
  </n-card>
</template>

<style scoped>
.chat-message-list {
  max-height: 560px;
  overflow-y: auto;
  padding-right: 4px;
}

.chat-message {
  margin-bottom: 12px;
}

.chat-content {
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.6;
}
</style>
