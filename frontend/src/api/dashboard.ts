import client from './client'
import type { Profile, ProfileSummary, ProfessorListItem, MatchResult, Letter } from '@/types'

export interface DashboardStats {
  profileCount: number
  professorCount: number
  matchCount: number
  letterCount: number
}

export interface DashboardData {
  stats: DashboardStats
  activeProfile: Profile | null
  recentProfiles: ProfileSummary[]
  recentProfessors: ProfessorListItem[]
  topMatches: MatchResult[]
  recentLetters: Letter[]
}

interface DashboardApiResponse {
  stats: {
    profile_count: number
    professor_count: number
    match_count: number
    letter_count: number
  }
  active_profile: Profile | null
  recent_profiles: ProfileSummary[]
  recent_professors: ProfessorListItem[]
  top_matches: MatchResult[]
  recent_letters: Letter[]
}

export const dashboardApi = {
  async getData(): Promise<DashboardData> {
    const response = await client.get<DashboardApiResponse>('/dashboard')
    const body = response.data
    return {
      stats: {
        profileCount: body.stats.profile_count,
        professorCount: body.stats.professor_count,
        matchCount: body.stats.match_count,
        letterCount: body.stats.letter_count,
      },
      activeProfile: body.active_profile,
      recentProfiles: body.recent_profiles,
      recentProfessors: body.recent_professors,
      topMatches: body.top_matches,
      recentLetters: body.recent_letters,
    }
  },
}
