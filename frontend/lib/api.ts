const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

async function post<T>(path: string, body: object): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Request failed')
  return data as T
}

export interface Job {
  title: string
  company: string
  url: string
  location?: string | null
  job_type?: string | null
  date_posted?: string | null
  is_remote?: boolean | null
  flagged_reason?: string
}

export interface FilteredJob {
  job: Job
  reason: string | null
}

export interface SearchResult {
  saved: Job[]
  filtered: FilteredJob[]
  skipped: Job[]
  errors: { job: Job; error: string }[]
}

export interface SetupResult {
  success: boolean
  database_id: string
  database_url: string
  parent_page: string
}

export interface ScrapeResult {
  scraped: boolean
  title?: string
  company?: string
  url?: string
  message?: string
}

export function setupNotion(token: string): Promise<SetupResult> {
  return post('/api/notion/setup', { notion_token: token })
}

export function searchJobs(params: {
  keyword: string
  location: string
  country: string
  results_wanted: number
  notion_token: string
  database_id: string
}): Promise<SearchResult> {
  return post('/api/search', params)
}

export function scrapeUrl(params: {
  url: string
  notion_token: string
  database_id: string
}): Promise<ScrapeResult> {
  return post('/api/add-url', params)
}

export function addManual(params: {
  title: string
  company: string
  url: string
  notion_token: string
  database_id: string
}): Promise<{ success: boolean; job: Job }> {
  return post('/api/add-manual', params)
}
