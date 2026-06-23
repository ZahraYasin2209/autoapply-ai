"""
Save utils — persists Claude Desktop's outputs to the database.
Claude generates content; these methods store it.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from autoapply.models.Application import Application
from autoapply.models.CoverLetter import CoverLetter
from autoapply.models.CriticReview import CriticReview
from autoapply.models.Job import Job
from autoapply.ai.utils.MemoryUtils import MemoryUtils


class SaveUtils:
    @staticmethod
    def save_fit_score(
        db: Session,
        job_id: uuid.UUID,
        fit_score: float,
        recommendation: str,
        reasoning: str,
    ) -> Job:
        """Save Claude's fit scoring result onto the Job record."""
        scored_job = db.query(Job).filter(Job.id == job_id).first()
        if not scored_job:
            raise ValueError(f"Job {job_id} not found.")

        scored_job.fit_score = fit_score
        scored_job.recommendation = recommendation.upper()
        scored_job.fit_reasoning = reasoning
        db.commit()
        db.refresh(scored_job)

        return scored_job

    @staticmethod
    def save_cover_letter(
        db: Session,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        cover_letter_text: str,
    ) -> tuple[Application, CoverLetter]:
        """Save Claude's generated cover letter. Creates Application if needed."""
        application = db.query(Application).filter(
            Application.user_id == user_id,
            Application.job_id == job_id,
        ).first()

        if not application:
            application = Application(user_id=user_id, job_id=job_id, status="draft")
            db.add(application)
            db.flush()

        cover_letter = db.query(CoverLetter).filter(
            CoverLetter.application_id == application.id
        ).first()

        if cover_letter:
            cover_letter.draft_text = cover_letter_text
            cover_letter.revision_count += 1
            cover_letter.critic_approved = False
            cover_letter.generated_at = datetime.now(timezone.utc)
        else:
            cover_letter = CoverLetter(
                application_id=application.id,
                draft_text=cover_letter_text,
                revision_count=0,
                critic_approved=False,
                generated_at=datetime.now(timezone.utc),
            )
            db.add(cover_letter)

        db.commit()
        db.refresh(application)
        db.refresh(cover_letter)
        return application, cover_letter

    @staticmethod
    def save_critic_review(
        db: Session,
        application_id: uuid.UUID,
        verdict: str,
        feedback: str,
        revised_text: str | None = None,
    ) -> dict:
        """Save Claude's critic review. If APPROVE, finalizes and stores to memory."""
        from sqlalchemy import func

        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise ValueError(f"Application {application_id} not found.")

        cover_letter = db.query(CoverLetter).filter(
            CoverLetter.application_id == application_id
        ).first()
        if not cover_letter:
            raise ValueError("No cover letter found for this application.")

        attempt_number = db.query(func.count(CriticReview.id)).filter(
            CriticReview.application_id == application_id
        ).scalar() + 1

        critic_review = CriticReview(
            application_id=application_id,
            verdict=verdict.upper(),
            feedback_text=feedback,
            attempt_number=attempt_number,
            reviewed_at=datetime.now(timezone.utc),
        )
        db.add(critic_review)

        normalized_verdict = verdict.upper()

        if normalized_verdict == "APPROVE":
            cover_letter.final_text = revised_text or cover_letter.draft_text
            cover_letter.critic_approved = True
            application.status = "ready"

            approved_job = db.query(Job).filter(Job.id == application.job_id).first()
            memory_content = (
                f"Approved cover letter for {approved_job.title} at {approved_job.company}:\n\n{cover_letter.final_text}"
            )
            MemoryUtils.store_memory(
                db=db,
                user_id=application.user_id,
                entry_type="approved_cover_letter",
                content=memory_content,
                source_outcome="approved",
            )
        else:
            if revised_text:
                cover_letter.draft_text = revised_text
            cover_letter.revision_count = attempt_number
            application.status = "needs_review"

        db.commit()

        return {
            "application_id": str(application_id),
            "verdict": normalized_verdict,
            "attempt_number": attempt_number,
            "critic_approved": cover_letter.critic_approved,
            "status": application.status,
        }
