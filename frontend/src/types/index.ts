// User types
export interface User {
  id: number
  username: string
  is_admin: boolean
  must_change_password: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  must_change_password: boolean
}

// Profile types
export interface EducationItem {
  degree?: string
  school?: string
  major?: string
  period?: string
}

export interface ResearchItem {
  title?: string
  organization?: string
  description?: string
  period?: string
}

export interface ProjectItem {
  name?: string
  description?: string
}

export interface Profile {
  id: number
  title: string
  name?: string
  name_locales?: Record<string, string>
  is_active: boolean
  education: EducationItem[]
  research_experience: ResearchItem[]
  projects: ProjectItem[]
  skills: string[]
  source_format?: string
  profile_materials?: Array<Record<string, unknown>>
  manual_inputs?: Record<string, string>
  academic_profile?: string
  profile_analysis?: Record<string, unknown>
  evidence_notes?: unknown[]
  conflict_notes?: unknown[]
  profile_generated_at?: string
  created_at: string
  updated_at: string
}

export interface ProfileCreate {
  title: string
  name?: string
  name_locales?: Record<string, string>
  education: EducationItem[]
  research_experience: ResearchItem[]
  projects: ProjectItem[]
  skills: string[]
  raw_content?: string
  source_format: string
}

// Professor types
export interface Publication {
  title: string
  year?: number | string
  citations?: number
  authors?: string
  source?: 'scholar' | 'dblp' | string
  author_pub_id?: string
  gscholar_url?: string
  dblp_url?: string
  venue?: string
  abstract?: string
  pub_url?: string
  eprint_url?: string
  journal?: string
  conference?: string
  volume?: string
  number?: string
  pages?: string
  publisher?: string
}

export interface PaperSummary {
  source_input_id?: number
  source_type?: string
  title: string
  summary: string
  keywords?: string[]
}

export interface ScholarCandidate {
  scholar_id: string
  name: string
  affiliation?: string
  score: number
  email_domain_match: boolean
  citedby?: number
}

export interface DblpCandidate {
  pid: string
  name: string
  affiliation?: string
  url?: string
  score: number
  email_domain_match?: boolean
}

export interface DblpSearchResult {
  name: string
  pid: string
  url: string
  affiliations: string[]
}

export interface Professor {
  id: number
  name: string
  name_locales?: Record<string, string>
  affiliation?: string
  email?: string
  homepage?: string
  google_scholar_id?: string
  google_scholar_url?: string
  dblp_pid?: string
  dblp_url?: string
  dblp_enrichment_status?: string
  dblp_candidates?: DblpCandidate[]
  research_interests: string[]
  publications: Publication[]
  paper_summaries?: PaperSummary[]
  h_index?: number
  total_citations?: number
  manual_notes?: string
  research_profile?: string
  research_profile_analysis?: Record<string, unknown>
  research_profile_sources?: Array<Record<string, unknown>>
  research_profile_evidence?: unknown[]
  research_profile_conflicts?: unknown[]
  research_profile_generated_at?: string
  source?: string
  enrichment_status?: string
  scholar_candidates?: ScholarCandidate[]
  created_at: string
  updated_at: string
  enrichment_task_id?: string
  enrichment_task_total?: number
}

export interface ProfessorListItem {
  id: number
  name: string
  affiliation?: string
  research_interests: string[]
  h_index?: number
  publication_count: number
  source?: string
  enrichment_status?: string
  google_scholar_id?: string
  dblp_pid?: string
  dblp_enrichment_status?: string
  created_at: string
}

export interface ScholarSearchResult {
  name: string
  affiliation?: string
  scholar_id: string
  scholar_url: string
  interests: string[]
  citations?: number
}

export interface SourceInput {
  id: number
  source_type: 'pdf' | 'arxiv' | string
  original_name?: string
  source_url?: string
  canonical_id?: string
  title?: string
  abstract?: string
  extracted_markdown?: string
  status: 'pending' | 'succeeded' | 'failed' | string
  error_message?: string
  metadata_only: boolean
  created_at: string
  updated_at: string
}

export interface ProfessorEditPreviewResponse {
  manual_patch_applied: Record<string, unknown>
  source_suggestions: {
    publications?: Publication[]
    paper_summaries?: PaperSummary[]
    manual_notes_append?: string | null
  }
}

// Match types
export interface MatchResult {
  professor_id: number
  professor_name: string
  professor_affiliation?: string
  score: number
  match_reasons: string[]
  letter_generated: boolean
}

export interface MatchDetail {
  professor_id: number
  professor_name: string
  professor_affiliation?: string
  professor_interests: string[]
  score: number
  match_reasons: string[]
  letter_content?: string
  letter_generated_at?: string
}

// Letter types
export interface Letter {
  professor_id: number
  professor_name: string
  content?: string
  generated_at?: string
  is_generated: boolean
}

// Chat types
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ProfileChatResponse {
  reply: string
}

// Settings types
export interface UserSettings {
  llm_provider: 'openai' | 'anthropic'
  llm_api_key_masked?: string | null
  llm_base_url: string
  llm_model: string
  request_delay: number
  auto_enrich_on_save_fetch_publication_details?: boolean
  auto_enrich_on_save_paper_summaries?: boolean
  auto_enrich_on_save_research_profile?: boolean
}

// Task panel types
export type TaskType =
  | 'batch-crawl'
  | 'batch-dblp-crawl'
  | 'batch-letters'
  | 'single-crawl'
  | 'single-dblp-crawl'
  | 'university-crawl'
  | 'generic-university-crawl'
  | 'batch-dblp-match'
  | 'batch-refresh-dblp'
  | 'batch-refresh-external'
  | 'paper-summary'
  | 'profile-parse'
  | 'profile-generate'
  | 'professor-profile'
  | 'professor-enrichment'
  | 'batch-professor-enrichment'
  | 'batch-professor-profiles'
  | 'fill-publications'
  | 'professor-homepage-crawl'
  | 'batch-refresh'
  | 'profile-refine'
  | 'match'
  | 'single-letter'
  | 'download-model'
export type TaskStatus =
  | 'pending'
  | 'running'
  | 'cancelling'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'interrupted'

export interface TaskListItem {
  task_id: string
  task_type: TaskType
  task_name: string
  status: TaskStatus
  current: number
  total: number
  message: string
  error_message: string
  cancel_requested?: boolean
}

// Task types
export interface TaskProgress {
  current: number
  total: number
  status: TaskStatus
  message: string
  cancel_requested?: boolean
  item?: {
    success: boolean
    name?: string
    error?: string
    [key: string]: unknown
  }
}

export interface TaskResult {
  status: string
  current?: number
  total?: number
  message?: string
  success_count: number
  failed_count: number
  results: Array<{
    success: boolean
    name?: string
    error?: string
    [key: string]: unknown
  }>
}

// Pagination types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// API response types
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  error: string
  detail: string
}
