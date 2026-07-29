import { h } from 'vue'
import { NButton, useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useErrorDetailStore } from '@/stores/errorDetail'
import {
  parseApiError,
  resolveFriendlyMessage,
  type ParsedApiError,
} from '@/utils/apiError'

export function useApiError() {
  const message = useMessage()
  const { t, te } = useI18n()
  const errorDetail = useErrorDetailStore()

  function openDetails(parsed: ParsedApiError, friendlyMessage: string) {
    errorDetail.open({
      ...parsed,
      friendlyMessage,
    })
  }

  function renderErrorContent(friendlyMessage: string, onDetails: () => void) {
    return h(
      'div',
      {
        style: {
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          flexWrap: 'wrap',
        },
      },
      [
        h('span', { style: { flex: '1 1 auto' } }, friendlyMessage),
        h(
          NButton,
          {
            text: true,
            type: 'primary',
            size: 'tiny',
            onClick: (e: MouseEvent) => {
              e.stopPropagation()
              onDetails()
            },
          },
          { default: () => t('common.errorDetails') },
        ),
      ],
    )
  }

  function handleApiError(error: unknown, fallback: string) {
    const parsed = parseApiError(error)
    const friendly = resolveFriendlyMessage(parsed, t, te, fallback)
    const showDetails = parsed.hasRawDetail

    if (showDetails) {
      message.error(
        () =>
          renderErrorContent(friendly, () => openDetails(parsed, friendly)),
        { duration: 8000, closable: true },
      )
    } else {
      message.error(friendly)
    }
  }

  /** Present a non-Axios error (e.g. task SSE) with the same UX. */
  function presentRawError(options: {
    friendlyMessage: string
    detail: string
    code?: string | null
    status?: number | null
    via?: 'message' | 'none'
  }) {
    const parsed: ParsedApiError = {
      code: options.code ?? null,
      detail: options.detail,
      status: options.status ?? null,
      hasRawDetail: Boolean(options.detail || options.code || options.status),
    }
    if (options.via !== 'none') {
      if (parsed.hasRawDetail) {
        message.error(
          () =>
            renderErrorContent(options.friendlyMessage, () =>
              openDetails(parsed, options.friendlyMessage),
            ),
          { duration: 8000, closable: true },
        )
      } else {
        message.error(options.friendlyMessage)
      }
    }
    return { parsed, openDetails: () => openDetails(parsed, options.friendlyMessage) }
  }

  return { handleApiError, presentRawError, parseApiError, openDetails }
}
