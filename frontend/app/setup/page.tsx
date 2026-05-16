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
          style={{ color: 'var(--accent)' }}
          className="hover:underline"
        >
          notion.so/profile/integrations
        </a>
        , click <strong>New connection</strong>, name it <em>Job Tracker</em>, select your
        workspace, then click <strong>Create</strong>.
      </>
    ),
    images: [
      { src: '/setup/integration.png', alt: 'Internal connections page' },
      { src: '/setup/integration2.png', alt: 'New connection form' },
    ],
  },
  {
    number: 2,
    title: 'Share a page with your integration',
    description: (
      <>
        Open any Notion page, click <strong>…</strong> (top right) → <strong>Connections</strong>{' '}
        → find <em>Job Tracker</em> and select it. This gives the tool a place to create your
        database.
      </>
    ),
    images: [
      { src: '/setup/connection.png', alt: 'Connecting the integration to a page' },
    ],
  },
  {
    number: 3,
    title: 'Copy your integration token',
    description: (
      <>
        Back on the integrations page, open <em>Job Tracker</em>. Under{' '}
        <strong>Integration token</strong>, click the copy icon and paste it below.
      </>
    ),
    images: [
      { src: '/setup/token.png', alt: 'Copying the integration token' },
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
    <div className="max-w-2xl mx-auto px-8 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold mb-1" style={{ color: 'var(--text)' }}>
          Connect Notion
        </h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          One-time setup — takes about 2 minutes
        </p>
      </div>

      {/* Steps */}
      <div className="space-y-4 mb-10">
        {STEPS.map((step) => (
          <div
            key={step.number}
            style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}
            className="overflow-hidden"
          >
            <div className="px-5 py-4 flex gap-4">
              <div
                style={{
                  background: 'var(--accent)',
                  color: '#fff',
                  borderRadius: '50%',
                  width: 22,
                  height: 22,
                  fontSize: 11,
                  fontWeight: 600,
                }}
                className="flex-shrink-0 flex items-center justify-center mt-0.5"
              >
                {step.number}
              </div>
              <div>
                <p className="text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  {step.title}
                </p>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                  {step.description}
                </p>
              </div>
            </div>

            {step.images.length > 0 && (
              <div
                style={{ borderTop: '1px solid var(--border)', background: 'var(--sidebar)' }}
                className={`grid gap-3 px-5 py-4 ${step.images.length > 1 ? 'grid-cols-2' : 'grid-cols-1'}`}
              >
                {step.images.map((img) => (
                  <div
                    key={img.src}
                    style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}
                  >
                    <Image
                      src={img.src}
                      alt={img.alt}
                      width={560}
                      height={360}
                      className="w-full h-auto"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Token form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label htmlFor="token" className="text-sm font-medium" style={{ color: 'var(--text)' }}>
            Integration token
          </label>
          <input
            id="token"
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="ntn_..."
            required
            style={{
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              background: 'var(--input-bg)',
              color: 'var(--text)',
            }}
            className="w-full px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)] placeholder:text-[var(--text-placeholder)]"
          />
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
          disabled={loading || !token.trim()}
          style={{
            background: loading || !token.trim() ? 'var(--border)' : 'var(--accent)',
            color: loading || !token.trim() ? 'var(--text-muted)' : '#fff',
            borderRadius: 'var(--radius)',
          }}
          className="w-full py-2.5 text-sm font-medium transition-colors hover:opacity-90 disabled:cursor-not-allowed"
        >
          {loading ? 'Setting up…' : 'Connect & Set Up'}
        </button>
      </form>
    </div>
  )
}
