from sqladmin import ModelView

from autoapply.models import Job


class JobAdmin(ModelView, model=Job):
    column_list = [
        Job.id,
        Job.title,
        Job.company,
        Job.fit_score,
        Job.recommendation,
        Job.scraped_at
    ]

    column_details_list = [
        Job.id,
        Job.title,
        Job.company,
        Job.url,
        Job.fit_score,
        Job.recommendation,
        Job.fit_reasoning,
        Job.description,
        Job.scraped_at,
    ]

    column_searchable_list = [Job.title, Job.company]
    column_sortable_list = [Job.fit_score, Job.scraped_at]
    name = "Job"
    name_plural = "Jobs"
    icon = "fa-solid fa-briefcase"
