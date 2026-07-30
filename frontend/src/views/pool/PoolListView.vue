<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NCard,
  NSpace,
  NButton,
  NDataTable,
  NPopconfirm,
  NModal,
  NForm,
  NFormItem,
  NInput,
  useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useFormatDate } from '@/composables/useDateLocale'
import { useApiError } from '@/composables/useApiError'
import { poolsApi } from '@/api/pools'
import type { ExperiencePool } from '@/types'

const router = useRouter()
const message = useMessage()
const { t } = useI18n()
const { handleApiError } = useApiError()
const { formatDateTime } = useFormatDate()

const loading = ref(false)
const pools = ref<ExperiencePool[]>([])
const showCreate = ref(false)
const creating = ref(false)
const createTitle = ref('')
const createDescription = ref('')

const columns = computed<DataTableColumns<ExperiencePool>>(() => [
  {
    title: t('pool.title'),
    key: 'title',
    ellipsis: { tooltip: true },
  },
  {
    title: t('pool.seeds'),
    key: 'seed_count',
    width: 100,
  },
  {
    title: t('pool.stories'),
    key: 'story_count',
    width: 120,
  },
  {
    title: t('pool.phase'),
    key: 'phase',
    width: 120,
    render(row) {
      return t(`pool.phases.${row.phase}` as 'pool.phases.brainstorm')
    },
  },
  {
    title: t('pool.updatedAt'),
    key: 'updated_at',
    width: 180,
    render(row) {
      return formatDateTime(row.updated_at)
    },
  },
  {
    title: t('pool.actions'),
    key: 'actions',
    width: 220,
    render(row) {
      return h(NSpace, { size: 'small' }, () => [
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            onClick: () => router.push(`/pool/${row.id}`),
          },
          { default: () => t('pool.open') }
        ),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row.id) },
          {
            trigger: () =>
              h(NButton, { size: 'small', type: 'error' }, { default: () => t('common.delete') }),
            default: () => t('pool.deleteConfirm'),
          }
        ),
      ])
    },
  },
])

async function fetchPools() {
  loading.value = true
  try {
    pools.value = await poolsApi.list()
  } catch (error: unknown) {
    handleApiError(error, t('pool.fetchFailed'))
  } finally {
    loading.value = false
  }
}

async function handleCreate(): Promise<boolean> {
  if (!createTitle.value.trim()) {
    message.warning(t('pool.titleRequired'))
    return false
  }
  creating.value = true
  try {
    const pool = await poolsApi.create({
      title: createTitle.value.trim(),
      description: createDescription.value.trim() || undefined,
    })
    message.success(t('pool.createSuccess'))
    showCreate.value = false
    createTitle.value = ''
    createDescription.value = ''
    await router.push(`/pool/${pool.id}`)
    return false
  } catch (error: unknown) {
    handleApiError(error, t('pool.createFailed'))
    return false
  } finally {
    creating.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await poolsApi.delete(id)
    message.success(t('pool.deleteSuccess'))
    await fetchPools()
  } catch (error: unknown) {
    handleApiError(error, t('pool.deleteFailed'))
  }
}

onMounted(fetchPools)
</script>

<template>
  <div>
    <n-card :title="$t('pool.management')">
      <template #header-extra>
        <n-button type="primary" @click="showCreate = true">
          {{ $t('pool.createNew') }}
        </n-button>
      </template>

      <p class="pool-intro">{{ $t('pool.intro') }}</p>

      <n-data-table
        :columns="columns"
        :data="pools"
        :loading="loading"
        :row-key="(row: ExperiencePool) => row.id"
      />
    </n-card>

    <n-modal
      v-model:show="showCreate"
      preset="dialog"
      :title="$t('pool.createNew')"
      :positive-text="$t('common.confirm')"
      :negative-text="$t('common.cancel')"
      :positive-button-props="{ loading: creating }"
      @positive-click="handleCreate"
      style="width: 520px"
    >
      <n-form label-placement="top">
        <n-form-item :label="$t('pool.title')">
          <n-input v-model:value="createTitle" :placeholder="$t('pool.titlePlaceholder')" />
        </n-form-item>
        <n-form-item :label="$t('pool.description')">
          <n-input
            v-model:value="createDescription"
            type="textarea"
            :rows="3"
            :placeholder="$t('pool.descriptionPlaceholder')"
          />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<style scoped>
.pool-intro {
  margin: 0 0 16px;
  color: var(--muted-foreground);
  font-size: 14px;
  line-height: 1.5;
}
</style>
