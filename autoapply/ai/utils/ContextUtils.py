"""
Context utils — fetches data for Claude Desktop to reason over.
"""

import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from config.settings.base import MEMORY_TOP_K
from autoapply.models.Job import Job
from autoapply.models.Resume import Resume
from autoapply.ai.utils.Embedder import Embedder


class ContextUtils:
    @staticmethod
    def get_fit_context(db: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> dict:
        """Return resume excerpts + job details for Claude to score fit."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        resume = db.query(Resume).filter(Resume.user_id == user_id).first()
        if not resume:
            raise ValueError(f"No resume found for user {user_id}.")

        relevant_resume_chunks = ContextUtils._get_top_resume_chunks(
            db, resume.id, job.description or job.title
        )

        resume_excerpts = "\n---\n".join(relevant_resume_chunks) \
            if relevant_resume_chunks \
            else (resume.raw_text or "")[:3000]

        return {
            "job_id": str(job.id),
            "job_title": job.title,
            "company": job.company,
            "job_description": (job.description or "")[:3000],
            "resume_excerpts": resume_excerpts,
        }

    @staticmethod
    def get_cover_letter_context(db: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> dict:
        """Return resume excerpts + job details + past memory for Claude to write a cover letter."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        resume = db.query(Resume).filter(Resume.user_id == user_id).first()
        if not resume:
            raise ValueError(f"No resume found for user {user_id}.")

        relevant_resume_chunks = ContextUtils._get_top_resume_chunks(
            db, resume.id, job.description or job.title
        )

        resume_excerpts = "\n---\n".join(relevant_resume_chunks) \
            if relevant_resume_chunks \
            else (resume.raw_text or "")[:3000]

        past_approved_letters = ContextUtils._get_past_memory(db, user_id, job.title)

        return {
            "job_id": str(job.id),
            "job_title": job.title,
            "company": job.company,
            "job_description": (job.description or "")[:3000],
            "resume_excerpts": resume_excerpts,
            "fit_score": job.fit_score,
            "fit_reasoning": job.fit_reasoning,
            "past_approved_letters": past_approved_letters,
        }

    @staticmethod
    def _get_top_resume_chunks(db: Session, resume_id: uuid.UUID, query: str) -> list[str]:
        query_embedding = Embedder.embed_text(query[:2000])
        embedding_vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        similar_chunk_rows = db.execute(
            text("""
                SELECT chunk_text
                FROM resume_chunks
                WHERE resume_id = :resume_id
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """),
            {"resume_id": str(resume_id), "embedding": embedding_vector_str, "top_k": MEMORY_TOP_K},
        ).fetchall()

        return [row[0] for row in similar_chunk_rows]

    @staticmethod
    def _get_past_memory(db: Session, user_id: uuid.UUID, query: str) -> list[str]:
        query_embedding = Embedder.embed_text(query[:2000])
        embedding_vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        approved_letter_rows = db.execute(
            text("""
                SELECT content
                FROM memory_entries
                WHERE user_id = :user_id AND entry_type = 'approved_cover_letter'
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT 2
            """),
            {"user_id": str(user_id), "embedding": embedding_vector_str},
        ).fetchall()

        return [row[0] for row in approved_letter_rows]
