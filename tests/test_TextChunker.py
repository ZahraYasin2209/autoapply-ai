from unittest.mock import patch

from autoapply.ai.utils.TextChunker import chunk_text

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


@patch("autoapply.ai.utils.TextChunker.CHUNK_SIZE", CHUNK_SIZE)
@patch("autoapply.ai.utils.TextChunker.CHUNK_OVERLAP", CHUNK_OVERLAP)
def test_empty_string_returns_empty_list():
    assert chunk_text("") == []


@patch("autoapply.ai.utils.TextChunker.CHUNK_SIZE", CHUNK_SIZE)
@patch("autoapply.ai.utils.TextChunker.CHUNK_OVERLAP", CHUNK_OVERLAP)
def test_whitespace_only_returns_empty_list():
    assert chunk_text("   \n\t  ") == []


@patch("autoapply.ai.utils.TextChunker.CHUNK_SIZE", CHUNK_SIZE)
@patch("autoapply.ai.utils.TextChunker.CHUNK_OVERLAP", CHUNK_OVERLAP)
def test_short_text_returns_single_chunk():
    text = "Short text."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


@patch("autoapply.ai.utils.TextChunker.CHUNK_SIZE", CHUNK_SIZE)
@patch("autoapply.ai.utils.TextChunker.CHUNK_OVERLAP", CHUNK_OVERLAP)
def test_long_text_produces_multiple_chunks():
    text = "A" * 1200
    chunks = chunk_text(text)
    assert len(chunks) > 1


@patch("autoapply.ai.utils.TextChunker.CHUNK_SIZE", CHUNK_SIZE)
@patch("autoapply.ai.utils.TextChunker.CHUNK_OVERLAP", CHUNK_OVERLAP)
def test_chunks_overlap_correctly():
    text = "A" * 1200
    chunks = chunk_text(text)
    step = CHUNK_SIZE - CHUNK_OVERLAP
    assert chunks[1] == text[step: step + CHUNK_SIZE]


@patch("autoapply.ai.utils.TextChunker.CHUNK_SIZE", CHUNK_SIZE)
@patch("autoapply.ai.utils.TextChunker.CHUNK_OVERLAP", CHUNK_OVERLAP)
def test_all_text_is_covered():
    text = "B" * 900
    chunks = chunk_text(text)
    assert chunks[0].startswith("B")
    assert "".join(chunks[0]) == text[:CHUNK_SIZE]
