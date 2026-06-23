from sqladmin import ModelView

from autoapply.models import Feedback


class FeedbackAdmin(ModelView, model=Feedback):
    column_list = [
        Feedback.id,
        Feedback.application_id,
        Feedback.rating,
        Feedback.comment,
        Feedback.created_at
    ]

    column_details_list = [
        Feedback.id,
        Feedback.application_id,
        Feedback.rating,
        Feedback.comment,
        Feedback.created_at,
    ]

    name = "Feedback"
    name_plural = "Feedback"
    icon = "fa-solid fa-star"
