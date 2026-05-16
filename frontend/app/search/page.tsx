'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { searchJobs, type SearchResult, type Job, type FilteredJob } from '@/lib/api'
import { getToken, getDatabaseId } from '@/lib/token'

const COUNTRIES = [
  { value: 'canada', label: 'Canada' },
  { value: 'usa', label: 'United States' },
  { value: 'uk', label: 'United Kingdom' },
  { value: 'australia', label: 'Australia' },
]

const REASON_LABELS: Record<string, string> = {
  RECRUITER_SPAM: 'Recruiter / staffing agency',
  SENIORITY_MISMATCH: 'Seniority mismatch',
  DUPLICATE: 'Duplicate listing',
}

function JobCard({ job }: { job: Job }) {
  return (
    <a
      href={job.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-start justify-between gap-3 rounded-xl bg-emerald-900/30 border border-emerald-800 px-4 py-3 hover:bg-emerald-900/50 transition-colors"
    >
      <div className="min-w-0">
        <p className="font-medium truncate">{job.title}</p>
        <p className="text-sm text-slate-400 truncate">{job.company}</p>
      </div>
      <span className="flex-shrink-0 text-xs bg-emerald-700 text-emerald-100 px-2 py-0.5 rounded-full">
        Saved
      </span>
    </a>
  )
}

function FilteredCard({ item }: { item: FilteredJob }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl bg-slate-800/40 border border-slate-700 px-4 py-3 opacity-60">
      <div className="min-w-0">
        <p className="font-medium truncate">{item.job.title}</p>
        <p className="text-sm text-slate-400 truncate">{item.job.company}</p>
      </div>
      <span className="flex-shrink-0 text-xs bg-amber-900 text-amber-300 px-2 py-0.5 rounded-full whitespace-nowrap">
        {item.reason ? REASON_LABELS[item.reason] ?? item.reason : 'Filtered'}
      </span>
    </div>
  )
}

function ErrorCard({ item }: { item: { job: Job; error: string } }) {
  return (
    <div className="rounded-xl bg-red-900/20 border border-red-800 px-4 py-3 space-y-1">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-medium truncate">{item.job.title}</p>
          <p className="text-sm text-slate-400 truncate">{item.job.company}</p>
        </div>
        <span className="flex-shrink-0 text-xs bg-red-900 text-red-300 px-2 py-0.5 rounded-full">
          Error
        </span>
      </div>
      <p className="text-xs text-red-400 font-mono break-all">{item.error}</p>
    </div>
  )
}

export default function SearchPage() {
  const router = useRouter()
  const [ready, setReady] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [location, setLocation] = useState('')
  const [country, setCountry] = useState('canada')
  const [count, setCount] = useState('10')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<SearchResult | null>(null)

  useEffect(() => {
    if (!getToken() || !getDatabaseId()) {
      router.push('/setup')
    } else {
      setReady(true)
    }
  }, [router])

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    const token = getToken()
    const dbId = getDatabaseId()
    if (!token || !dbId) return

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const data = await searchJobs({
        keyword,
        location,
        country,
        results_wanted: parseInt(count),
        notion_token: token,
        database_id: dbId,
      })
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  if (!ready) return null

  return (
    <main className="flex min-h-screen flex-col items-center px-4 py-12">
      <div className="w-full max-w-lg space-y-8">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-slate-400 hover:text-slate-200 transition-colors text-sm">
            ← Home
          </Link>
          <h1 className="text-2xl font-bold">Search Jobs</h1>
        </div>

        <form onSubmit={handleSearch} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-300">Job title / keyword</label>
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="e.g. Software Engineer Intern"
              required
              className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-300">Location</label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Toronto"
                required
                className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-300">Country</label>
              <select
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
              >
                {COUNTRIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-300">Max results</label>
            <select
              value={count}
              onChange={(e) => setCount(e.target.value)}
              className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            >
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="20">20</option>
            </select>
          </div>

          {error && (
            <div className="rounded-xl bg-red-900/40 border border-red-700 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:text-slate-500 transition-colors py-3 font-semibold"
          >
            {loading ? 'Searching & filtering…' : 'Search'}
          </button>
        </form>

        {loading && (
          <div className="text-center text-slate-400 text-sm space-y-1">
            <p>Searching LinkedIn &amp; Indeed…</p>
            <p>Running filter…</p>
            <p>Saving to Notion…</p>
          </div>
        )}

        {results && (
          <div className="space-y-6">
            <div className="flex gap-4 text-sm flex-wrap">
              <span className="text-emerald-400 font-medium">{results.saved.length} saved</span>
              <span className="text-slate-500">·</span>
              <span className="text-amber-400 font-medium">{results.filtered.length} filtered out</span>
              {results.errors.length > 0 && (
                <>
                  <span className="text-slate-500">·</span>
                  <span className="text-red-400 font-medium">{results.errors.length} failed to save</span>
                </>
              )}
            </div>

            {results.errors.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-widest text-red-500 font-medium">
                  Failed to save — check your Notion token or database
                </p>
                {results.errors.map((item, i) => (
                  <ErrorCard key={i} item={item} />
                ))}
              </div>
            )}

            {results.saved.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-widest text-slate-500 font-medium">
                  Saved to Notion
                </p>
                {results.saved.map((job, i) => (
                  <JobCard key={i} job={job} />
                ))}
              </div>
            )}

            {results.filtered.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-widest text-slate-500 font-medium">
                  Filtered out
                </p>
                {results.filtered.map((item, i) => (
                  <FilteredCard key={i} item={item} />
                ))}
              </div>
            )}

            {results.saved.length === 0 && results.filtered.length === 0 && results.errors.length === 0 && (
              <div className="rounded-xl bg-slate-800/40 border border-slate-700 px-4 py-6 text-center text-slate-400 text-sm">
                No jobs found. Try a different keyword or location.
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  )
}
