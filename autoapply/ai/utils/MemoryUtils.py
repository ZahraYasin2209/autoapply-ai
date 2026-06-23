import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from config.settings.base import MEMORY_TOP_K
from autoapply.models.Application import Application
from autoapply.models.CoverLetter import CoverLetter
from autoapply.models.MemoryEntry import MemoryEntry
from autoapply.ai.utils.Embedder import Embedder


class MemoryUtils:
    @staticmethod
    def store_memory(
        db: Session,
        user_id: uuid.UUID,
        entry_type: str,
        content: str,
        source_outcome: str | None = None,
    ) -> MemoryEntry:
        content_embedding = Embedder.embed_text(content)
        memory_entry = MemoryEntry(
            user_id=user_id,
            entry_type=entry_type,
            content=content,
            embedding=content_embedding,
            source_outcome=source_outcome,
        )
        db.add(memory_entry)
        db.commit()
        db.refresh(memory_entry)

        return memory_entry

    @staticmethod
    def retrieve_memory(
        db: Session,
        user_id: uuid.UUID,
        query: str,
        entry_type: str | None = None,
        top_k: int = MEMORY_TOP_K,
    ) -> list[MemoryEntry]:
        query_embedding = Embedder.embed_text(query)
        embedding_vector_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        entry_type_filter = "AND entry_type = :entry_type" if entry_type else ""
        query_params: dict = {
            "user_id": str(user_id),
            "embedding": embedding_vector_str,
            "top_k": top_k,
        }
        if entry_type:
            query_params["entry_type"] = entry_type

        memory_rows = db.execute(
            text(f"""
                SELECT id, entry_type, content, source_outcome, stored_at
                FROM memory_entries
                WHERE user_id = :user_id
                {entry_type_filter}
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """),
            query_params,
        ).fetchall()

        return [
            MemoryEntry(
                id=row[0],
                user_id=user_id,
                entry_type=row[1],
                content=row[2],
                source_outcome=row[3],
                stored_at=row[4],
            )
            for row in memory_rows
        ]

    @staticmethod
    def store_approved_cover_letter(db: Session, application_id: uuid.UUID) -> MemoryEntry | None:
        """Store final approved cover letter as a RAG memory entry."""
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            return None

        cover_letter = db.query(CoverLetter).filter(
            CoverLetter.application_id == application_id
        ).first()

        if not cover_letter or not cover_letter.final_text or not cover_letter.critic_approved:
            return None

        approved_letter_content = (
            f"Approved cover letter for role at {application.job.company}:\n\n{cover_letter.final_text}"
        )

        return MemoryUtils.store_memory(
            db=db,
            user_id=application.user_id,
            entry_type="approved_cover_letter",
            content=approved_letter_content,
            source_outcome="approved",
        )
