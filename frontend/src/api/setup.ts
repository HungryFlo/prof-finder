import client from './client'

export interface SetupStatus {
  packaged: boolean
  configured: boolean
  suggested_data_dir: string | null
}

export interface PickDirectoryResponse {
  path: string
}

export interface SetupCompleteResponse {
  restart_required: boolean
  data_dir: string
  model_dir: string
}

export const setupApi = {
  async getStatus(): Promise<SetupStatus> {
    const { data } = await client.get<SetupStatus>('/setup/status')
    return data
  },

  async pickDirectory(): Promise<string> {
    const { data } = await client.post<PickDirectoryResponse>('/setup/pick-directory')
    return data.path
  },

  async complete(dataDir: string): Promise<SetupCompleteResponse> {
    const { data } = await client.post<SetupCompleteResponse>('/setup/complete', {
      data_dir: dataDir,
    })
    return data
  },
}
