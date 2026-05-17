import pandas as pd

_STOP_WORDS = {"in", "at", "for", "the", "and", "a", "an", "of", "to", "with"}

_SENIOR_TERMS = {
    "senior", "sr.", "sr ", "lead", "staff", "principal",
    "director", "manager", "vp", "head of", "chief",
}

_JUNIOR_SEARCH_TERMS = {"intern", "internship", "junior", "jr.", "jr ", "entry level", "entry-level", "new grad"}
_SENIOR_SEARCH_TERMS = {"senior", "sr.", "lead", "staff", "principal"}


def _keyword_tokens(keyword: str) -> list[str]:
    return [t for t in keyword.lower().split() if t not in _STOP_WORDS]


def _check_missing_fields(row) -> bool:
    for field in ("title", "company", "job_url"):
        val = row.get(field)
        if val is None or (isinstance(val, float) and pd.isna(val)) or str(val).strip() == "":
            return True
    return False


def _check_seniority_mismatch(title: str, keyword: str) -> bool:
    kw = keyword.lower()
    t = title.lower()
    if any(jt in kw for jt in _JUNIOR_SEARCH_TERMS):
        return any(st in t for st in _SENIOR_TERMS)
    if any(st in kw for st in _SENIOR_SEARCH_TERMS):
        # searching senior but got intern/junior result
        return any(jt in t for jt in {"intern", "internship", "junior", "jr."})
    return False


def _check_low_relevance(title: str, keyword: str) -> bool:
    tokens = _keyword_tokens(keyword)
    if not tokens:
        return False
    t = title.lower()
    return not any(tok in t for tok in tokens)


def flag_jobs(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """Add a 'flagged_reason' column to df. Empty string means clean."""
    df = df.copy()
    reasons = []
    for _, row in df.iterrows():
        flags = []
        if _check_missing_fields(row):
            flags.append("missing fields")
        title = str(row.get("title", ""))
        if not flags:
            if _check_seniority_mismatch(title, keyword):
                flags.append("seniority mismatch")
            if _check_low_relevance(title, keyword):
                flags.append("low relevance")
        reasons.append("; ".join(flags))
    df["flagged_reason"] = reasons
    return df
