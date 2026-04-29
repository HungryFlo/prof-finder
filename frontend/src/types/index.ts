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
  author_pub_id?: string
  gscholar_url?: string
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

export interface Professor {
  id: number
  name: string
  affiliation?: string
  email?: string
  homepage?: string
  google_scholar_id?: string
  google_scholar_url?: string
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
  created_at: string
  updated_at: string
}

export interface ProfessorListItem {
  id: number
  name: string
  affiliation?: string
  research_interests: string[]
  h_index?: number
  publication_count: number
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
  deepseek_api_key_masked?: string | null
  deepseek_base_url: string
  request_delay: number
}

// Task panel types
export type TaskType =
  | 'batch-crawl'
  | 'batch-letters'
  | 'single-crawl'
  | 'university-crawl'
  | 'paper-summary'
  | 'profile-parse'
  | 'profile-generate'
  | 'professor-profile'
  | 'batch-professor-profiles'
  | 'fill-publications'
  | 'batch-refresh'
  | 'profile-refine'
  | 'match'
  | 'single-letter'
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface TaskListItem {
  task_id: string
  task_type: TaskType
  task_name: string
  status: TaskStatus
  current: number
  total: number
  message: string
  error_message: string
}

// Task types
export interface TaskProgress {
  current: number
  total: number
  status: 'pending' | 'running' | 'completed' | 'cancelled' | 'failed'
  message: string
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
