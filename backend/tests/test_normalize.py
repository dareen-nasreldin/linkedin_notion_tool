"""Unit tests for job_type normalization before Notion save."""
from routes.notion_api import _normalize_job_type


class TestNormalizeJobType:
    # ── Full-time variants ────────────────────────────────────────────────────
    def test_fulltime_no_hyphen(self):
        assert _normalize_job_type("fulltime") == "Full-time"

    def test_fulltime_hyphen(self):
        assert _normalize_job_type("full-time") == "Full-time"

    def test_fulltime_space(self):
        assert _normalize_job_type("full time") == "Full-time"

    def test_fulltime_uppercase(self):
        assert _normalize_job_type("FULLTIME") == "Full-time"

    # ── Part-time variants ────────────────────────────────────────────────────
    def test_parttime_no_hyphen(self):
        assert _normalize_job_type("parttime") == "Part-time"

    def test_parttime_hyphen(self):
        assert _normalize_job_type("part-time") == "Part-time"

    def test_parttime_space(self):
        assert _normalize_job_type("part time") == "Part-time"

    # ── Internship variants ───────────────────────────────────────────────────
    def test_internship(self):
        assert _normalize_job_type("internship") == "Internship"

    def test_intern(self):
        assert _normalize_job_type("intern") == "Internship"

    def test_intern_uppercase(self):
        assert _normalize_job_type("INTERNSHIP") == "Internship"

    # ── Contract / Temporary ──────────────────────────────────────────────────
    def test_contract(self):
        assert _normalize_job_type("contract") == "Contract"

    def test_contractor(self):
        assert _normalize_job_type("contractor") == "Contract"

    def test_temporary(self):
        assert _normalize_job_type("temporary") == "Temporary"

    def test_temp(self):
        assert _normalize_job_type("temp") == "Temporary"

    # ── The bug that broke prod: comma-separated values ───────────────────────
    def test_comma_separated_takes_first(self):
        assert _normalize_job_type("Parttime, fulltime, internship") == "Part-time"

    def test_comma_separated_fulltime_first(self):
        assert _normalize_job_type("fulltime, parttime") == "Full-time"

    def test_comma_with_spaces(self):
        assert _normalize_job_type("  internship ,  fulltime") == "Internship"

    # ── Unknown / garbage ─────────────────────────────────────────────────────
    def test_unknown_returns_none(self):
        assert _normalize_job_type("gig work") is None

    def test_empty_returns_none(self):
        assert _normalize_job_type("") is None

    def test_gibberish_returns_none(self):
        assert _normalize_job_type("xyzabc") is None
