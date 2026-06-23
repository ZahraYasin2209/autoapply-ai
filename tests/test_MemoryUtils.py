import uuid
from unittest.mock import MagicMock, patch

import pytest

from autoapply.ai.utils.MemoryUtils import MemoryUtils
from autoapply.models.MemoryEntry import MemoryEntry
from tests.conftest import APPLICATION_ID, USER_ID


# store_memory
@patch("autoapply.ai.utils.MemoryUtils.Embedder.embed_text", return_value=[0.1] * 384)
def test_store_memory_creates_entry(mock_embed, mock_db):
    result = MemoryUtils.store_memory(
        db=mock_db,
        user_id=USER_ID,
        entry_type="approved_cover_letter",
        content="Great cover letter.",
        source_outcome="approved",
    )

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_embed.assert_called_once_with("Great cover letter.")


@patch("autoapply.ai.utils.MemoryUtils.Embedder.embed_text", return_value=[0.1] * 384)
def test_store_memory_without_source_outcome(mock_embed, mock_db):
    MemoryUtils.store_memory(
        db=mock_db,
        user_id=USER_ID,
        entry_type="general",
        content="Some memory.",
    )

    mock_db.add.assert_called_once()


# retrieve_memory
@patch("autoapply.ai.utils.MemoryUtils.Embedder.embed_text", return_value=[0.1] * 384)
def test_retrieve_memory_queries_db(mock_embed, mock_db):
    mock_row = (uuid.uuid4(), "approved_cover_letter", "content text", "approved", None)
    mock_db.execute.return_value.fetchall.return_value = [mock_row]

    results = MemoryUtils.retrieve_memory(
        db=mock_db,
        user_id=USER_ID,
        query="machine learning engineer",
    )

    assert len(results) == 1
    assert isinstance(results[0], MemoryEntry)
    assert results[0].content == "content text"


@patch("autoapply.ai.utils.MemoryUtils.Embedder.embed_text", return_value=[0.1] * 384)
def test_retrieve_memory_with_entry_type_filter(mock_embed, mock_db):
    mock_db.execute.return_value.fetchall.return_value = []

    results = MemoryUtils.retrieve_memory(
        db=mock_db,
        user_id=USER_ID,
        query="some query",
        entry_type="approved_cover_letter",
    )

    assert results == []
    call_args = mock_db.execute.call_args
    assert "entry_type" in call_args[0][1]


# store_approved_cover_letter
def test_store_approved_cover_letter_returns_none_when_application_missing(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = MemoryUtils.store_approved_cover_letter(db=mock_db, application_id=APPLICATION_ID)

    assert result is None


def test_store_approved_cover_letter_returns_none_when_not_approved(mock_db, sample_application, sample_cover_letter):
    sample_cover_letter.critic_approved = False
    call_count = 0

    def first_side_effect():
        nonlocal call_count
        call_count += 1
        return sample_application if call_count == 1 else sample_cover_letter

    mock_db.query.return_value.filter.return_value.first.side_effect = first_side_effect

    result = MemoryUtils.store_approved_cover_letter(db=mock_db, application_id=APPLICATION_ID)

    assert result is None
