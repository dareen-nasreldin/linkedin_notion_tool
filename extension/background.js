const BACKEND = 'https://backend-nu-two-54.vercel.app'

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type !== 'SAVE_JOB') return false

  const { job, notion_token, database_id } = msg

  fetch(`${BACKEND}/api/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jobs: [job], notion_token, database_id }),
  })
    .then(r => r.json())
    .then(data => sendResponse({ ok: true, data }))
    .catch(err => sendResponse({ ok: false, error: err.message }))

  return true  // keep message channel open for async response
})
