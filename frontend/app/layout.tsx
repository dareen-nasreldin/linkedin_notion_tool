import type { Metadata } from 'next'
import { Plus_Jakarta_Sans } from 'next/font/google'
import Sidebar from '@/components/Sidebar'
import './globals.css'

const jakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-jakarta',
})

export const metadata: Metadata = {
  title: 'NotionJobs',
  description: 'Search LinkedIn & Indeed jobs and save them directly to Notion',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={jakarta.variable}>
      <body className="flex h-screen overflow-hidden font-[family-name:var(--font-jakarta)]">
        <Sidebar />
        <main className="flex-1 overflow-y-auto pt-12 md:pt-0">
          {children}
        </main>
      </body>
    </html>
  )
}
