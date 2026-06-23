from sqladmin import ModelView

from autoapply.models import Resume


class ResumeAdmin(ModelView, model=Resume):
    column_list = [
        Resume.id,
        Resume.user_id,
        Resume.file_path,
        Resume.created_at,
        Resume.updated_at
    ]

    column_details_list = [
        Resume.id,
        Resume.user_id,
        Resume.file_path,
        Resume.raw_text,
        Resume.created_at,
        Resume.updated_at,
    ]

    column_formatters = {
        "file_path": lambda resume, attr: resume.file_path or "(uploaded via chat)",
    }

    column_formatters_detail = {
        "file_path": lambda resume, attr: resume.file_path or "(uploaded via chat)",
        "raw_text": lambda resume, attr: (resume.raw_text or "")[:2000] + ("..." if resume.raw_text and len(resume.raw_text) > 2000 else ""),
    }

    name = "Resume"
    name_plural = "Resumes"
    icon = "fa-solid fa-file"
