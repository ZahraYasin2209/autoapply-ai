import uuid
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy.orm import Session

from config.settings.base import UPLOAD_DIR
from autoapply.models.Resume import Resume
from autoapply.models.ResumeChunk import ResumeChunk
from autoapply.ai.utils.TextChunker import chunk_text
from autoapply.ai.utils.Embedder import Embedder


class ResumeUtils:
    @staticmethod
    def extract_text_from_pdf(file_path: Path) -> str:
        pdf_reader = PdfReader(str(file_path))
        page_texts = [page.extract_text() or "" for page in pdf_reader.pages]

        return "\n".join(page_texts).strip()

    @staticmethod
    def ingest_resume(db: Session, user_id: uuid.UUID, file_bytes: bytes, filename: str) -> Resume:
        file_destination = UPLOAD_DIR / str(user_id) / filename
        file_destination.parent.mkdir(parents=True, exist_ok=True)
        file_destination.write_bytes(file_bytes)

        raw_text = ResumeUtils.extract_text_from_pdf(file_destination)

        resume = db.query(Resume).filter(Resume.user_id == user_id).first()
        if resume:
            db.query(ResumeChunk).filter(ResumeChunk.resume_id == resume.id).delete()
            resume.file_path = str(file_destination)
            resume.raw_text = raw_text
        else:
            resume = Resume(user_id=user_id, file_path=str(file_destination), raw_text=raw_text)
            db.add(resume)
            db.flush()

        text_chunks = chunk_text(raw_text)
        chunk_embeddings = Embedder.embed_texts(text_chunks)

        for chunk_index, (chunk_text_content, chunk_embedding) in enumerate(zip(text_chunks, chunk_embeddings)):
            db.add(ResumeChunk(
                resume_id=resume.id,
                chunk_text=chunk_text_content,
                embedding=chunk_embedding,
                chunk_index=chunk_index,
            ))

        db.commit()
        db.refresh(resume)
        return resume

    @staticmethod
    def ingest_resume_from_text(db: Session, user_id: uuid.UUID, raw_text: str) -> Resume:
        """Ingest resume from raw text — used when Claude Desktop passes resume content directly."""
        resume = db.query(Resume).filter(Resume.user_id == user_id).first()
        if resume:
            db.query(ResumeChunk).filter(ResumeChunk.resume_id == resume.id).delete()
            resume.raw_text = raw_text
        else:
            resume = Resume(user_id=user_id, raw_text=raw_text)
            db.add(resume)
            db.flush()

        text_chunks = chunk_text(raw_text)
        chunk_embeddings = Embedder.embed_texts(text_chunks)

        for chunk_index, (chunk_text_content, chunk_embedding) in enumerate(zip(text_chunks, chunk_embeddings)):
            db.add(ResumeChunk(
                resume_id=resume.id,
                chunk_text=chunk_text_content,
                embedding=chunk_embedding,
                chunk_index=chunk_index,
            ))

        db.commit()
        db.refresh(resume)
        return resume
