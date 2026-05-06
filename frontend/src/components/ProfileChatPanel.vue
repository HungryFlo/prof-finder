<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import type { ChatStatus } from 'ai'
import { Conversation, ConversationContent, ConversationEmptyState } from '@/components/ai-elements/conversation'
import { Message, MessageContent, MessageResponse } from '@/components/ai-elements/message'
import { Shimmer } from '@/components/ai-elements/shimmer'
import { Suggestion, Suggestions } from '@/components/ai-elements/suggestion'
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputTextarea,
  PromptInputSubmit,
  PromptInputTools,
} from '@/components/ai-elements/prompt-input'
import { profilesApi } from '@/api/profiles'
import { useTaskStore } from '@/stores/tasks'
import type { ChatMessage } from '@/types'

interface ChatEntry {
  key: string
  role: 'user' | 'assistant'
  content: string
}

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

const messages = ref<ChatEntry[]>([])
const status = ref<ChatStatus>('ready')
const abortController = ref<AbortController | null>(null)
const hasInteracted = ref(false)

const suggestions = [
  t('chat.suggestProfileStrengths'),
  t('chat.suggestImproveDescription'),
  t('chat.suggestAddProjects'),
  t('chat.suggestTailorForPhD'),
]

let idCounter = 0
function uid(): string {
  return `${Date.now().toString(36)}-${(idCounter++).toString(36)}`
}

watch(
  () => props.visible,
  async (nowVisible) => {
    if (nowVisible && messages.value.length === 0 && !hasInteracted.value) {
      await sendMessage(t('chat.startPrompt'))
    }
  },
)

async function sendMessage(text?: string) {
  const content = (text ?? '').trim()
  if (!content || status.value === 'streaming' || status.value === 'submitted') return

  hasInteracted.value = true

  messages.value = [...messages.value, { key: uid(), role: 'user', content }]

  const assistantKey = uid()
  messages.value = [...messages.value, { key: assistantKey, role: 'assistant', content: '' }]

  status.value = 'submitted'
  const controller = new AbortController()
  abortController.value = controller

  const history: ChatMessage[] = messages.value
    .filter((m) => m.key !== assistantKey)
    .slice(0, -1)
    .map((m) => ({ role: m.role, content: m.content }))

  try {
    await profilesApi.chatStream(
      props.profileId,
      content,
      history,
      (token) => {
        status.value = 'streaming'
        const target = messages.value.find((m) => m.key === assistantKey)
        if (target) {
          target.content += token
          messages.value = [...messages.value]
        }
      },
      () => {
        status.value = 'ready'
        abortController.value = null
      },
      (errorMsg) => {
        const target = messages.value.find((m) => m.key === assistantKey)
        if (target) {
          target.content = t('chat.errorLine', { msg: errorMsg })
          messages.value = [...messages.value]
        }
        status.value = 'error'
        abortController.value = null
      },
      controller.signal,
    )
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      status.value = 'ready'
      abortController.value = null
      return
    }
    const target = messages.value.find((m) => m.key === assistantKey)
    if (target && !target.content) {
      target.content = t('chat.errorLine', { msg: t('chat.errorAiFailed') })
      messages.value = [...messages.value]
    }
    status.value = 'error'
    abortController.value = null
  }
}

function handleSubmit(payload: { text: string; files: unknown[] }) {
  if (payload.text?.trim()) {
    sendMessage(payload.text)
  }
}

function handleSuggestionClick(suggestion: string) {
  sendMessage(suggestion)
}

async function handleRefine() {
  if (messages.value.length <= 1) {
    message.warning(t('chat.needChatFirst'))
    return
  }

  try {
    const history: ChatMessage[] = messages.value.map((m) => ({
      role: m.role,
      content: m.content,
    }))
    const { task_id, message: msg } = (await profilesApi.refineFromChat(
      props.profileId,
      history,
    )) as { task_id: string; message: string }
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
</script>

<template>
  <div
    v-if="visible"
    class="relative flex h-full w-full flex-col overflow-hidden rounded-lg border bg-background"
  >
    <!-- Header -->
    <div class="flex items-center justify-between border-b px-4 py-3 shrink-0">
      <h3 class="text-sm font-medium">{{ $t('chat.title') }}</h3>
      <button
        class="inline-flex items-center justify-center gap-2 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
        :disabled="status === 'streaming' || status === 'submitted'"
        @click="handleRefine"
      >
        {{ $t('chat.optimizeProfile') }}
      </button>
    </div>

    <!-- Messages -->
    <Conversation class="min-h-0 flex-1">
      <ConversationContent>
        <ConversationEmptyState
          v-if="messages.length === 0 && status === 'ready'"
          :title="$t('chat.emptyHint')"
        />

        <Message
          v-for="msg in messages"
          :key="msg.key"
          :from="msg.role"
          :class="msg.role === 'assistant' ? '!max-w-full' : ''"
        >
          <MessageContent :class="msg.role === 'assistant' ? '!w-full' : ''">
            <MessageResponse :content="msg.content" />
          </MessageContent>
        </Message>

        <Shimmer
          v-if="(status === 'submitted') && messages.length > 0 && !messages[messages.length - 1]?.content"
          class="px-4 py-2"
        >
          {{ $t('chat.aiThinking') }}
        </Shimmer>
      </ConversationContent>
    </Conversation>

    <!-- Suggestions -->
    <div
      v-if="status === 'ready' && messages.length > 0"
      class="shrink-0 border-t px-4 py-3"
    >
      <Suggestions>
        <Suggestion
          v-for="suggestion in suggestions"
          :key="suggestion"
          :suggestion="suggestion"
          @click="handleSuggestionClick"
        />
      </Suggestions>
    </div>

    <!-- Input -->
    <div class="shrink-0 border-t px-4 py-3">
      <PromptInput
        class="w-full"
        @submit="handleSubmit"
      >
        <PromptInputBody>
          <PromptInputTextarea
            :placeholder="$t('chat.inputPlaceholder')"
            :disabled="status === 'streaming' || status === 'submitted'"
          />
        </PromptInputBody>

        <PromptInputFooter>
          <PromptInputTools>
            <span
              v-if="status === 'streaming' || status === 'submitted'"
              class="text-xs text-muted-foreground"
            >
              {{ $t('chat.streamingHint') }}
            </span>
          </PromptInputTools>

          <PromptInputSubmit
            :status="status"
            :disabled="status === 'streaming' || status === 'submitted'"
          />
        </PromptInputFooter>
      </PromptInput>
    </div>
  </div>
</template>

<style scoped>
:deep([data-stream-markdown='text-word']) {
  display: inline !important;
}

:deep([data-stream-markdown='text-space']) {
  display: inline !important;
}
</style>
