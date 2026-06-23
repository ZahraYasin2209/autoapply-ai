from sqladmin import ModelView

from autoapply.models import Application


class ApplicationAdmin(ModelView, model=Application):
    column_list = [
        Application.id,
        Application.user_id,
        Application.job_id,
        Application.status,
        Application.applied_at
    ]

    column_details_list = [
        Application.id,
        Application.user_id,
        Application.job_id,
        Application.status,
        Application.applied_at,
        Application.created_at,
        Application.updated_at,
    ]

    column_sortable_list = [Application.created_at]
    name = "Application"
    name_plural = "Applications"
    icon = "fa-solid fa-paper-plane"
