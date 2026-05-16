'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { getToken, getDatabaseId, clearCredentials } from '@/lib/token'

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
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-md space-y-10">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">Job Tracker</h1>
          <p className="text-slate-400">Search jobs and save them straight to Notion</p>
        </div>

        <div className="grid gap-4">
          <Link
            href="/search"
            className="flex flex-col items-center gap-1 rounded-2xl bg-violet-600 hover:bg-violet-500 active:bg-violet-700 transition-colors px-6 py-8 text-center"
          >
            <span className="text-3xl">🔍</span>
            <span className="text-xl font-semibold">Search Jobs</span>
            <span className="text-sm text-violet-200">
              Bulk search LinkedIn &amp; Indeed by keyword
            </span>
          </Link>

          <Link
            href="/add-url"
            className="flex flex-col items-center gap-1 rounded-2xl bg-slate-800 hover:bg-slate-700 active:bg-slate-900 transition-colors px-6 py-8 text-center border border-slate-700"
          >
            <span className="text-3xl">🔗</span>
            <span className="text-xl font-semibold">Add a Job</span>
            <span className="text-sm text-slate-400">
              Paste a LinkedIn or Indeed job URL
            </span>
          </Link>
        </div>

        <div className="text-center">
          <button
            onClick={() => {
              clearCredentials()
              router.push('/setup')
            }}
            className="text-sm text-slate-500 hover:text-slate-300 underline underline-offset-4 transition-colors"
          >
            Reset Notion connection
          </button>
        </div>
      </div>
    </main>
  )
}
