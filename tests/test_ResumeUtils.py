from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from autoapply.ai.utils.ResumeUtils import ResumeUtils
from tests.conftest import USER_ID


# ── extract_text_from_pdf ─────────────────────────────────────────────────────

@patch("autoapply.ai.utils.ResumeUtils.PdfReader")
def test_extract_text_from_pdf_joins_pages(mock_pdf_reader):
    page1 = MagicMock()
    page1.extract_text.return_value = "Page one content."
    page2 = MagicMock()
    page2.extract_text.return_value = "Page two content."
    mock_pdf_reader.return_value.pages = [page1, page2]

    result = ResumeUtils.extract_text_from_pdf(Path("/fake/resume.pdf"))

    assert "Page one content." in result
    assert "Page two content." in result


@patch("autoapply.ai.utils.ResumeUtils.PdfReader")
def test_extract_text_from_pdf_skips_none_pages(mock_pdf_reader):
    page1 = MagicMock()
    page1.extract_text.return_value = None
    page2 = MagicMock()
    page2.extract_text.return_value = "Valid text."
    mock_pdf_reader.return_value.pages = [page1, page2]

    result = ResumeUtils.extract_text_from_pdf(Path("/fake/resume.pdf"))

    assert "Valid text." in result


# ── ingest_resume ─────────────────────────────────────────────────────────────

@patch("autoapply.ai.utils.ResumeUtils.Embedder.embed_texts", return_value=[[0.1] * 384])
@patch("autoapply.ai.utils.ResumeUtils.chunk_text", return_value=["chunk one"])
@patch("autoapply.ai.utils.ResumeUtils.ResumeUtils.extract_text_from_pdf", return_value="Resume text content.")
@patch("autoapply.ai.utils.ResumeUtils.Path.mkdir")
@patch("autoapply.ai.utils.ResumeUtils.Path.write_bytes")
def test_ingest_resume_saves_chunks(mock_write, mock_mkdir, mock_extract, mock_chunk, mock_embed, mock_db, sample_resume):
    mock_db.query.return_value.filter.return_value.first.return_value = sample_resume

    ResumeUtils.ingest_resume(db=mock_db, user_id=USER_ID, file_bytes=b"fake pdf", filename="resume.pdf")

    mock_db.add.assert_called()
    mock_db.commit.assert_called()


@patch("autoapply.ai.utils.ResumeUtils.Embedder.embed_texts", return_value=[[0.1] * 384])
@patch("autoapply.ai.utils.ResumeUtils.chunk_text", return_value=["chunk one"])
@patch("autoapply.ai.utils.ResumeUtils.ResumeUtils.extract_text_from_pdf", return_value="New resume text.")
@patch("autoapply.ai.utils.ResumeUtils.Path.mkdir")
@patch("autoapply.ai.utils.ResumeUtils.Path.write_bytes")
def test_ingest_resume_creates_resume_record_when_missing(mock_write, mock_mkdir, mock_extract, mock_chunk, mock_embed, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    ResumeUtils.ingest_resume(db=mock_db, user_id=USER_ID, file_bytes=b"fake pdf", filename="cv.pdf")

    mock_db.add.assert_called()


# ── ingest_resume_from_text ───────────────────────────────────────────────────

@patch("autoapply.ai.utils.ResumeUtils.Embedder.embed_texts", return_value=[[0.1] * 384])
@patch("autoapply.ai.utils.ResumeUtils.chunk_text", return_value=["chunk one"])
def test_ingest_resume_from_text_stores_chunks(mock_chunk, mock_embed, mock_db, sample_resume):
    mock_db.query.return_value.filter.return_value.first.return_value = sample_resume

    ResumeUtils.ingest_resume_from_text(db=mock_db, user_id=USER_ID, raw_text="My resume text.")

    mock_db.add.assert_called()
    mock_db.commit.assert_called()


@patch("autoapply.ai.utils.ResumeUtils.Embedder.embed_texts", return_value=[[0.1] * 384])
@patch("autoapply.ai.utils.ResumeUtils.chunk_text", return_value=["chunk one"])
def test_ingest_resume_from_text_creates_resume_when_missing(mock_chunk, mock_embed, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    ResumeUtils.ingest_resume_from_text(db=mock_db, user_id=USER_ID, raw_text="My resume text.")

    mock_db.add.assert_called()
