from sqladmin import ModelView

from autoapply.models import ApplicationOutcome


class ApplicationOutcomeAdmin(ModelView, model=ApplicationOutcome):
    column_list = [
        ApplicationOutcome.id,
        ApplicationOutcome.application_id,
        ApplicationOutcome.outcome,
        ApplicationOutcome.outcome_date,
    ]

    column_details_list = [
        ApplicationOutcome.id,
        ApplicationOutcome.application_id,
        ApplicationOutcome.outcome,
        ApplicationOutcome.outcome_date,
        ApplicationOutcome.notes,
        ApplicationOutcome.created_at,
    ]

    name = "Application Outcome"
    name_plural = "Application Outcomes"
    icon = "fa-solid fa-chart-line"
