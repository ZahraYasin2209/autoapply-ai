import re
import uuid
from datetime import datetime, timezone

from langchain_groq import ChatGroq
from sqlalchemy import text
from sqlalchemy.orm import Session

from config.settings.base import GROQ_API_KEY, MEMORY_TOP_K
from autoapply.models.Application import Application
from autoapply.models.CoverLetter import CoverLetter
from autoapply.models.Job import Job
from autoapply.models.Resume import Resume
from autoapply.ai.utils.Embedder import Embedder
from autoapply.ai.prompts import COVER_LETTER_PROMPT


class CoverLetterUtils:
    @staticmethod
    def clean_cover_letter(raw_text: str) -> str:
        """Deterministic post-processing: remove em dashes used as dashes, strip leading bullets."""
        raw_text = re.sub(r"\s*—\s*", ", ", raw_text)
        raw_text = re.sub(r" - ", ", ", raw_text)
        raw_text = re.sub(r",\s*,", ",", raw_text)
        raw_text = re.sub(r"^[\s]*[•\-\*]\s+", "", raw_text, flags=re.MULTILINE)

        return raw_text.strip()

    @staticmethod
    def _get_top_resume_chunks(db: Session, resume_id: uuid.UUID, job_description: str, top_k: int) -> list[str]:
        query_embedding = Embedder.embed_text(job_description[:2000])
        embedding_vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        similar_chunks = db.execute(
            text("""
                SELECT chunk_text
                FROM resume_chunks
                WHERE resume_id = :resume_id
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """),
            {"resume_id": str(resume_id), "embedding": embedding_vector_str, "top_k": top_k},
        ).fetchall()

        return [row[0] for row in similar_chunks]

    @staticmethod
    def generate_cover_letter(db: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> tuple[Application, CoverLetter]:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        resume = db.query(Resume).filter(Resume.user_id == user_id).first()
        if not resume:
            raise ValueError(f"No resume found for user {user_id}.")

        application = db.query(Application).filter(
            Application.user_id == user_id,
            Application.job_id == job_id,
        ).first()

        if not application:
            application = Application(user_id=user_id, job_id=job_id, status="draft")
            db.add(application)
            db.flush()

        relevant_resume_chunks = CoverLetterUtils._get_top_resume_chunks(
            db, resume.id, job.description or job.title, top_k=MEMORY_TOP_K
        )
        resume_excerpts = "\n---\n".join(relevant_resume_chunks) if relevant_resume_chunks else (resume.raw_text or "")[:3000]

        cover_letter_llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.7)
        cover_letter_prompt = COVER_LETTER_PROMPT.format(
            title=job.title,
            company=job.company,
            description=(job.description or "")[:3000],
            resume_excerpts=resume_excerpts,
            fit_score=job.fit_score or "N/A",
            fit_reasoning=job.fit_reasoning or "N/A",
        )

        llm_response = cover_letter_llm.invoke(cover_letter_prompt)
        draft_text = CoverLetterUtils.clean_cover_letter(llm_response.content.strip())

        cover_letter = db.query(CoverLetter).filter(
            CoverLetter.application_id == application.id
        ).first()

        if cover_letter:
            cover_letter.draft_text = draft_text
            cover_letter.resume_bullets = resume_excerpts
            cover_letter.revision_count += 1
            cover_letter.critic_approved = False
            cover_letter.generated_at = datetime.now(timezone.utc)
        else:
            cover_letter = CoverLetter(
                application_id=application.id,
                draft_text=draft_text,
                resume_bullets=resume_excerpts,
                revision_count=0,
                critic_approved=False,
                generated_at=datetime.now(timezone.utc),
            )
            db.add(cover_letter)

        db.commit()
        db.refresh(application)
        db.refresh(cover_letter)

        return application, cover_letter
