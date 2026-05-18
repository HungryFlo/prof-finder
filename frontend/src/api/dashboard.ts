import { profilesApi } from './profiles'
import { professorsApi } from './professors'
import { matchApi } from './match'
import { lettersApi } from './letters'
import type { Profile, ProfessorListItem } from '@/types'

export interface DashboardStats {
  profileCount: number
  professorCount: number
  matchCount: number
  letterCount: number
}

export interface DashboardData {
  stats: DashboardStats
  recentProfiles: Profile[]
  recentProfessors: ProfessorListItem[]
}

export const dashboardApi = {
  async getData(): Promise<DashboardData> {
    const [profiles, professorsRes, matchesRes, lettersRes] = await Promise.all([
      profilesApi.list(),
      professorsApi.list({ page: 1, page_size: 5 }),
      matchApi.getResults({ page: 1, page_size: 1 }),
      lettersApi.list({ page: 1, page_size: 1 }),
    ])

    // Sort profiles by updated_at descending and take the 5 most recent
    const recentProfiles = [...profiles]
      .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
      .slice(0, 5)

    return {
      stats: {
        profileCount: profiles.length,
        professorCount: professorsRes.total,
        matchCount: matchesRes.total,
        letterCount: lettersRes.total,
      },
      recentProfiles,
      recentProfessors: professorsRes.items,
    }
  },
}
