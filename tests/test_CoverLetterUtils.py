from unittest.mock import MagicMock, patch

from autoapply.ai.utils.CoverLetterUtils import CoverLetterUtils
from tests.conftest import JOB_ID, USER_ID


# clean_cover_letter
def test_clean_cover_letter_removes_em_dash():
    result = CoverLetterUtils.clean_cover_letter("I led the team — and delivered results.")
    assert "—" not in result


def test_clean_cover_letter_removes_sentence_hyphen():
    result = CoverLetterUtils.clean_cover_letter("I led the team - and delivered results.")
    assert " - " not in result


def test_clean_cover_letter_removes_leading_bullets():
    text = "• First point\n• Second point"
    result = CoverLetterUtils.clean_cover_letter(text)
    assert "•" not in result


def test_clean_cover_letter_collapses_double_commas():
    result = CoverLetterUtils.clean_cover_letter("good, , great")
    assert ", ," not in result


def test_clean_cover_letter_strips_whitespace():
    result = CoverLetterUtils.clean_cover_letter("  hello world  ")
    assert result == "hello world"


def test_clean_cover_letter_preserves_compound_adjectives():
    text = "I built a production-ready full-stack system."
    result = CoverLetterUtils.clean_cover_letter(text)
    assert "production-ready" in result
    assert "full-stack" in result


# generate_cover_letter
@patch("autoapply.ai.utils.CoverLetterUtils.Embedder.embed_text", return_value=[0.1] * 384)
@patch("autoapply.ai.utils.CoverLetterUtils.ChatGroq")
def test_generate_cover_letter_creates_application_and_cover_letter(
    mock_groq, mock_embed, mock_db, sample_job, sample_resume
):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "I am writing to apply for the ML Engineer role at Acme Corp."
    mock_groq.return_value = mock_llm

    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_job
        if call_count == 2:
            return sample_resume
        return None

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect
    mock_db.execute.return_value.fetchall.return_value = []

    CoverLetterUtils.generate_cover_letter(db=mock_db, user_id=USER_ID, job_id=JOB_ID)

    mock_db.add.assert_called()
    mock_db.commit.assert_called_once()
    mock_llm.invoke.assert_called_once()


@patch("autoapply.ai.utils.CoverLetterUtils.Embedder.embed_text", return_value=[0.1] * 384)
@patch("autoapply.ai.utils.CoverLetterUtils.ChatGroq")
def test_generate_cover_letter_applies_clean_post_processing(
    mock_groq, mock_embed, mock_db, sample_job, sample_resume
):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "I led the team — and delivered results."
    mock_groq.return_value = mock_llm

    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return sample_job
        if call_count == 2:
            return sample_resume
        return None

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect
    mock_db.execute.return_value.fetchall.return_value = []

    CoverLetterUtils.generate_cover_letter(db=mock_db, user_id=USER_ID, job_id=JOB_ID)

    added_cover_letter = mock_db.add.call_args_list[-1][0][0]
    assert "—" not in (added_cover_letter.draft_text or "")
