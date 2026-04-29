<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
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
const sending = ref(false)
const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const scrollContainer = ref<HTMLElement | null>(null)

watch(
  () => props.visible,
  async (nowVisible) => {
    if (nowVisible && messages.value.length === 0) {
      await sendMessage('开始')
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
    const errorMsg = err.response?.data?.detail || 'AI 响应失败，请重试'
    messages.value.push({ role: 'assistant', content: `[错误] ${errorMsg}` })
  } finally {
    sending.value = false
  }
}

async function handleRefine() {
  if (messages.value.length <= 1) {
    message.warning('请先与 AI 进行至少一轮对话')
    return
  }

  try {
    const { task_id, message: msg } = await profilesApi.refineFromChat(props.profileId, messages.value) as { task_id: string; message: string }
    message.success(msg || '画像优化任务已启动')
    taskStore.addTask(task_id, 'profile-refine', '优化学生画像', 4, () => {
      message.success('学生画像优化完成')
      emit('profile-refreshed')
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '启动优化任务失败')
  }
}

function scrollToBottom() {
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
  }
}

function formatRole(role: string): string {
  return role === 'user' ? '我' : 'AI'
}
</script>

<template>
  <n-card title="AI 画像优化" size="small" v-if="visible">
    <template #header-extra>
      <n-button
        type="warning"
        size="small"
        @click="handleRefine"
      >
        优化画像
      </n-button>
    </template>

    <div
      ref="scrollContainer"
      class="chat-message-list"
    >
      <n-empty
        v-if="messages.length === 0 && !sending"
        description="AI 将根据你的画像分析提出优化问题"
        style="margin-top: 24px"
      />

      <n-thing
        v-for="(msg, index) in messages"
        :key="index"
        :class="['chat-message', msg.role === 'user' ? 'chat-user' : 'chat-ai']"
        :title="formatRole(msg.role)"
        :title-extra="msg.role === 'assistant' ? 'AI 面试官' : ''"
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
        placeholder="输入你的回答..."
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
        发送
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
