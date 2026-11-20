import type {
  AdminDetail,
  AdminSummary,
  ApplicationCreated,
  ApplicationView,
  Fund,
  SubmitResponse,
} from './types'

const BASE = '/api/v1'

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
  ) {
    super(typeof detail === 'string' ? detail : `Request failed (${status})`)
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { headers?: Record<string, string> } = {},
): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })
  const body = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(response.status, (body as { detail?: unknown })?.detail ?? null)
  }
  return body as T
}

const resumeHeaders = (token: string) => ({ 'X-Resume-Token': token })
const adminHeaders = (token: string) => ({ 'X-Admin-Token': token })

export const api = {
  getFunds: () => request<Fund[]>('/funds'),

  createApplication: () => request<ApplicationCreated>('/applications', { method: 'POST' }),

  getApplication: (id: string, token: string) =>
    request<ApplicationView>(`/applications/${id}`, { headers: resumeHeaders(token) }),

  updateDraft: (id: string, token: string, sections: Record<string, unknown>) =>
    request<ApplicationView>(`/applications/${id}`, {
      method: 'PUT',
      headers: resumeHeaders(token),
      body: JSON.stringify(sections),
    }),

  submit: (id: string, token: string) =>
    request<SubmitResponse>(`/applications/${id}/submit`, {
      method: 'POST',
      headers: resumeHeaders(token),
    }),

  admin: {
    list: (token: string, status?: string) =>
      request<AdminSummary[]>(
        `/admin/applications${status ? `?status=${encodeURIComponent(status)}` : ''}`,
        { headers: adminHeaders(token) },
      ),
    detail: (token: string, id: string) =>
      request<AdminDetail>(`/admin/applications/${id}`, { headers: adminHeaders(token) }),
    decide: (token: string, id: string, decision: 'approve' | 'decline', note?: string) =>
      request<AdminDetail>(`/admin/applications/${id}/decision`, {
        method: 'POST',
        headers: adminHeaders(token),
        body: JSON.stringify({ decision, note: note || null }),
      }),
  },
}
