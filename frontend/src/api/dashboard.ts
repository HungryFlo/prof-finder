import { profilesApi } from './profiles'
import { professorsApi } from './professors'
import { matchApi } from './match'
import { lettersApi } from './letters'
import type { Profile, ProfessorListItem, MatchResult, Letter } from '@/types'
import { parseApiDateTime } from '@/utils/datetime'

export interface DashboardStats {
  profileCount: number
  professorCount: number
  matchCount: number
  letterCount: number
}

export interface DashboardData {
  stats: DashboardStats
  activeProfile: Profile | null
  recentProfiles: Profile[]
  recentProfessors: ProfessorListItem[]
  topMatches: MatchResult[]
  recentLetters: Letter[]
}

export const dashboardApi = {
  async getData(): Promise<DashboardData> {
    const [profiles, professorsRes, topMatchesRes, recentLettersRes] =
      await Promise.all([
        profilesApi.list(),
        professorsApi.list({ page: 1, page_size: 5 }),
        matchApi.getResults({ page: 1, page_size: 5 }),
        lettersApi.list({ page: 1, page_size: 5 }),
      ])

    const recentProfiles = [...profiles]
      .sort(
        (a, b) =>
          parseApiDateTime(b.updated_at).getTime() -
          parseApiDateTime(a.updated_at).getTime()
      )
      .slice(0, 5)

    const activeProfile = profiles.find((p) => p.is_active) ?? null

    return {
      stats: {
        profileCount: profiles.length,
        professorCount: professorsRes.total,
        matchCount: topMatchesRes.total,
        letterCount: recentLettersRes.total,
      },
      activeProfile,
      recentProfiles,
      recentProfessors: professorsRes.items,
      topMatches: topMatchesRes.items,
      recentLetters: recentLettersRes.items,
    }
  },
}
