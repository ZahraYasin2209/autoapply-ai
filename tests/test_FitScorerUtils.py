from unittest.mock import MagicMock, patch

import pytest

from autoapply.ai.utils.FitScorerUtils import FitScorerUtils
from tests.conftest import JOB_ID, USER_ID


@patch("autoapply.ai.utils.FitScorerUtils.Embedder.embed_text", return_value=[0.1] * 384)
@patch("autoapply.ai.utils.FitScorerUtils.ChatGroq")
def test_score_job_fit_returns_score_and_recommendation(mock_groq, mock_embed, mock_db, sample_job, sample_resume):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = '{"fit_score": 82, "recommendation": "apply", "reasoning": "Strong match."}'
    mock_groq.return_value = mock_llm

    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_job
        return sample_resume

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect
    mock_db.execute.return_value.fetchall.return_value = []

    result = FitScorerUtils.score_job_fit(db=mock_db, user_id=USER_ID, job_id=JOB_ID)

    assert result.fit_score == 82.0
    assert result.recommendation == "apply"
    assert result.fit_reasoning == "Strong match."
    mock_llm.invoke.assert_called_once()


@patch("autoapply.ai.utils.FitScorerUtils.Embedder.embed_text", return_value=[0.1] * 384)
@patch("autoapply.ai.utils.FitScorerUtils.ChatGroq")
def test_score_job_fit_raises_when_job_not_found(mock_groq, mock_embed, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="not found"):
        FitScorerUtils.score_job_fit(db=mock_db, user_id=USER_ID, job_id=JOB_ID)


@patch("autoapply.ai.utils.FitScorerUtils.Embedder.embed_text", return_value=[0.1] * 384)
@patch("autoapply.ai.utils.FitScorerUtils.ChatGroq")
def test_score_job_fit_raises_when_resume_not_found(mock_groq, mock_embed, mock_db, sample_job):
    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_job
        return None

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

    with pytest.raises(ValueError, match="No resume"):
        FitScorerUtils.score_job_fit(db=mock_db, user_id=USER_ID, job_id=JOB_ID)


@patch("autoapply.ai.utils.FitScorerUtils.Embedder.embed_text", return_value=[0.1] * 384)
@patch("autoapply.ai.utils.FitScorerUtils.ChatGroq")
def test_score_job_fit_handles_malformed_json_gracefully(mock_groq, mock_embed, mock_db, sample_job, sample_resume):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "not valid json at all"
    mock_groq.return_value = mock_llm

    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_job
        return sample_resume

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect
    mock_db.execute.return_value.fetchall.return_value = []

    with pytest.raises(Exception):
        FitScorerUtils.score_job_fit(db=mock_db, user_id=USER_ID, job_id=JOB_ID)
