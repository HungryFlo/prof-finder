<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NDrawer,
  NDrawerContent,
  NSpace,
  NSpin,
  NTag,
  useMessage,
} from 'naive-ui'
import { professorsApi } from '@/api/professors'
import type { Professor } from '@/types'

const props = defineProps<{
  show: boolean
  professorId: number
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'close'): void
}>()

const router = useRouter()
const message = useMessage()
const loading = ref(false)
const professor = ref<Professor | null>(null)

watch(
  () => [props.show, props.professorId] as const,
  async ([show, id]) => {
    if (show && id) {
      loading.value = true
      try {
        professor.value = await professorsApi.get(id)
      } catch (error: unknown) {
        const err = error as { response?: { data?: { detail?: string } } }
        message.error(err.response?.data?.detail || '获取教授信息失败')
        emit('update:show', false)
      } finally {
        loading.value = false
      }
    }
  }
)

function handleViewDetail() {
  if (professor.value) {
    emit('update:show', false)
    router.push(`/professor/${professor.value.id}`)
  }
}

function formatJsonNote(note: unknown): string {
  return typeof note === 'string' ? note : JSON.stringify(note)
}
</script>

<template>
  <n-drawer :show="show" :width="480" @update:show="(val: boolean) => emit('update:show', val)">
    <n-drawer-content
      v-if="professor"
      :title="professor.name"
      :native-scrollbar="false"
    >
      <n-spin :show="loading">
        <n-descriptions :column="1" label-placement="left" bordered>
          <n-descriptions-item label="机构">
            {{ professor.affiliation || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="邮箱">
            {{ professor.email || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="主页">
            <a
              v-if="professor.homepage"
              :href="professor.homepage"
              target="_blank"
            >
              {{ professor.homepage }}
            </a>
            <span v-else>-</span>
          </n-descriptions-item>
          <n-descriptions-item label="Google Scholar">
            <a
              v-if="professor.google_scholar_url"
              :href="professor.google_scholar_url"
              target="_blank"
            >
              查看 Scholar 主页
            </a>
            <span v-else>-</span>
          </n-descriptions-item>
          <n-descriptions-item label="H-Index">
            {{ professor.h_index ?? '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="总引用">
            {{ professor.total_citations ?? '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="研究方向">
            <n-space size="small">
              <n-tag
                v-for="interest in professor.research_interests"
                :key="interest"
                type="info"
                size="small"
              >
                {{ interest }}
              </n-tag>
            </n-space>
            <span v-if="!professor.research_interests?.length">-</span>
          </n-descriptions-item>
        </n-descriptions>

        <template v-if="professor.research_profile">
          <n-divider />
          <h4 style="margin: 8px 0 12px">
            科研画像
            <n-tag
              v-if="professor.research_profile_generated_at"
              size="small"
              type="success"
              style="margin-left: 8px"
            >
              {{ new Date(professor.research_profile_generated_at).toLocaleString('zh-CN') }}
            </n-tag>
          </h4>
          <div
            style="
              white-space: pre-wrap;
              background: var(--n-color-modal);
              padding: 16px;
              border-radius: 6px;
              border: 1px solid var(--n-border-color);
              font-size: 13px;
              line-height: 1.7;
            "
          >
            {{ professor.research_profile }}
          </div>

          <n-space
            v-if="professor.research_profile_evidence?.length"
            vertical
            style="margin-top: 12px"
          >
            <strong>证据摘要</strong>
            <div>
              <n-tag
                v-for="(note, index) in professor.research_profile_evidence"
                :key="index"
                style="margin: 0 8px 8px 0"
              >
                {{ formatJsonNote(note) }}
              </n-tag>
            </div>
          </n-space>

          <n-space
            v-if="professor.research_profile_conflicts?.length"
            vertical
            style="margin-top: 12px"
          >
            <strong>冲突说明</strong>
            <div>
              <n-tag
                v-for="(note, index) in professor.research_profile_conflicts"
                :key="index"
                type="warning"
                style="margin: 0 8px 8px 0"
              >
                {{ formatJsonNote(note) }}
              </n-tag>
            </div>
          </n-space>
        </template>

        <n-divider />
        <n-space justify="end">
          <n-button type="primary" @click="handleViewDetail">
            查看详情
          </n-button>
        </n-space>
      </n-spin>
    </n-drawer-content>
  </n-drawer>
</template>
