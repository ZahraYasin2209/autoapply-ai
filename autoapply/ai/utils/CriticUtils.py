import json
import uuid
from datetime import datetime, timezone

from langchain_groq import ChatGroq
from sqlalchemy.orm import Session

from config.settings.base import CRITIC_MAX_REVISIONS, GROQ_API_KEY
from autoapply.models.Application import Application
from autoapply.models.CoverLetter import CoverLetter
from autoapply.models.CriticReview import CriticReview
from autoapply.models.Job import Job
from autoapply.ai.utils.CoverLetterUtils import CoverLetterUtils
from autoapply.ai.utils.MemoryUtils import MemoryUtils
from autoapply.ai.prompts import CRITIC_PROMPT, REVISION_PROMPT


class CriticUtils:

    @staticmethod
    def _run_critic(critic_llm: ChatGroq, job: Job, draft_text: str) -> tuple[str, str]:
        """Returns (verdict, feedback)."""
        critic_prompt = CRITIC_PROMPT.format(
            title=job.title,
            company=job.company,
            cover_letter=draft_text,
        )
        llm_response = critic_llm.invoke(critic_prompt)
        response_content = llm_response.content.strip()

        if "```" in response_content:
            response_content = response_content.split("```")[1]
            if response_content.startswith("json"):
                response_content = response_content[4:]

        critic_result = json.loads(response_content)

        return critic_result["verdict"], critic_result["feedback"]

    @staticmethod
    def _run_revision(critic_llm: ChatGroq, job: Job, draft_text: str, feedback: str) -> str:
        """Returns revised cover letter text."""
        revision_prompt = REVISION_PROMPT.format(
            title=job.title,
            company=job.company,
            description=(job.description or "")[:3000],
            cover_letter=draft_text,
            feedback=feedback,
        )
        llm_response = critic_llm.invoke(revision_prompt)

        return CoverLetterUtils.clean_cover_letter(llm_response.content.strip())

    @staticmethod
    def critique_and_revise(db: Session, application_id: uuid.UUID) -> dict:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise ValueError(f"Application {application_id} not found.")

        cover_letter = db.query(CoverLetter).filter(
            CoverLetter.application_id == application_id
        ).first()
        if not cover_letter or not cover_letter.draft_text:
            raise ValueError("No cover letter draft found. Generate one first.")

        job = db.query(Job).filter(Job.id == application.job_id).first()
        critic_llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.3)

        current_draft = cover_letter.draft_text
        revision_attempt = 0
        verdict = "REVISE"
        feedback = ""

        while revision_attempt < CRITIC_MAX_REVISIONS and verdict == "REVISE":
            revision_attempt += 1
            verdict, feedback = CriticUtils._run_critic(critic_llm, job, current_draft)

            critic_review = CriticReview(
                application_id=application_id,
                verdict=verdict,
                feedback_text=feedback,
                attempt_number=revision_attempt,
                reviewed_at=datetime.now(timezone.utc),
            )
            db.add(critic_review)
            db.flush()

            if verdict == "APPROVE":
                break

            if revision_attempt < CRITIC_MAX_REVISIONS:
                current_draft = CriticUtils._run_revision(critic_llm, job, current_draft, feedback)
                cover_letter.draft_text = current_draft
                cover_letter.revision_count = revision_attempt

        cover_letter.final_text = current_draft
        cover_letter.critic_approved = verdict == "APPROVE"
        cover_letter.revision_count = revision_attempt

        if verdict == "APPROVE":
            application.status = "ready"
        else:
            application.status = "needs_review"

        db.commit()
        db.refresh(cover_letter)
        db.refresh(application)

        if verdict == "APPROVE":
            MemoryUtils.store_approved_cover_letter(db, application_id)

        return {
            "application_id": str(application_id),
            "verdict": verdict,
            "attempts": revision_attempt,
            "critic_approved": cover_letter.critic_approved,
            "final_text": cover_letter.final_text,
            "last_feedback": feedback,
            "status": application.status,
        }
