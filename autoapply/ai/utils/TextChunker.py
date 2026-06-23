from config.settings.base import CHUNK_OVERLAP, CHUNK_SIZE


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks by character count."""
    text = text.strip()
    if not text:
        return []

    text_chunks = []
    chunk_start = 0
    while chunk_start < len(text):
        chunk_end = chunk_start + CHUNK_SIZE
        text_chunks.append(text[chunk_start:chunk_end])
        chunk_start += CHUNK_SIZE - CHUNK_OVERLAP

    return text_chunks
