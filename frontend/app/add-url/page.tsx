'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { scrapeUrl, addManual, type Job } from '@/lib/api'
import { getToken, getDatabaseId } from '@/lib/token'

type Stage = 'url-input' | 'manual-fallback' | 'saved'

export default function AddUrlPage() {
  const router = useRouter()
  const [ready, setReady] = useState(false)
  const [stage, setStage] = useState<Stage>('url-input')

  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedJob, setSavedJob] = useState<Job | null>(null)

  // Manual fallback fields
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
        // Auto-scraped — save immediately
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
        // Scraping failed — switch to manual fallback
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
    <main className="flex min-h-screen flex-col items-center px-4 py-12">
      <div className="w-full max-w-lg space-y-8">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-slate-400 hover:text-slate-200 transition-colors text-sm">
            ← Home
          </Link>
          <h1 className="text-2xl font-bold">Add a Job</h1>
        </div>

        {stage === 'url-input' && (
          <form onSubmit={handleScrape} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-300">Job URL</label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://linkedin.com/jobs/view/..."
                required
                className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
              <p className="text-xs text-slate-500">Works with LinkedIn and Indeed job pages</p>
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
              {loading ? 'Scraping job details…' : 'Add to Notion'}
            </button>
          </form>
        )}

        {stage === 'manual-fallback' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-amber-900/30 border border-amber-700 px-4 py-3 text-sm text-amber-300">
              Couldn&apos;t auto-extract job details (LinkedIn may have blocked it). Fill in the details below.
            </div>

            <form onSubmit={handleManualSave} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-300">Job title</label>
                <input
                  type="text"
                  value={manualTitle}
                  onChange={(e) => setManualTitle(e.target.value)}
                  placeholder="e.g. Software Engineer Intern"
                  required
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-300">Company</label>
                <input
                  type="text"
                  value={manualCompany}
                  onChange={(e) => setManualCompany(e.target.value)}
                  placeholder="e.g. Google"
                  required
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-300">Job URL</label>
                <input
                  type="url"
                  value={manualUrl}
                  onChange={(e) => setManualUrl(e.target.value)}
                  required
                  className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
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
                {loading ? 'Saving…' : 'Save to Notion'}
              </button>
            </form>
          </div>
        )}

        {stage === 'saved' && savedJob && (
          <div className="space-y-6">
            <div className="rounded-xl bg-emerald-900/30 border border-emerald-700 px-6 py-8 text-center space-y-2">
              <p className="text-3xl">✅</p>
              <p className="text-lg font-semibold">{savedJob.title}</p>
              <p className="text-slate-400">{savedJob.company}</p>
              <p className="text-sm text-emerald-400 mt-2">Saved to Notion!</p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={reset}
                className="rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors py-3 font-medium text-sm"
              >
                Add another
              </button>
              <Link
                href="/"
                className="flex items-center justify-center rounded-xl bg-violet-600 hover:bg-violet-500 transition-colors py-3 font-medium text-sm"
              >
                Back home
              </Link>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
