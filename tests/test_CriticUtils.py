from unittest.mock import MagicMock, call, patch

import pytest

from autoapply.ai.utils.CriticUtils import CriticUtils
from tests.conftest import APPLICATION_ID, JOB_ID, USER_ID


# critique_and_revise
@patch("autoapply.ai.utils.CriticUtils.ChatGroq")
def test_critique_and_revise_approve_on_first_attempt(mock_groq, mock_db, sample_application, sample_cover_letter, sample_job):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = (
        '{"verdict": "APPROVE", "feedback": "Great letter.", "revised_text": null}'
    )
    mock_groq.return_value = mock_llm

    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_application
        if call_count == 2:
            return sample_cover_letter
        return sample_job

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

    result = CriticUtils.critique_and_revise(db=mock_db, application_id=APPLICATION_ID)

    assert result["verdict"] == "APPROVE"
    assert result["attempts"] == 1
    mock_llm.invoke.assert_called_once()


@patch("autoapply.ai.utils.CriticUtils.ChatGroq")
def test_critique_and_revise_revise_then_approve(mock_groq, mock_db, sample_application, sample_cover_letter, sample_job):
    mock_llm = MagicMock()
    revise_response = MagicMock()
    revise_response.content = (
        '{"verdict": "REVISE", "feedback": "Add company name.", "revised_text": "Revised letter."}'
    )
    approve_response = MagicMock()
    approve_response.content = (
        '{"verdict": "APPROVE", "feedback": "Perfect now.", "revised_text": null}'
    )
    mock_llm.invoke.side_effect = [revise_response, approve_response]
    mock_groq.return_value = mock_llm

    fetch_count = 0

    def first_side_effect():
        nonlocal fetch_count
        fetch_count += 1
        if fetch_count == 1:
            return sample_application
        if fetch_count == 2:
            return sample_cover_letter
        if fetch_count == 3:
            return sample_job
        return None

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

    result = CriticUtils.critique_and_revise(db=mock_db, application_id=APPLICATION_ID)

    assert result["verdict"] == "APPROVE"
    assert result["attempts"] == 2
    assert mock_llm.invoke.call_count == 2


@patch("autoapply.ai.utils.CriticUtils.ChatGroq")
def test_critique_and_revise_raises_when_application_not_found(mock_groq, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="not found"):
        CriticUtils.critique_and_revise(db=mock_db, application_id=APPLICATION_ID)


@patch("autoapply.ai.utils.CriticUtils.ChatGroq")
def test_critique_and_revise_raises_when_cover_letter_missing(mock_groq, mock_db, sample_application):
    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_application
        return None

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

    with pytest.raises(ValueError, match="[Cc]over [Ll]etter"):
        CriticUtils.critique_and_revise(db=mock_db, application_id=APPLICATION_ID)


@patch("autoapply.ai.utils.CriticUtils.ChatGroq")
def test_critique_and_revise_stops_after_max_revisions(mock_groq, mock_db, sample_application, sample_cover_letter, sample_job):
    mock_llm = MagicMock()
    revise_response = MagicMock()
    revise_response.content = (
        '{"verdict": "REVISE", "feedback": "Needs work.", "revised_text": "New draft."}'
    )
    mock_llm.invoke.return_value = revise_response
    mock_groq.return_value = mock_llm

    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_application
        if call_count % 2 == 0:
            return sample_cover_letter
        return sample_job

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

    result = CriticUtils.critique_and_revise(db=mock_db, application_id=APPLICATION_ID)

    assert result["attempts"] >= 1
    assert result["verdict"] == "REVISE"
