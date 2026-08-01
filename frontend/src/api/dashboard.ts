import { profilesApi } from './profiles'
import { professorsApi } from './professors'
import { matchApi } from './match'
import { lettersApi } from './letters'
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

export const dashboardApi = {
  async getData(): Promise<DashboardData> {
    // Every call asks for counts plus the five newest rows; the active profile
    // is the only record fetched in full, since its card renders detail fields.
    const [profilesRes, activeProfile, professorsRes, topMatchesRes, recentLettersRes] =
      await Promise.all([
        profilesApi.listSummary({ page: 1, page_size: 5 }),
        profilesApi.getActive(),
        professorsApi.list({ page: 1, page_size: 5 }),
        matchApi.getResults({ page: 1, page_size: 5 }),
        lettersApi.list({ page: 1, page_size: 5 }),
      ])

    return {
      stats: {
        profileCount: profilesRes.total,
        professorCount: professorsRes.total,
        matchCount: topMatchesRes.total,
        letterCount: recentLettersRes.total,
      },
      activeProfile,
      recentProfiles: profilesRes.items,
      recentProfessors: professorsRes.items,
      topMatches: topMatchesRes.items,
      recentLetters: recentLettersRes.items,
    }
  },
}
