<script setup lang="ts">
import { computed, provide, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NBreadcrumb, NBreadcrumbItem } from 'naive-ui'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const dynamicTitle = ref<string | null>(null)

provide('setBreadcrumbTitle', (title: string) => {
  dynamicTitle.value = title
})

// Reset dynamic title on route change
const routePath = computed(() => route.path)

interface BreadcrumbItem {
  label: string
  path: string
  isCurrent: boolean
  clickable: boolean
}

const breadcrumbItems = computed<BreadcrumbItem[]>(() => {
  // Reset dynamic title reference when path changes (actual reset happens in detail pages)
  void routePath.value

  const items: BreadcrumbItem[] = []

  // Always add Home as first item (unless we're on the root/dashboard)
  const matched = route.matched
  const hasBreadcrumb = matched.some((r) => r.meta?.breadcrumb)

  if (!hasBreadcrumb) {
    return items
  }

  items.push({
    label: t('breadcrumb.home'),
    path: '/',
    isCurrent: false,
    clickable: true,
  })

  // Build items from matched routes that have breadcrumb meta
  for (let i = 0; i < matched.length; i++) {
    const record = matched[i]
    const bc = record.meta?.breadcrumb as { labelKey?: string; dynamic?: boolean } | undefined
    if (!bc?.labelKey) continue

    const isLast = i === matched.length - 1
    const isDynamic = bc.dynamic === true

    let label = t(bc.labelKey)
    if (isDynamic && dynamicTitle.value) {
      label = dynamicTitle.value
    }

    // Build the path for this matched route
    // For child routes, we need to construct the full path
    let itemPath = record.path
    // If the record path is relative (doesn't start with /), prepend parent path
    if (!itemPath.startsWith('/')) {
      const parentPath = matched[i - 1]?.path || ''
      itemPath = parentPath === '/' ? `/${itemPath}` : `${parentPath}/${itemPath}`
    }

    items.push({
      label,
      path: itemPath,
      isCurrent: isLast,
      clickable: !isLast,
    })
  }

  return items
})

const show = computed(() => breadcrumbItems.value.length > 0)

function handleClick(path: string) {
  router.push(path)
}
</script>

<template>
  <n-breadcrumb v-if="show" class="breadcrumb-nav">
    <n-breadcrumb-item
      v-for="(item, index) in breadcrumbItems"
      :key="index"
      :clickable="item.clickable"
      @click="item.clickable ? handleClick(item.path) : undefined"
    >
      {{ item.label }}
    </n-breadcrumb-item>
  </n-breadcrumb>
</template>

<style scoped>
.breadcrumb-nav {
  margin-bottom: 16px;
}
</style>
