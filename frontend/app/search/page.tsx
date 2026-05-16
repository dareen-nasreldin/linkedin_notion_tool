'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { searchJobs, type SearchResult, type Job, type FilteredJob } from '@/lib/api'
import { getToken, getDatabaseId } from '@/lib/token'

const COUNTRIES = [
  { value: 'canada', label: 'Canada' },
  { value: 'usa', label: 'United States' },
  { value: 'uk', label: 'United Kingdom' },
  { value: 'australia', label: 'Australia' },
]

const REASON_LABELS: Record<string, string> = {
  RECRUITER_SPAM: 'Recruiter spam',
  SENIORITY_MISMATCH: 'Seniority mismatch',
  DUPLICATE: 'Duplicate',
}

function Tag({ label, color }: { label: string; color: 'green' | 'amber' | 'red' }) {
  const styles = {
    green: { background: 'var(--success-bg)', color: 'var(--success)' },
    amber: { background: 'var(--warning-bg)', color: 'var(--warning)' },
    red: { background: 'var(--danger-bg)', color: 'var(--danger)' },
  }
  return (
    <span
      style={{ ...styles[color], borderRadius: 4, fontSize: 11, fontWeight: 500 }}
      className="px-2 py-0.5 whitespace-nowrap"
    >
      {label}
    </span>
  )
}

function SavedRow({ job }: { job: Job }) {
  return (
    <a
      href={job.url}
      target="_blank"
      rel="noopener noreferrer"
      style={{ borderBottom: '1px solid var(--border)' }}
      className="flex items-center gap-3 px-4 py-3 hover:bg-[var(--sidebar)] transition-colors group"
    >
      <span className="text-sm leading-none">📄</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>{job.title}</p>
        <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--text-muted)' }}>{job.company}</p>
      </div>
      <Tag label="Saved" color="green" />
      <span className="text-xs opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: 'var(--text-muted)' }}>↗</span>
    </a>
  )
}

function FilteredRow({ item }: { item: FilteredJob }) {
  return (
    <div
      style={{ borderBottom: '1px solid var(--border)' }}
      className="flex items-center gap-3 px-4 py-3 opacity-50"
    >
      <span className="text-sm leading-none">📄</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>{item.job.title}</p>
        <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--text-muted)' }}>{item.job.company}</p>
      </div>
      <Tag label={item.reason ? REASON_LABELS[item.reason] ?? item.reason : 'Filtered'} color="amber" />
    </div>
  )
}

function ErrorRow({ item }: { item: { job: Job; error: string } }) {
  return (
    <div style={{ borderBottom: '1px solid var(--border)' }} className="px-4 py-3">
      <div className="flex items-center gap-3">
        <span className="text-sm leading-none">📄</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>{item.job.title}</p>
          <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--text-muted)' }}>{item.job.company}</p>
        </div>
        <Tag label="Error" color="red" />
      </div>
      <p className="text-xs mt-2 ml-7 font-mono break-all" style={{ color: 'var(--danger)' }}>{item.error}</p>
    </div>
  )
}

const inputClass = "w-full px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)]"
const inputStyle = {
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  background: 'var(--input-bg)',
  color: 'var(--text)',
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
        keyword, location, country,
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
    <div className="max-w-2xl mx-auto px-8 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold mb-1" style={{ color: 'var(--text)' }}>Search Jobs</h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Search LinkedIn &amp; Indeed. Recruiter spam and mismatched roles are filtered automatically.
        </p>
      </div>

      {/* Form */}
      <form
        onSubmit={handleSearch}
        style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}
        className="p-5 space-y-4 mb-8"
      >
        <div className="space-y-1.5">
          <label className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            Keyword
          </label>
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="e.g. Software Engineer Intern"
            required
            style={inputStyle}
            className={inputClass + " placeholder:text-[var(--text-placeholder)]"}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              Location
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Toronto"
              required
              style={inputStyle}
              className={inputClass + " placeholder:text-[var(--text-placeholder)]"}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              Country
            </label>
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              style={inputStyle}
              className={inputClass}
            >
              {COUNTRIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            Max results
          </label>
          <select value={count} onChange={(e) => setCount(e.target.value)} style={inputStyle} className={inputClass}>
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="20">20</option>
          </select>
        </div>

        {error && (
          <div
            style={{ background: 'var(--danger-bg)', border: '1px solid #ffc9c9', borderRadius: 'var(--radius)', color: 'var(--danger)' }}
            className="px-4 py-3 text-sm"
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            background: loading ? 'var(--border)' : 'var(--accent)',
            color: loading ? 'var(--text-muted)' : '#fff',
            borderRadius: 'var(--radius)',
          }}
          className="w-full py-2.5 text-sm font-medium transition-colors hover:opacity-90 disabled:cursor-not-allowed"
        >
          {loading ? 'Searching…' : 'Search'}
        </button>

        {loading && (
          <p className="text-xs text-center" style={{ color: 'var(--text-muted)' }}>
            Searching LinkedIn &amp; Indeed, filtering results, saving to Notion…
          </p>
        )}
      </form>

      {/* Results */}
      {results && (
        <div>
          <div className="flex items-center gap-4 mb-4">
            <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>Results</p>
            <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--text-muted)' }}>
              <span style={{ color: 'var(--success)' }}>{results.saved.length} saved</span>
              <span>·</span>
              <span>{results.filtered.length} filtered</span>
              {results.errors.length > 0 && (
                <>
                  <span>·</span>
                  <span style={{ color: 'var(--danger)' }}>{results.errors.length} failed</span>
                </>
              )}
            </div>
          </div>

          {results.saved.length === 0 && results.filtered.length === 0 && results.errors.length === 0 ? (
            <div
              style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text-muted)' }}
              className="px-4 py-8 text-center text-sm"
            >
              No jobs found. Try a different keyword or location.
            </div>
          ) : (
            <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
              {results.errors.map((item, i) => <ErrorRow key={i} item={item} />)}
              {results.saved.map((job, i) => <SavedRow key={i} job={job} />)}
              {results.filtered.map((item, i) => <FilteredRow key={i} item={item} />)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
