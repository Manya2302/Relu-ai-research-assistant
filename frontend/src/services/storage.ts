import type { StoredConfig } from '@/types/research'

const STORAGE_KEY = 'relu_company_research_config'

export const defaultStoredConfig = (): StoredConfig => ({
  groq_api_key: '',
  serper_api_key: '',
  model: 'llama-3.1-70b-versatile',
  discord: {
    bot_token: '',
    channel_id: '',
    applicant_name: '',
    applicant_email: '',
  },
})

export function loadStoredConfig(): StoredConfig {
  if (typeof window === 'undefined') {
    return defaultStoredConfig()
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return defaultStoredConfig()
    }
    const parsed = JSON.parse(raw) as Partial<StoredConfig>
    return {
      ...defaultStoredConfig(),
      ...parsed,
      discord: {
        ...defaultStoredConfig().discord,
        ...(parsed.discord ?? {}),
      },
    }
  } catch {
    return defaultStoredConfig()
  }
}

export function saveStoredConfig(config: StoredConfig) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
}

export function clearStoredConfig() {
  window.localStorage.removeItem(STORAGE_KEY)
}
