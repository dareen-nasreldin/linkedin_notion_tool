'use client'

export default function ExtensionPage() {
  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      <div className="max-w-xl mx-auto px-6 py-12">

        {/* Hero */}
        <div className="text-center mb-10">
          <div className="text-5xl mb-4">🧩</div>
          <h1 className="text-2xl font-bold mb-3" style={{ color: 'var(--text)' }}>
            NotionJobs Chrome Extension
          </h1>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
            Save LinkedIn job listings to your Notion tracker in one click —
            without leaving LinkedIn.
          </p>
        </div>

        {/* Download card */}
        <div
          className="rounded-xl p-6 mb-6"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--text)' }}>
            Install the extension
          </h2>

          <div className="space-y-4">
            {/* Step 1 */}
            <Step n={1} title="Download the extension">
              <a
                href="/notionjobs-extension.zip"
                download
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium mt-2 transition-opacity hover:opacity-85"
                style={{ background: 'var(--accent)', color: 'var(--accent-fg)' }}
              >
                <span>⬇️</span> Download notionjobs-extension.zip
              </a>
            </Step>

            {/* Step 2 */}
            <Step n={2} title="Open Chrome Extensions">
              <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                Go to{' '}
                <Code>chrome://extensions</Code>
                {' '}in your browser.
              </p>
            </Step>

            {/* Step 3 */}
            <Step n={3} title="Enable Developer Mode">
              <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                Toggle <strong style={{ color: 'var(--text)' }}>Developer mode</strong> on
                (top-right corner of the extensions page).
              </p>
            </Step>

            {/* Step 4 */}
            <Step n={4} title="Unzip and load the extension">
              <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                Unzip the file you downloaded. Then click{' '}
                <strong style={{ color: 'var(--text)' }}>Load unpacked</strong>{' '}
                and select the unzipped folder.
              </p>
            </Step>

            {/* Step 5 */}
            <Step n={5} title="Connect to your Notion">
              <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                Come back here, click{' '}
                <strong style={{ color: 'var(--text)' }}>Export for extension</strong>{' '}
                in the sidebar, then paste the credentials into the extension popup.
              </p>
            </Step>
          </div>
        </div>

        {/* Usage card */}
        <div
          className="rounded-xl p-6"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
            How to use it
          </h2>
          <ol className="space-y-2">
            {[
              'Browse jobs on LinkedIn as normal.',
              'Open any job listing you\'re interested in.',
              'Click the NotionJobs icon in your Chrome toolbar.',
              'Hit "Save to Notion" — done.',
            ].map((step, i) => (
              <li key={i} className="flex items-start gap-3">
                <span
                  className="text-xs font-semibold mt-0.5 w-5 h-5 flex items-center justify-center rounded-full shrink-0"
                  style={{ background: 'var(--accent)', color: 'var(--accent-fg)' }}
                >
                  {i + 1}
                </span>
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{step}</span>
              </li>
            ))}
          </ol>
        </div>

      </div>
    </div>
  )
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-3">
      <span
        className="text-xs font-semibold w-5 h-5 flex items-center justify-center rounded-full shrink-0 mt-0.5"
        style={{ background: 'var(--accent)', color: 'var(--accent-fg)' }}
      >
        {n}
      </span>
      <div className="flex-1">
        <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{title}</p>
        {children}
      </div>
    </div>
  )
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code
      className="px-1.5 py-0.5 rounded text-xs font-mono"
      style={{ background: 'var(--bg)', color: 'var(--accent)', border: '1px solid var(--border)' }}
    >
      {children}
    </code>
  )
}
