'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { setupNotion } from '@/lib/api'
import { saveCredentials } from '@/lib/token'

const STEPS = [
  {
    number: 1,
    title: 'Create a Notion integration',
    description: (
      <>
        Go to{' '}
        <a
          href="https://www.notion.so/profile/integrations"
          target="_blank"
          rel="noopener noreferrer"
          className="text-violet-400 underline hover:text-violet-300"
        >
          notion.so/profile/integrations
        </a>
        , click <strong>New connection</strong>, give it any name (e.g. <em>Job Tracker</em>),
        select your workspace, then click <strong>Create</strong>.
      </>
    ),
    images: [
      { src: '/setup/integration.png', alt: 'Internal connections page — click Create a new connection' },
      { src: '/setup/integration2.png', alt: 'New connection form — fill in the name and click Create' },
    ],
  },
  {
    number: 2,
    title: 'Share a Notion page with your integration',
    description: (
      <>
        Open any page in your Notion workspace. Click the <strong>…</strong> menu (top right) →{' '}
        <strong>Connections</strong> → find <em>Job Tracker</em> and click it to connect. This
        gives the tool a place to create your database.
      </>
    ),
    images: [
      { src: '/setup/connection.png', alt: 'Connections menu on a Notion page — select your integration' },
    ],
  },
  {
    number: 3,
    title: 'Copy your integration token',
    description: (
      <>
        Back on the integrations page, open your <em>Job Tracker</em> connection. Under{' '}
        <strong>Integration token</strong>, click the copy icon next to the hidden token and
        paste it below.
      </>
    ),
    images: [
      { src: '/setup/token.png', alt: 'Manage connection page — copy the Access token' },
    ],
  },
]

export default function SetupPage() {
  const router = useRouter()
  const [token, setToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!token.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await setupNotion(token.trim())
      saveCredentials(token.trim(), result.database_id)
      router.push('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center px-4 py-16">
      <div className="w-full max-w-xl space-y-10">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">Connect your Notion</h1>
          <p className="text-slate-400">One-time setup — takes about 2 minutes</p>
        </div>

        <div className="space-y-6">
          {STEPS.map((step) => (
            <div key={step.number} className="rounded-2xl bg-slate-800/60 border border-slate-700 overflow-hidden">
              <div className="flex gap-4 p-5">
                <div className="flex-shrink-0 flex items-start justify-center w-8 h-8 rounded-full bg-violet-600 text-sm font-bold mt-0.5">
                  {step.number}
                </div>
                <div className="space-y-1">
                  <p className="font-semibold">{step.title}</p>
                  <p className="text-sm text-slate-400 leading-relaxed">{step.description}</p>
                </div>
              </div>

              {step.images.length > 0 && (
                <div className={`grid gap-2 px-5 pb-5 ${step.images.length > 1 ? 'grid-cols-2' : 'grid-cols-1'}`}>
                  {step.images.map((img) => (
                    <div key={img.src} className="rounded-xl overflow-hidden border border-slate-700">
                      <Image
                        src={img.src}
                        alt={img.alt}
                        width={600}
                        height={400}
                        className="w-full h-auto object-cover"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="token" className="text-sm font-medium text-slate-300">
              Integration token
            </label>
            <input
              id="token"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="ntn_..."
              required
              className="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            />
          </div>

          {error && (
            <div className="rounded-xl bg-red-900/40 border border-red-700 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !token.trim()}
            className="w-full rounded-xl bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:text-slate-500 transition-colors py-3 font-semibold"
          >
            {loading ? 'Setting up your database…' : 'Connect & Set Up'}
          </button>
        </form>
      </div>
    </main>
  )
}
