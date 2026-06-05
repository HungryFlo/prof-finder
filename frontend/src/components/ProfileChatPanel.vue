<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { NDrawer, NDrawerContent, useMessage } from 'naive-ui'
import type { ChatStatus } from 'ai'
import { Conversation, ConversationContent, ConversationEmptyState, ConversationScrollButton } from '@/components/ai-elements/conversation'
import { Message, MessageContent, MessageResponse, MessageToolbar, MessageActions, MessageAction } from '@/components/ai-elements/message'
import { Suggestions, Suggestion } from '@/components/ai-elements/suggestion'
import { Shimmer } from '@/components/ai-elements/shimmer'
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputTextarea,
  PromptInputSubmit,
  PromptInputTools,
} from '@/components/ai-elements/prompt-input'
import { CopyIcon, RefreshCwIcon } from 'lucide-vue-next'
import { profilesApi } from '@/api/profiles'
import { useApiError } from '@/composables/useApiError'
import { useTaskStore } from '@/stores/tasks'
import type { ChatMessage } from '@/types'

interface ChatEntry {
  key: string
  role: 'user' | 'assistant'
  content: string
  failed?: boolean
}

const { handleApiError } = useApiError()

const props = defineProps<{
  profileId: number
}>()

const show = defineModel<boolean>('show', { default: false })

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

let idCounter = 0
function uid(): string {
  return `${Date.now().toString(36)}-${(idCounter++).toString(36)}`
}

watch(
  () => show.value,
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
    // Throttle token updates with requestAnimationFrame
    let tokenBuffer = ''
    let rafId: number | null = null
    const flushTokens = () => {
      const target = messages.value.find((m) => m.key === assistantKey)
      if (target && tokenBuffer) {
        target.content += tokenBuffer
        tokenBuffer = ''
        messages.value = [...messages.value]
      }
      rafId = null
    }

    await profilesApi.chatStream(
      props.profileId,
      content,
      history,
      (token) => {
        status.value = 'streaming'
        tokenBuffer += token
        if (rafId === null) {
          rafId = requestAnimationFrame(flushTokens)
        }
      },
      () => {
        // Flush any remaining buffered tokens
        if (rafId !== null) {
          cancelAnimationFrame(rafId)
          rafId = null
        }
        flushTokens()
        status.value = 'ready'
        abortController.value = null
      },
      (errorMsg) => {
        const target = messages.value.find((m) => m.key === assistantKey)
        if (target) {
          target.content = t('chat.errorLine', { msg: errorMsg })
          target.failed = true
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
      target.failed = true
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

function handleSuggestion(suggestion: string) {
  sendMessage(suggestion)
}

async function copyMessage(content: string) {
  try {
    await navigator.clipboard.writeText(content)
    message.success(t('chat.copySuccess'))
  } catch {
    message.error(t('common.copyFailed'))
  }
}

function resendFromAssistantTurn(assistantKey: string) {
  const assistantIdx = messages.value.findIndex((m) => m.key === assistantKey)
  if (assistantIdx === -1 || messages.value[assistantIdx]?.role !== 'assistant') return

  const userMsg = messages.value[assistantIdx - 1]
  if (!userMsg || userMsg.role !== 'user') return

  messages.value = messages.value.slice(0, assistantIdx)
  status.value = 'ready'
  sendMessage(userMsg.content)
}

function handleRegenerate(assistantKey: string) {
  resendFromAssistantTurn(assistantKey)
}

function isApiKeyError(content: string): boolean {
  return content.includes('LLM') || content.includes('API Key') || content.includes('503')
}

function handleRetry(assistantKey: string) {
  resendFromAssistantTurn(assistantKey)
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
    const err = error as { response?: { status?: number; data?: { detail?: string } } }
    if (err.response?.status === 503 || isApiKeyError(err.response?.data?.detail || '')) {
      message.warning(t('chat.apiKeyHint'), { duration: 5000 })
    } else {
      handleApiError(error, t('chat.refineStartFailed'))
    }
  }
}
</script>

<template>
  <n-drawer
    v-model:show="show"
    :width="480"
    placement="right"
  >
    <n-drawer-content :title="$t('chat.title')" closable body-content-class="!p-0">
      <template #header>
        <div class="flex items-center justify-between w-full pr-8">
          <h3 class="text-sm font-medium m-0">{{ $t('chat.title') }}</h3>
          <button
            class="inline-flex items-center justify-center gap-2 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
            :disabled="status === 'streaming' || status === 'submitted'"
            @click="handleRefine"
          >
            {{ $t('chat.optimizeProfile') }}
          </button>
        </div>
      </template>

      <div class="flex flex-col h-full">

      <!-- Messages -->
      <Conversation class="min-h-0 flex-1">
        <ConversationContent>
          <ConversationEmptyState
            v-if="messages.length === 0 && status === 'ready'"
            :title="$t('chat.emptyHint')"
          >
            <Suggestions class="mt-4">
              <Suggestion
                :suggestion="$t('chat.suggestResearchExperience')"
                @click="handleSuggestion"
              />
              <Suggestion
                :suggestion="$t('chat.suggestCoreSkills')"
                @click="handleSuggestion"
              />
              <Suggestion
                :suggestion="$t('chat.suggestAcademicGoals')"
                @click="handleSuggestion"
              />
              <Suggestion
                :suggestion="$t('chat.suggestImproveDescription')"
                @click="handleSuggestion"
              />
            </Suggestions>
          </ConversationEmptyState>

          <Message
            v-for="msg in messages"
            :key="msg.key"
            :from="msg.role"
            :class="msg.role === 'assistant' ? '!max-w-full flex-col' : ''"
          >
            <MessageContent :class="msg.role === 'assistant' ? '!w-full' : ''">
              <MessageResponse :content="msg.content" />
            </MessageContent>
            <MessageToolbar v-if="msg.role === 'assistant' && msg.content && (status === 'ready' || status === 'error')">
              <MessageActions>
                <MessageAction
                  :tooltip="$t('chat.actionCopy')"
                  @click="copyMessage(msg.content)"
                >
                  <CopyIcon class="size-4" />
                </MessageAction>
                <MessageAction
                  v-if="!msg.failed && status === 'ready'"
                  :tooltip="$t('chat.actionRegenerate')"
                  @click="handleRegenerate(msg.key)"
                >
                  <RefreshCwIcon class="size-4" />
                </MessageAction>
                <MessageAction
                  v-if="msg.failed"
                  :tooltip="$t('chat.actionRetry')"
                  @click="handleRetry(msg.key)"
                >
                  <RefreshCwIcon class="size-4" />
                </MessageAction>
              </MessageActions>
            </MessageToolbar>
            <div
              v-if="msg.role === 'assistant' && msg.failed && isApiKeyError(msg.content)"
              class="text-xs text-amber-600 dark:text-amber-400 mt-1 px-1"
            >
              {{ $t('chat.apiKeyHint') }}
            </div>
          </Message>

          <ConversationScrollButton />

          <Shimmer
            v-if="(status === 'submitted') && messages.length > 0 && !messages[messages.length - 1]?.content"
            class="px-4 py-2"
          >
            {{ $t('chat.aiThinking') }}
          </Shimmer>
        </ConversationContent>
      </Conversation>

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
    </n-drawer-content>
  </n-drawer>
</template>

<style scoped>
:deep([data-stream-markdown='text-word']) {
  display: inline !important;
}

:deep([data-stream-markdown='text-space']) {
  display: inline !important;
}
</style>
