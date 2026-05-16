'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { scrapeUrl, addManual, type Job } from '@/lib/api'
import { getToken, getDatabaseId } from '@/lib/token'

type Stage = 'url-input' | 'manual-fallback' | 'saved'

const inputStyle = {
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  background: 'var(--input-bg)',
  color: 'var(--text)',
}
const inputClass = "w-full px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)] placeholder:text-[var(--text-placeholder)]"

export default function AddUrlPage() {
  const router = useRouter()
  const [ready, setReady] = useState(false)
  const [stage, setStage] = useState<Stage>('url-input')
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedJob, setSavedJob] = useState<Job | null>(null)
  const [manualTitle, setManualTitle] = useState('')
  const [manualCompany, setManualCompany] = useState('')
  const [manualUrl, setManualUrl] = useState('')

  useEffect(() => {
    if (!getToken() || !getDatabaseId()) {
      router.push('/setup')
    } else {
      setReady(true)
    }
  }, [router])

  async function handleScrape(e: React.FormEvent) {
    e.preventDefault()
    const token = getToken()
    const dbId = getDatabaseId()
    if (!token || !dbId) return
    setLoading(true)
    setError(null)
    try {
      const result = await scrapeUrl({ url: url.trim(), notion_token: token, database_id: dbId })
      if (result.scraped && result.title && result.company) {
        await addManual({
          title: result.title,
          company: result.company,
          url: result.url ?? url.trim(),
          notion_token: token,
          database_id: dbId,
        })
        setSavedJob({ title: result.title, company: result.company, url: result.url ?? url.trim() })
        setStage('saved')
      } else {
        setManualUrl(url.trim())
        setStage('manual-fallback')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  async function handleManualSave(e: React.FormEvent) {
    e.preventDefault()
    const token = getToken()
    const dbId = getDatabaseId()
    if (!token || !dbId) return
    setLoading(true)
    setError(null)
    try {
      const result = await addManual({
        title: manualTitle,
        company: manualCompany,
        url: manualUrl,
        notion_token: token,
        database_id: dbId,
      })
      setSavedJob(result.job)
      setStage('saved')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setStage('url-input')
    setUrl('')
    setError(null)
    setSavedJob(null)
    setManualTitle('')
    setManualCompany('')
    setManualUrl('')
  }

  if (!ready) return null

  return (
    <div className="max-w-2xl mx-auto px-8 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold mb-1" style={{ color: 'var(--text)' }}>Add a Job</h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Paste a LinkedIn or Indeed job URL to save it to Notion
        </p>
      </div>

      {stage === 'url-input' && (
        <form
          onSubmit={handleScrape}
          style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}
          className="p-5 space-y-4"
        >
          <div className="space-y-1.5">
            <label className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              Job URL
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://linkedin.com/jobs/view/..."
              required
              style={inputStyle}
              className={inputClass}
            />
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              Works with LinkedIn and Indeed job pages
            </p>
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
            {loading ? 'Extracting job details…' : 'Save to Notion'}
          </button>
        </form>
      )}

      {stage === 'manual-fallback' && (
        <div className="space-y-4">
          <div
            style={{ background: 'var(--warning-bg)', border: '1px solid #f5c27a', borderRadius: 'var(--radius)', color: 'var(--warning)' }}
            className="px-4 py-3 text-sm"
          >
            Couldn&apos;t auto-extract details — LinkedIn may have blocked it. Fill in the fields below manually.
          </div>

          <form
            onSubmit={handleManualSave}
            style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}
            className="p-5 space-y-4"
          >
            {[
              { label: 'Job title', value: manualTitle, setter: setManualTitle, placeholder: 'e.g. Software Engineer Intern', type: 'text' },
              { label: 'Company', value: manualCompany, setter: setManualCompany, placeholder: 'e.g. Google', type: 'text' },
              { label: 'Job URL', value: manualUrl, setter: setManualUrl, placeholder: 'https://...', type: 'url' },
            ].map(({ label, value, setter, placeholder, type }) => (
              <div key={label} className="space-y-1.5">
                <label className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                  {label}
                </label>
                <input
                  type={type}
                  value={value}
                  onChange={(e) => setter(e.target.value)}
                  placeholder={placeholder}
                  required
                  style={inputStyle}
                  className={inputClass}
                />
              </div>
            ))}

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
              {loading ? 'Saving…' : 'Save to Notion'}
            </button>
          </form>
        </div>
      )}

      {stage === 'saved' && savedJob && (
        <div className="space-y-4">
          <div
            style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}
            className="px-6 py-8 text-center space-y-2"
          >
            <p className="text-3xl mb-3">✅</p>
            <p className="text-base font-medium" style={{ color: 'var(--text)' }}>{savedJob.title}</p>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{savedJob.company}</p>
            <p className="text-sm mt-1" style={{ color: 'var(--success)' }}>Saved to Notion</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={reset}
              style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text)' }}
              className="py-2.5 text-sm font-medium hover:bg-[var(--sidebar)] transition-colors"
            >
              Add another
            </button>
            <Link
              href="/"
              style={{ background: 'var(--accent)', borderRadius: 'var(--radius)', color: '#fff' }}
              className="flex items-center justify-center py-2.5 text-sm font-medium hover:opacity-90 transition-opacity"
            >
              Back home
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
