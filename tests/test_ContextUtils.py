import uuid
from unittest.mock import patch

import pytest

from autoapply.ai.utils.ContextUtils import ContextUtils
from tests.conftest import JOB_ID, USER_ID


# get_fit_context
@patch("autoapply.ai.utils.ContextUtils.Embedder.embed_text", return_value=[0.1] * 384)
def test_get_fit_context_returns_expected_keys(mock_embed, mock_db, sample_job, sample_resume):
    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        return sample_job if call_count == 1 else sample_resume

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect
    mock_db.execute.return_value.fetchall.return_value = []

    result = ContextUtils.get_fit_context(db=mock_db, user_id=USER_ID, job_id=JOB_ID)

    assert "job_id" in result
    assert "job_title" in result
    assert "company" in result
    assert "job_description" in result
    assert "resume_excerpts" in result


@patch("autoapply.ai.utils.ContextUtils.Embedder.embed_text", return_value=[0.1] * 384)
def test_get_fit_context_uses_raw_text_when_no_chunks(mock_embed, mock_db, sample_job, sample_resume):
    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        return sample_job if call_count == 1 else sample_resume

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect
    mock_db.execute.return_value.fetchall.return_value = []

    result = ContextUtils.get_fit_context(db=mock_db, user_id=USER_ID, job_id=JOB_ID)

    assert sample_resume.raw_text[:3000] in result["resume_excerpts"]


def test_get_fit_context_raises_when_job_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="not found"):
        ContextUtils.get_fit_context(db=mock_db, user_id=USER_ID, job_id=uuid.uuid4())


def test_get_fit_context_raises_when_resume_not_found(mock_db, sample_job):
    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        return sample_job if call_count == 1 else None

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

    with pytest.raises(ValueError, match="No resume found"):
        ContextUtils.get_fit_context(db=mock_db, user_id=USER_ID, job_id=JOB_ID)


# get_cover_letter_context
@patch("autoapply.ai.utils.ContextUtils.Embedder.embed_text", return_value=[0.1] * 384)
def test_get_cover_letter_context_includes_past_letters(mock_embed, mock_db, sample_job, sample_resume):
    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        return sample_job if call_count == 1 else sample_resume

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect
    mock_db.execute.return_value.fetchall.return_value = []

    result = ContextUtils.get_cover_letter_context(db=mock_db, user_id=USER_ID, job_id=JOB_ID)

    assert "past_approved_letters" in result
    assert "fit_score" in result
    assert "fit_reasoning" in result
