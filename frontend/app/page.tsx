'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getToken, getDatabaseId } from '@/lib/token'

const ACTIONS = [
  {
    href: '/search',
    icon: '🔍',
    title: 'Search Jobs',
    desc: 'Bulk search LinkedIn & Indeed by keyword, location, and country',
  },
  {
    href: '/add-url',
    icon: '🔗',
    title: 'Add a Job',
    desc: 'Paste a job URL and save it directly to your Notion database',
  },
]

export default function Home() {
  const router = useRouter()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (!getToken() || !getDatabaseId()) {
      router.push('/setup')
    } else {
      setReady(true)
    }
  }, [router])

  if (!ready) return null

  return (
    <div className="max-w-2xl mx-auto px-8 py-12">
      <div className="mb-10">
        <h1 className="text-2xl font-semibold mb-1" style={{ color: 'var(--text)' }}>
          Job Tracker
        </h1>
        <p style={{ color: 'var(--text-muted)' }} className="text-sm">
          Search for jobs and save them directly to your Notion workspace
        </p>
      </div>

      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
          Actions
        </p>
        {ACTIONS.map(({ href, icon, title, desc }) => (
          <Link
            key={href}
            href={href}
            style={{
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
            }}
            className="flex items-start gap-4 px-5 py-4 bg-white hover:bg-[var(--sidebar)] transition-colors group"
          >
            <span className="text-2xl mt-0.5 leading-none">{icon}</span>
            <div>
              <p className="text-sm font-medium mb-0.5" style={{ color: 'var(--text)' }}>{title}</p>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{desc}</p>
            </div>
            <span
              className="ml-auto text-base opacity-0 group-hover:opacity-100 transition-opacity self-center"
              style={{ color: 'var(--text-muted)' }}
            >
              →
            </span>
          </Link>
        ))}
      </div>

      <div
        style={{ background: 'var(--sidebar)', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}
        className="mt-10 px-5 py-4"
      >
        <p className="text-xs font-medium mb-1" style={{ color: 'var(--text)' }}>How filtering works</p>
        <p className="text-sm" style={{ color: 'var(--text-muted)', lineHeight: '1.6' }}>
          Jobs are automatically checked before saving. Recruiter spam, seniority mismatches
          (e.g. senior roles when you searched for intern), and duplicates are skipped.
          Everything else goes straight into Notion.
        </p>
      </div>
    </div>
  )
}
