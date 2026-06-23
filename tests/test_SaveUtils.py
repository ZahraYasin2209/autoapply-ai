import uuid
from unittest.mock import MagicMock, patch

import pytest

from autoapply.ai.utils.SaveUtils import SaveUtils
from autoapply.models.Application import Application
from autoapply.models.CoverLetter import CoverLetter
from autoapply.models.Job import Job
from tests.conftest import APPLICATION_ID, JOB_ID, USER_ID


# save_fit_score
def test_save_fit_score_updates_job(mock_db, sample_job):
    mock_db.query.return_value.filter.return_value.first.return_value = sample_job

    result = SaveUtils.save_fit_score(
        db=mock_db,
        job_id=JOB_ID,
        fit_score=85.0,
        recommendation="apply",
        reasoning="Strong match.",
    )

    assert result.fit_score == 85.0
    assert result.recommendation == "APPLY"
    assert result.fit_reasoning == "Strong match."
    mock_db.commit.assert_called_once()


def test_save_fit_score_raises_when_job_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="not found"):
        SaveUtils.save_fit_score(
            db=mock_db, job_id=uuid.uuid4(), fit_score=80.0,
            recommendation="apply", reasoning="Good fit."
        )


# save_cover_letter
def test_save_cover_letter_creates_application_when_missing(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    SaveUtils.save_cover_letter(
        db=mock_db,
        user_id=USER_ID,
        job_id=JOB_ID,
        cover_letter_text="Dear Acme Corp...",
    )

    mock_db.add.assert_called()
    mock_db.commit.assert_called_once()


def test_save_cover_letter_updates_existing_cover_letter(mock_db, sample_application, sample_cover_letter):
    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_application
        return sample_cover_letter

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

    SaveUtils.save_cover_letter(
        db=mock_db,
        user_id=USER_ID,
        job_id=JOB_ID,
        cover_letter_text="Updated letter.",
    )

    assert sample_cover_letter.draft_text == "Updated letter."
    assert sample_cover_letter.critic_approved is False


# save_critic_review
@patch("autoapply.ai.utils.SaveUtils.MemoryUtils.store_memory")
def test_save_critic_review_approve_finalizes_letter(mock_store_memory, mock_db, sample_application, sample_cover_letter, sample_job):
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
    mock_db.query.return_value.filter.return_value.scalar.return_value = 0

    result = SaveUtils.save_critic_review(
        db=mock_db,
        application_id=APPLICATION_ID,
        verdict="APPROVE",
        feedback="Looks great.",
    )

    assert result["verdict"] == "APPROVE"
    assert result["critic_approved"] is True
    assert sample_application.status == "ready"
    mock_store_memory.assert_called_once()


def test_save_critic_review_revise_updates_draft(mock_db, sample_application, sample_cover_letter):
    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_application
        return sample_cover_letter

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect
    mock_db.query.return_value.filter.return_value.scalar.return_value = 0

    result = SaveUtils.save_critic_review(
        db=mock_db,
        application_id=APPLICATION_ID,
        verdict="REVISE",
        feedback="Missing company name.",
        revised_text="Revised letter text.",
    )

    assert result["verdict"] == "REVISE"
    assert sample_cover_letter.draft_text == "Revised letter text."
    assert sample_application.status == "needs_review"


def test_save_critic_review_raises_when_application_not_found(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="not found"):
        SaveUtils.save_critic_review(
            db=mock_db,
            application_id=uuid.uuid4(),
            verdict="APPROVE",
            feedback="Good.",
        )
