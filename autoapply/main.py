from fastapi import FastAPI
from sqladmin import Admin

from autoapply.database import engine, check_db_connection
from autoapply.admin import (
    UserAdmin,
    ResumeAdmin,
    SearchPreferenceAdmin,
    JobAdmin,
    ApplicationAdmin,
    CoverLetterAdmin,
    CriticReviewAdmin,
    ApplicationOutcomeAdmin,
    FeedbackAdmin,
    MemoryEntryAdmin,
)

app = FastAPI(
    title="AutoApply",
    description="Autonomous multi-agent job application system",
    version="1.0.0",
)

admin = Admin(app, engine, title="AutoApply Admin")
admin.add_view(UserAdmin)
admin.add_view(ResumeAdmin)
admin.add_view(SearchPreferenceAdmin)
admin.add_view(JobAdmin)
admin.add_view(ApplicationAdmin)
admin.add_view(CoverLetterAdmin)
admin.add_view(CriticReviewAdmin)
admin.add_view(ApplicationOutcomeAdmin)
admin.add_view(FeedbackAdmin)
admin.add_view(MemoryEntryAdmin)


@app.get("/health")
def health():
    return {"status": "ok", "db": check_db_connection()}
