from sqladmin import ModelView

from autoapply.models import CriticReview


class CriticReviewAdmin(ModelView, model=CriticReview):
    column_list = [
        CriticReview.id,
        CriticReview.application_id,
        CriticReview.verdict,
        CriticReview.attempt_number,
        CriticReview.reviewed_at,
    ]

    column_details_list = [
        CriticReview.id,
        CriticReview.application_id,
        CriticReview.verdict,
        CriticReview.feedback_text,
        CriticReview.attempt_number,
        CriticReview.reviewed_at,
    ]

    name = "Critic Review"
    name_plural = "Critic Reviews"
    icon = "fa-solid fa-magnifying-glass"
