import json
import uuid

from langchain_groq import ChatGroq
from sqlalchemy import text
from sqlalchemy.orm import Session

from config.settings.base import GROQ_API_KEY, MEMORY_TOP_K
from autoapply.models.Job import Job
from autoapply.models.Resume import Resume
from autoapply.ai.utils.Embedder import Embedder
from autoapply.ai.prompts import FIT_PROMPT


class FitScorerUtils:
    @staticmethod
    def _get_top_resume_chunks(db: Session, resume_id: uuid.UUID, job_description: str, top_k: int) -> list[str]:
        """Retrieve top-k resume chunks most similar to the job description."""
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
    def score_job_fit(db: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> Job:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        resume = db.query(Resume).filter(Resume.user_id == user_id).first()
        if not resume:
            raise ValueError(f"No resume found for user {user_id}.")

        relevant_resume_chunks = FitScorerUtils._get_top_resume_chunks(
            db, resume.id, job.description or job.title, top_k=MEMORY_TOP_K
        )
        resume_excerpts = "\n---\n".join(relevant_resume_chunks) if relevant_resume_chunks else (resume.raw_text or "")[:3000]

        fit_scoring_llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0)
        fit_scoring_prompt = FIT_PROMPT.format(
            title=job.title,
            company=job.company,
            description=(job.description or "")[:3000],
            resume_excerpts=resume_excerpts,
        )

        llm_response = fit_scoring_llm.invoke(fit_scoring_prompt)
        response_content = llm_response.content.strip()

        if "```" in response_content:
            response_content = response_content.split("```")[1]
            if response_content.startswith("json"):
                response_content = response_content[4:]

        fit_scoring_result = json.loads(response_content)

        job.fit_score = float(fit_scoring_result["fit_score"])
        job.recommendation = fit_scoring_result["recommendation"]
        job.fit_reasoning = fit_scoring_result["reasoning"]
        db.commit()
        db.refresh(job)

        return job
