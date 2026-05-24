"""
Pytest configuration.

Stubs out jobspy so the integration tests can import the FastAPI app
without needing the full jobspy/numpy stack installed locally.
"""
import sys
from unittest.mock import MagicMock

# Stub jobspy before any test module imports routes.jobs
jobspy_mock = MagicMock()
jobspy_mock.scrape_jobs.return_value = None
sys.modules.setdefault("jobspy", jobspy_mock)
