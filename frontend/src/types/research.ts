export interface Competitor {
  name: string
  website: string
  reason: string
}

export interface ResearchSource {
  title: string
  url: string
  snippet: string
}

export interface CompanyResearchResult {
  company_name: string
  summary: string
  website: string
  phone: string
  address: string
  revenue: string
  products: string[]
  pain_points: string[]
  industry: string
  country: string
  competitors: Competitor[]
  sources?: ResearchSource[]
  generated_at: string
  pdf_base64: string
  report_filename: string
}

export interface DiscordSettings {
  bot_token: string
  channel_id: string
  applicant_name: string
  applicant_email: string
}

export interface ResearchRequest {
  query: string
  input_type: 'company_name' | 'website_url'
  groq_api_key: string
  serper_api_key: string
  model: string
  discord?: DiscordSettings
}

export interface ModelInfo {
  id: string
  object?: string
  owned_by?: string
  label: string
}

export interface ProgressEvent {
  stage: string
  message: string
  progress: number
  done?: boolean
  result?: CompanyResearchResult | null
  error?: string
}

export interface StoredConfig {
  groq_api_key: string
  serper_api_key: string
  model: string
  discord: DiscordSettings
}
