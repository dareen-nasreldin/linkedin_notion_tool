'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { clearCredentials, getToken, getDatabaseId } from '@/lib/token'

const NAV = [
  { href: '/', label: 'Home', icon: '🏠' },
  { href: '/search', label: 'Search Jobs', icon: '🔍' },
  { href: '/add-url', label: 'Add a Job', icon: '🔗' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()

  const [copied, setCopied] = useState(false)

  function handleReset() {
    clearCredentials()
    router.push('/setup')
  }

  function handleCopySetupLink() {
    const t = getToken()
    const d = getDatabaseId()
    if (!t || !d) return
    const url = `https://notionjobs.vercel.app/setup?token=${encodeURIComponent(t)}&db=${encodeURIComponent(d)}`
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        style={{ background: 'var(--sidebar)', borderRight: '1px solid var(--border)' }}
        className="hidden md:flex flex-col w-56 shrink-0 h-screen sticky top-0"
      >
        {/* Logo */}
        <div
          style={{ borderBottom: '1px solid var(--border)' }}
          className="px-3 py-3"
        >
          <div className="flex items-center gap-2 px-2 py-1">
            <span className="text-base leading-none">💼</span>
            <span className="text-sm font-semibold tracking-tight" style={{ color: 'var(--text)' }}>
              NotionJobs
            </span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-1.5 space-y-px">
          {NAV.map(({ href, label, icon }) => {
            const active = pathname === href
            return (
              <Link
                key={href}
                href={href}
                style={{
                  background: active ? 'var(--sidebar-active)' : 'transparent',
                  color: active ? 'var(--text)' : 'var(--text-muted)',
                  borderRadius: 'var(--radius)',
                }}
                className="flex items-center gap-2 px-2 py-1.5 text-sm transition-colors hover:bg-[var(--sidebar-hover)] hover:!text-[var(--text)]"
              >
                <span className="text-base leading-none">{icon}</span>
                <span className={active ? 'font-medium' : ''}>{label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Settings */}
        <div style={{ borderTop: '1px solid var(--border)' }} className="p-1.5 space-y-px">
          <button
            onClick={handleCopySetupLink}
            style={{ color: copied ? 'var(--success)' : 'var(--text-muted)', borderRadius: 'var(--radius)' }}
            className="flex items-center gap-2 w-full px-2 py-1.5 text-sm transition-colors hover:bg-[var(--sidebar-hover)] hover:!text-[var(--text)]"
          >
            <span className="text-base leading-none">{copied ? '✓' : '🔗'}</span>
            <span>{copied ? 'Copied!' : 'Copy setup link'}</span>
          </button>
          <button
            onClick={handleReset}
            style={{ color: 'var(--text-muted)', borderRadius: 'var(--radius)' }}
            className="flex items-center gap-2 w-full px-2 py-1.5 text-sm transition-colors hover:bg-[var(--sidebar-hover)] hover:!text-[var(--text)]"
          >
            <span className="text-base leading-none">⚙️</span>
            <span>Reset connection</span>
          </button>
        </div>
      </aside>

      {/* Mobile top bar */}
      <div
        style={{ background: 'var(--sidebar)', borderBottom: '1px solid var(--border)' }}
        className="md:hidden fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 h-12"
      >
        <div className="flex items-center gap-2">
          <span className="text-base">💼</span>
          <span className="text-sm font-semibold">NotionJobs</span>
        </div>
        <div className="flex items-center gap-1">
          {NAV.map(({ href, icon }) => (
            <Link
              key={href}
              href={href}
              style={{
                background: pathname === href ? 'var(--sidebar-active)' : 'transparent',
                borderRadius: 'var(--radius)',
              }}
              className="p-2 text-base transition-colors hover:bg-[var(--sidebar-hover)]"
            >
              {icon}
            </Link>
          ))}
        </div>
      </div>
    </>
  )
}
