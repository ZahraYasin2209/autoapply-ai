import uuid
from unittest.mock import MagicMock, patch

import pytest

from autoapply.ai.utils.JobSearchUtils import JobSearchUtils
from autoapply.models.Job import Job


# extract_domain_base
def test_extract_domain_base_standard_url():
    assert JobSearchUtils._extract_domain_base("https://greenhouse.io/jobs/123") == "greenhouse"


def test_extract_domain_base_strips_www():
    assert JobSearchUtils._extract_domain_base("https://www.lever.co/acme/apply") == "lever"


def test_extract_domain_base_invalid_url():
    assert JobSearchUtils._extract_domain_base("not-a-url") is None


# is_job_board
def test_is_job_board_returns_true_for_linkedin():
    assert JobSearchUtils._is_job_board("https://linkedin.com/jobs/view/123") is True


def test_is_job_board_returns_false_for_company_site():
    assert JobSearchUtils._is_job_board("https://openai.com/careers/ml-engineer") is False


def test_is_job_board_returns_false_for_invalid_url():
    assert JobSearchUtils._is_job_board("") is False


# parse_company_from_url
def test_parse_company_from_url_uses_domain():
    company = JobSearchUtils._parse_company_from_url("https://stripe.com/jobs/123", "Engineer at Stripe")
    assert company == "Stripe"


def test_parse_company_from_url_falls_back_to_title():
    company = JobSearchUtils._parse_company_from_url(
        "https://linkedin.com/jobs/123", "ML Engineer at DeepMind"
    )
    assert company == "DeepMind"


def test_parse_company_from_url_returns_unknown_when_no_match():
    company = JobSearchUtils._parse_company_from_url("https://linkedin.com/jobs/123", "ml engineer remote")
    assert company == "Unknown"


# build_search_queries
def test_build_search_queries_returns_at_most_four():
    queries = JobSearchUtils._build_search_queries("ML Engineer", "Berlin", "Python,PyTorch", "senior")
    assert len(queries) <= 4


def test_build_search_queries_includes_seniority():
    queries = JobSearchUtils._build_search_queries("Engineer", "remote", None, "junior")
    assert any("junior" in q.lower() for q in queries)


def test_build_search_queries_no_seniority():
    queries = JobSearchUtils._build_search_queries("Engineer", "remote", None, None)
    assert any("Engineer" in q for q in queries)


def test_build_search_queries_remote_location():
    queries = JobSearchUtils._build_search_queries("Engineer", "remote", None)
    assert any("remote" in q.lower() for q in queries)


# search_and_store_jobs
def test_search_and_store_jobs_returns_empty_when_no_api_key(mock_db):
    with patch("autoapply.ai.utils.JobSearchUtils.TAVILY_API_KEY", ""):
        result = JobSearchUtils.search_and_store_jobs(
            db=mock_db, user_id=uuid.uuid4(), target_role="Engineer"
        )
    assert result == []


# store_job_from_text
def test_store_job_from_text_returns_existing_job_if_url_exists(mock_db, sample_job):
    mock_db.query.return_value.filter.return_value.first.return_value = sample_job

    result = JobSearchUtils.store_job_from_text(
        db=mock_db,
        title="ML Engineer",
        company="Acme",
        description="Build ML models.",
        url="https://acme.com/jobs/mle",
    )

    assert result is sample_job
    mock_db.add.assert_not_called()


@patch("autoapply.ai.utils.JobSearchUtils.Embedder.embed_texts", return_value=[[0.1] * 384])
@patch("autoapply.ai.utils.JobSearchUtils.chunk_text", return_value=["chunk one"])
def test_store_job_from_text_creates_new_job(mock_chunk, mock_embed, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    JobSearchUtils.store_job_from_text(
        db=mock_db,
        title="ML Engineer",
        company="Acme",
        description="Build ML models.",
        url="https://acme.com/jobs/new",
    )

    mock_db.add.assert_called()
    mock_db.commit.assert_called_once()
