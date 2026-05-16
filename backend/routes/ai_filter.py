import re

# Companies matching these patterns are likely staffing/recruiting agencies.
# Add more entries here any time you notice spam slipping through.
RECRUITER_COMPANY_PATTERNS = [
    r"\bstaffing\b",
    r"\brecruiting\b",
    r"\brecruitment\b",
    r"\btalent\b",
    r"\bconsulting\b",
    r"\bconsultants\b",
    r"\bconfidential\b",
    r"\bvarious\b",
    r"\boutsourcing\b",
    r"\bmanpower\b",
    r"\bplacement\b",
    r"\bsourcing\b",
    r"\bhr partners\b",
    r"\bhr solutions\b",
    r"\bworkforce\b",
    r"\bpersonnel\b",
    r"\bstaffworks\b",
    # Known large agencies
    r"\badecco\b",
    r"\bkforce\b",
    r"\broberthalf\b",
    r"\bhays\b",
    r"\bmodis\b",
    r"\binfosys bpm\b",
    r"\btech mahindra\b",
]

# Job titles with these words are senior-level roles.
SENIOR_TITLE_PATTERNS = [
    r"\bsenior\b",
    r"\bsr\.\b",
    r"\blead\b",
    r"\bprincipal\b",
    r"\bdirector\b",
    r"\bmanager\b",
    r"\bvp\b",
    r"\bvice president\b",
    r"\bhead of\b",
    r"\bchief\b",
    r"\barchitect\b",
    r"\bstaff engineer\b",
    r"\bstaff software\b",
]

# If the search keyword contains any of these, seniority filtering kicks in.
JUNIOR_SEARCH_KEYWORDS = [
    "intern",
    "internship",
    "junior",
    "entry",
    "entry-level",
    "co-op",
    "coop",
    "new grad",
    "graduate",
    "trainee",
]


def _is_recruiter_spam(company: str) -> bool:
    c = company.lower()
    return any(re.search(p, c) for p in RECRUITER_COMPANY_PATTERNS)


def _is_seniority_mismatch(title: str, keyword: str) -> bool:
    if not any(k in keyword.lower() for k in JUNIOR_SEARCH_KEYWORDS):
        return False
    t = title.lower()
    return any(re.search(p, t) for p in SENIOR_TITLE_PATTERNS)


def filter_jobs(jobs: list[dict], keyword: str) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    result = []

    for job in jobs:
        title = job.get("title", "")
        company = job.get("company", "")

        dedup_key = (title.lower().strip(), company.lower().strip())
        if dedup_key in seen:
            result.append({"job": job, "decision": "filter", "reason": "DUPLICATE"})
            continue
        seen.add(dedup_key)

        if _is_recruiter_spam(company):
            result.append({"job": job, "decision": "filter", "reason": "RECRUITER_SPAM"})
            continue

        if _is_seniority_mismatch(title, keyword):
            result.append({"job": job, "decision": "filter", "reason": "SENIORITY_MISMATCH"})
            continue

        result.append({"job": job, "decision": "keep", "reason": None})

    return result
