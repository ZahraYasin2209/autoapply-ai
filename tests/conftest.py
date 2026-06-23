import uuid
from unittest.mock import MagicMock

import pytest

from autoapply.models.Application import Application
from autoapply.models.CoverLetter import CoverLetter
from autoapply.models.Job import Job
from autoapply.models.Resume import Resume
from autoapply.models.User import User


# Shared UUIDs
USER_ID = uuid.uuid4()
JOB_ID = uuid.uuid4()
RESUME_ID = uuid.uuid4()
APPLICATION_ID = uuid.uuid4()


# Model fixtures
@pytest.fixture
def sample_user() -> User:
    user = User(name="Test User", email="test@example.com")
    user.id = USER_ID
    return user


@pytest.fixture
def sample_job() -> Job:
    job = Job(
        title="Machine Learning Engineer",
        company="Acme Corp",
        url="https://acme.com/jobs/mle",
        description="We need a Python ML engineer with PyTorch experience.",
    )
    job.id = JOB_ID
    job.fit_score = 80.0
    job.fit_reasoning = "Strong Python and ML background."

    return job


@pytest.fixture
def sample_resume() -> Resume:
    resume = Resume(
        user_id=USER_ID,
        raw_text="Experienced ML engineer with 5 years in Python and PyTorch.",
    )
    resume.id = RESUME_ID
    resume.chunks = []
    return resume


@pytest.fixture
def sample_application(sample_job) -> Application:
    app = Application(user_id=USER_ID, job_id=JOB_ID, status="draft")
    app.id = APPLICATION_ID
    app.job = sample_job
    return app


@pytest.fixture
def sample_cover_letter(sample_application) -> CoverLetter:
    cl = CoverLetter(
        application_id=APPLICATION_ID,
        draft_text="I am excited to apply for this role at Acme Corp.",
        revision_count=0,
        critic_approved=False,
    )
    cl.id = uuid.uuid4()
    return cl


# Mock DB session
@pytest.fixture
def mock_db() -> MagicMock:
    """SQLAlchemy session mock with chainable query interface."""
    db = MagicMock()
    query_mock = MagicMock()
    db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = None
    query_mock.scalar.return_value = 0
    return db


# Mock embedding
@pytest.fixture
def fake_embedding() -> list[float]:
    return [0.1] * 384
