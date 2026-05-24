"""Unit tests for the job classification / filtering logic."""
import pytest
from routes.ai_filter import (
    filter_jobs,
    _is_recruiter_spam,
    _is_seniority_mismatch,
    _is_low_relevance,
)


# ── Helper: make a minimal job dict ──────────────────────────────────────────

def job(title, company, url="https://example.com/job"):
    return {"title": title, "company": company, "url": url}


# ── _is_recruiter_spam ────────────────────────────────────────────────────────

class TestRecruiterSpam:
    def test_staffing_in_name(self):
        assert _is_recruiter_spam("TechStaffing Inc") is True

    def test_recruiting_in_name(self):
        assert _is_recruiter_spam("Acme Recruiting") is True

    def test_known_agency(self):
        assert _is_recruiter_spam("Hays") is True
        assert _is_recruiter_spam("Adecco") is True
        assert _is_recruiter_spam("Robert Half") is True

    def test_talent_in_name(self):
        assert _is_recruiter_spam("Global Talent Solutions") is True

    def test_confidential(self):
        assert _is_recruiter_spam("Confidential") is True

    def test_real_companies_pass(self):
        assert _is_recruiter_spam("Google") is False
        assert _is_recruiter_spam("Shopify") is False
        assert _is_recruiter_spam("Stripe") is False
        assert _is_recruiter_spam("Apple") is False


# ── _is_seniority_mismatch ────────────────────────────────────────────────────

class TestSeniorityMismatch:
    def test_searching_intern_gets_senior(self):
        assert _is_seniority_mismatch("Senior Software Engineer", "software engineer intern") is True

    def test_searching_intern_gets_intern(self):
        assert _is_seniority_mismatch("Software Engineer Intern", "software engineer intern") is False

    def test_searching_junior_gets_lead(self):
        assert _is_seniority_mismatch("Lead Developer", "junior developer") is True

    def test_searching_senior_gets_intern(self):
        assert _is_seniority_mismatch("Software Engineer Intern", "senior software engineer") is True

    def test_searching_senior_gets_senior(self):
        assert _is_seniority_mismatch("Senior Software Engineer", "senior software engineer") is False

    def test_no_seniority_keywords_no_mismatch(self):
        assert _is_seniority_mismatch("Software Engineer", "software engineer") is False


# ── _is_low_relevance ─────────────────────────────────────────────────────────

class TestLowRelevance:
    def test_unrelated_title(self):
        assert _is_low_relevance("Marketing Manager", "software engineer") is True

    def test_matching_title(self):
        assert _is_low_relevance("Software Engineer II", "software engineer") is False

    def test_partial_keyword_match(self):
        assert _is_low_relevance("Data Engineer", "engineer") is False

    def test_empty_keyword_never_low_relevance(self):
        assert _is_low_relevance("Anything At All", "") is False

    def test_stopwords_stripped_from_keyword(self):
        # "for the" stripped → tokens = ["engineer"] → matches "Engineer"
        assert _is_low_relevance("Software Engineer", "for the engineer") is False


# ── filter_jobs (end-to-end pipeline) ────────────────────────────────────────

class TestFilterJobs:
    def test_clean_job_is_kept(self):
        jobs = [job("Software Engineer", "Shopify")]
        result = filter_jobs(jobs, "software engineer")
        assert result[0]["decision"] == "keep"
        assert result[0]["job"]["flagged_reason"] == ""

    def test_recruiter_spam_is_dropped(self):
        jobs = [job("Software Engineer", "TechStaffing Solutions")]
        result = filter_jobs(jobs, "software engineer")
        assert result[0]["decision"] == "filter"
        assert result[0]["reason"] == "RECRUITER_SPAM"

    def test_duplicate_is_dropped(self):
        j = job("Software Engineer", "Google", url="https://example.com/j1")
        result = filter_jobs([j, j.copy()], "software engineer")
        decisions = [r["decision"] for r in result]
        assert decisions[0] == "keep"
        assert decisions[1] == "filter"
        assert result[1]["reason"] == "DUPLICATE"

    def test_seniority_mismatch_flagged_but_kept(self):
        jobs = [job("Senior Software Engineer", "Stripe")]
        result = filter_jobs(jobs, "software engineer intern")
        assert result[0]["decision"] == "keep"
        assert "seniority mismatch" in result[0]["job"]["flagged_reason"]

    def test_low_relevance_flagged_but_kept(self):
        jobs = [job("Marketing Manager", "Acme")]
        result = filter_jobs(jobs, "software engineer")
        assert result[0]["decision"] == "keep"
        assert "low relevance" in result[0]["job"]["flagged_reason"]

    def test_both_flags_combined(self):
        jobs = [job("Senior Marketing Manager", "Acme")]
        result = filter_jobs(jobs, "junior software engineer")
        flagged = result[0]["job"]["flagged_reason"]
        assert "seniority mismatch" in flagged
        assert "low relevance" in flagged

    def test_multiple_jobs_mixed(self):
        jobs = [
            job("Software Engineer", "Google", "https://example.com/1"),
            job("Software Engineer", "TechStaffing", "https://example.com/2"),
            job("Senior Engineer", "Amazon", "https://example.com/3"),
        ]
        result = filter_jobs(jobs, "software engineer intern")
        assert result[0]["decision"] == "keep"
        assert result[1]["decision"] == "filter"   # recruiter spam
        assert result[2]["decision"] == "keep"
        assert "seniority mismatch" in result[2]["job"]["flagged_reason"]

    def test_dedup_is_case_insensitive(self):
        j1 = job("Software Engineer", "Google", "https://example.com/j")
        j2 = {**j1, "title": "SOFTWARE ENGINEER", "company": "GOOGLE"}
        result = filter_jobs([j1, j2], "software engineer")
        assert result[1]["decision"] == "filter"
        assert result[1]["reason"] == "DUPLICATE"

    def test_flagged_reason_on_job_object(self):
        """flagged_reason must be set directly on the job dict, not just in reason."""
        jobs = [job("Senior Engineer", "Stripe")]
        result = filter_jobs(jobs, "junior engineer")
        assert "flagged_reason" in result[0]["job"]
