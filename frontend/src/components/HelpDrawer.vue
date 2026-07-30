<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NDrawer, NDrawerContent, NCollapse, NCollapseItem, NButton, NSpace, NText } from 'naive-ui'
import { useHelpDrawer } from '@/composables/useHelpDrawer'

const { t } = useI18n()
const { showHelp } = useHelpDrawer()

const quickStartSteps = computed(() => [
  { title: t('help.step0Title'), desc: t('help.step0Desc') },
  { title: t('help.step1Title'), desc: t('help.step1Desc') },
  { title: t('help.step2Title'), desc: t('help.step2Desc') },
  { title: t('help.step3Title'), desc: t('help.step3Desc') },
  { title: t('help.step4Title'), desc: t('help.step4Desc') },
])

const apiKeySteps = computed(() => [
  t('help.apiKeyStep1'),
  t('help.apiKeyStep2'),
  t('help.apiKeyStep3'),
  t('help.apiKeyStep4'),
  t('help.apiKeyStep5'),
])

const bestPractices = computed(() => [
  t('help.bpExperiencePool'),
  t('help.bpCompleteProfile'),
  t('help.bpScholarUrl'),
  t('help.bpActiveProfile'),
  t('help.bpReviewLetter'),
  t('help.bpRequestDelay'),
  t('help.bpAutoEnrich'),
])

const faqItems = computed(() => [
  { q: t('help.faqDataLocationQ'), a: t('help.faqDataLocationA') },
  { q: t('help.faqPortQ'), a: t('help.faqPortA') },
  { q: t('help.faqMatchDisabledQ'), a: t('help.faqMatchDisabledA') },
  { q: t('help.faqScholarFailQ'), a: t('help.faqScholarFailA') },
  { q: t('help.faqLlmFailQ'), a: t('help.faqLlmFailA') },
])
</script>

<template>
  <n-drawer v-model:show="showHelp" :width="480" placement="right">
    <n-drawer-content :title="t('help.title')" closable>
      <n-collapse default-expanded-names="['quickStart', 'apiKey']">
        <n-collapse-item :title="t('help.quickStart')" name="quickStart">
          <n-text depth="3">{{ t('help.quickStartIntro') }}</n-text>
          <ol class="help-list">
            <li v-for="(step, i) in quickStartSteps" :key="i">
              <strong>{{ step.title }}</strong>
              <p>{{ step.desc }}</p>
            </li>
          </ol>
        </n-collapse-item>

        <n-collapse-item :title="t('help.apiKeyGuide')" name="apiKey">
          <n-text depth="3">{{ t('help.apiKeyIntro') }}</n-text>
          <ol class="help-list">
            <li v-for="(step, i) in apiKeySteps" :key="i">{{ step }}</li>
          </ol>
          <n-space style="margin-top: 12px">
            <n-button
              tag="a"
              href="https://platform.deepseek.com"
              target="_blank"
              rel="noopener noreferrer"
              type="primary"
              size="small"
            >
              {{ t('help.openDeepSeekPlatform') }}
            </n-button>
          </n-space>
        </n-collapse-item>

        <n-collapse-item :title="t('help.bestPractice')" name="bestPractice">
          <ul class="help-list help-list--bullet">
            <li v-for="(item, i) in bestPractices" :key="i">{{ item }}</li>
          </ul>
        </n-collapse-item>

        <n-collapse-item :title="t('help.faq')" name="faq">
          <dl class="help-faq">
            <template v-for="(item, i) in faqItems" :key="i">
              <dt>{{ item.q }}</dt>
              <dd>{{ item.a }}</dd>
            </template>
          </dl>
        </n-collapse-item>
      </n-collapse>
    </n-drawer-content>
  </n-drawer>
</template>

<style scoped>
.help-list {
  margin: 12px 0 0;
  padding-left: 20px;
}

.help-list li {
  margin-bottom: 10px;
  line-height: 1.5;
}

.help-list li p {
  margin: 4px 0 0;
  color: var(--muted-foreground);
}

.help-list--bullet {
  list-style-type: disc;
}

.help-faq {
  margin: 12px 0 0;
}

.help-faq dt {
  font-weight: 600;
  margin-top: 12px;
}

.help-faq dt:first-child {
  margin-top: 0;
}

.help-faq dd {
  margin: 4px 0 0;
  color: var(--muted-foreground);
  line-height: 1.5;
}
</style>
