const viewSetup  = document.getElementById('viewSetup')
const viewJob    = document.getElementById('viewJob')
const viewEmpty  = document.getElementById('viewEmpty')
const credInput  = document.getElementById('credInput')
const connectBtn = document.getElementById('connectBtn')
const setupError = document.getElementById('setupError')
const saveBtn    = document.getElementById('saveBtn')
const saveStatus = document.getElementById('saveStatus')
const gearBtn    = document.getElementById('gearBtn')
const jobTitleEl    = document.getElementById('jobTitle')
const jobCompanyEl  = document.getElementById('jobCompany')
const jobLocationEl = document.getElementById('jobLocation')

let currentJob  = null
let credentials = null

// ── Helpers ───────────────────────────────────────────────────────────────────

function showView(id) {
  [viewSetup, viewJob, viewEmpty].forEach(v => v.classList.remove('active'))
  document.getElementById(id).classList.add('active')
}

function setStatus(el, type, html) {
  el.className = `status ${type}`
  el.innerHTML = html
}

// ── Init ──────────────────────────────────────────────────────────────────────

chrome.storage.sync.get(['notion_token', 'database_id'], async (stored) => {
  if (!stored.notion_token || !stored.database_id) {
    showView('viewSetup')
    return
  }

  credentials = { notion_token: stored.notion_token, database_id: stored.database_id }

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  if (!tab?.url?.includes('linkedin.com/jobs')) {
    showView('viewEmpty')
    return
  }

  try {
    const job = await chrome.tabs.sendMessage(tab.id, { type: 'GET_JOB' })
    if (!job?.title) {
      showView('viewEmpty')
      return
    }
    currentJob = job
    jobTitleEl.textContent    = job.title
    jobCompanyEl.textContent  = job.company  || 'Unknown company'
    jobLocationEl.textContent = job.location || ''
    jobLocationEl.style.display = job.location ? 'block' : 'none'
    showView('viewJob')
  } catch {
    // Content script not yet injected (e.g. page still loading) — show empty
    showView('viewEmpty')
  }
})

// ── Connect ───────────────────────────────────────────────────────────────────

connectBtn.addEventListener('click', () => {
  setupError.textContent = ''
  const raw = credInput.value.trim()

  if (!raw) {
    setupError.textContent = 'Paste your credentials first.'
    return
  }

  let parsed
  try {
    parsed = JSON.parse(raw)
  } catch {
    setupError.textContent = 'Invalid JSON — copy the credentials again.'
    return
  }

  // Accept multiple key name variants
  const token = parsed.notion_token || parsed.token
  const dbId  = parsed.database_id  || parsed.db_id || parsed.db

  if (!token || !dbId) {
    setupError.textContent = 'Missing notion_token or database_id.'
    return
  }

  chrome.storage.sync.set({ notion_token: token, database_id: dbId }, () => {
    window.location.reload()  // re-init with new credentials
  })
})

// ── Save to Notion ────────────────────────────────────────────────────────────

saveBtn.addEventListener('click', () => {
  if (!currentJob || !credentials) return

  saveBtn.disabled = true
  setStatus(saveStatus, 'loading', '<span class="spinner"></span>Saving…')

  chrome.runtime.sendMessage(
    { type: 'SAVE_JOB', job: currentJob, ...credentials },
    (resp) => {
      saveBtn.disabled = false

      if (chrome.runtime.lastError || !resp) {
        setStatus(saveStatus, 'error', 'Extension error — try again.')
        return
      }
      if (!resp.ok) {
        setStatus(saveStatus, 'error', resp.error || 'Something went wrong.')
        return
      }

      const { saved = [], skipped = [], errors = [] } = resp.data

      if (errors.length) {
        setStatus(saveStatus, 'error', errors[0].error)
      } else if (skipped.length) {
        setStatus(saveStatus, 'skip', 'Already in Notion.')
        saveBtn.textContent = 'Already saved'
      } else if (saved.length) {
        setStatus(saveStatus, 'success', '✓ Saved to Notion!')
        saveBtn.textContent = 'Saved ✓'
        saveBtn.className = 'btn btn-success'
      }
    }
  )
})

// ── Gear icon → back to settings ─────────────────────────────────────────────

gearBtn.addEventListener('click', () => {
  showView('viewSetup')
})
