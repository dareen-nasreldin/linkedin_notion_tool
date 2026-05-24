// Injected into linkedin.com/jobs/* — scrapes job details from the DOM.
// LinkedIn changes their selectors frequently; we try multiple in priority order.

function extractJob() {
  const titleEl =
    document.querySelector('.job-details-jobs-unified-top-card__job-title h1') ||
    document.querySelector('h1.t-24.t-bold') ||
    document.querySelector('h1[class*="job-title"]') ||
    document.querySelector('.jobs-unified-top-card__job-title h1') ||
    document.querySelector('h1')

  const companyEl =
    document.querySelector('.job-details-jobs-unified-top-card__company-name a') ||
    document.querySelector('.job-details-jobs-unified-top-card__company-name') ||
    document.querySelector('.jobs-unified-top-card__company-name a') ||
    document.querySelector('.jobs-unified-top-card__company-name') ||
    document.querySelector('.topcard__org-name-link') ||
    document.querySelector('[class*="company-name"]')

  const locationEl =
    document.querySelector('.job-details-jobs-unified-top-card__bullet') ||
    document.querySelector('.jobs-unified-top-card__bullet') ||
    document.querySelector('.topcard__flavor--bullet')

  return {
    title:    titleEl?.innerText.trim()    || null,
    company:  companyEl?.innerText.trim()  || null,
    location: locationEl?.innerText.trim() || null,
    url:      window.location.href.split('?')[0],  // strip tracking params
  }
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === 'GET_JOB') {
    sendResponse(extractJob())
  }
})
