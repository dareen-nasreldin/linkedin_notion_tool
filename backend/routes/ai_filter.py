import re

_STOP_WORDS = {"in", "at", "for", "the", "and", "a", "an", "of", "to", "with"}

RECRUITER_COMPANY_PATTERNS = [
    r"staffing",
    r"recruiting",
    r"recruitment",
    r"talent",
    r"consulting",
    r"consultants",
    r"confidential",
    r"various",
    r"outsourcing",
    r"manpower",
    r"placement",
    r"sourcing",
    r"hr\s*partners",
    r"hr\s*solutions",
    r"workforce",
    r"personnel",
    r"staffworks",
    r"adecco",
    r"kforce",
    r"robert\s*half",
    r"hays",
    r"modis",
    r"infosys\s*bpm",
    r"tech\s*mahindra",
    r"kelly",
    r"michael\s*page",
    r"volt",
    r"hudson",
]

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

JUNIOR_TITLE_PATTERNS = [
    r"\bintern\b",
    r"\binternship\b",
    r"\bjunior\b",
    r"\bjr\.\b",
]

JUNIOR_SEARCH_KEYWORDS = [
    "intern", "internship", "junior", "entry", "entry-level",
    "co-op", "coop", "new grad", "graduate", "trainee",
]

SENIOR_SEARCH_KEYWORDS = [
    "senior", "sr.", "lead", "staff", "principal",
]


def _keyword_tokens(keyword: str) -> list[str]:
    return [t for t in keyword.lower().split() if t not in _STOP_WORDS]


def _is_recruiter_spam(company: str) -> bool:
    c = company.lower()
    return any(re.search(p, c) for p in RECRUITER_COMPANY_PATTERNS)


def _is_seniority_mismatch(title: str, keyword: str) -> bool:
    kw = keyword.lower()
    t = title.lower()
    if any(k in kw for k in JUNIOR_SEARCH_KEYWORDS):
        return any(re.search(p, t) for p in SENIOR_TITLE_PATTERNS)
    if any(k in kw for k in SENIOR_SEARCH_KEYWORDS):
        return any(re.search(p, t) for p in JUNIOR_TITLE_PATTERNS)
    return False


def _is_low_relevance(title: str, keyword: str) -> bool:
    tokens = _keyword_tokens(keyword)
    if not tokens:
        return False
    t = title.lower()
    return not any(tok in t for tok in tokens)


def filter_jobs(jobs: list[dict], keyword: str) -> list[dict]:
    """
    Classify jobs. All jobs are kept and saved to Notion — bad ones get a
    flagged_reason written to the Flagged column so the user can review them.
    Recruiter spam is the only case that is outright dropped (decision=filter).
    """
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

        flags = []
        if _is_seniority_mismatch(title, keyword):
            flags.append("seniority mismatch")
        if _is_low_relevance(title, keyword):
            flags.append("low relevance")

        flagged_reason = "; ".join(flags)
        job["flagged_reason"] = flagged_reason
        result.append({
            "job": job,
            "decision": "keep",
            "reason": flagged_reason or None,
        })

    return result
