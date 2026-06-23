from sqladmin import ModelView

from autoapply.models import CoverLetter


class CoverLetterAdmin(ModelView, model=CoverLetter):
    column_list = [
        CoverLetter.id,
        CoverLetter.application_id,
        CoverLetter.revision_count,
        CoverLetter.critic_approved,
        CoverLetter.generated_at,
    ]

    column_details_list = [
        CoverLetter.id,
        CoverLetter.application_id,
        CoverLetter.draft_text,
        CoverLetter.final_text,
        CoverLetter.revision_count,
        CoverLetter.critic_approved,
        CoverLetter.generated_at,
        CoverLetter.created_at,
    ]

    name = "Cover Letter"
    name_plural = "Cover Letters"
    icon = "fa-solid fa-envelope"
