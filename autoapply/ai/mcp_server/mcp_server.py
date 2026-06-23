"""
AutoApply MCP Server
--------------------
Tools expose data to Claude Desktop. Claude does ALL the thinking.
All prompts and agent instructions live in autoapply/ai/prompts/.

Claude Desktop config (%APPDATA%\\Claude\\claude_desktop_config.json):
{
  "mcpServers": {
    "autoapply": {
      "command": "C:\\\\path\\\\to\\\\AutoApply\\\\venv\\\\Scripts\\\\python.exe",
      "args": ["C:\\\\path\\\\to\\\\AutoApply\\\\autoapply\\\\ai\\\\mcp_server\\\\mcp_server.py"],
      "env": { "PYTHONPATH": "C:\\\\path\\\\to\\\\AutoApply" }
    }
  }
}
"""

import json
import sys
import uuid
from pathlib import Path


PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mcp.server.fastmcp import FastMCP

from autoapply.ai.prompts import (
    AGENT_INSTRUCTIONS,
    GREET_PROMPT,
    PROFILE_CREATED_PROMPT,
    RESUME_UPLOADED_PROMPT,
    PIPELINE_PROMPT,
    IMPROVE_PROMPT,
)
from autoapply.database import SessionLocal
from autoapply.models.Application import Application
from autoapply.models.CoverLetter import CoverLetter
from autoapply.models.User import User
from autoapply.ai.utils.ContextUtils import ContextUtils
from autoapply.ai.utils.JobSearchUtils import JobSearchUtils
from autoapply.ai.utils.MemoryUtils import MemoryUtils
from autoapply.ai.utils.ResumeUtils import ResumeUtils
from autoapply.ai.utils.SaveUtils import SaveUtils


# MCP Server
mcp = FastMCP("AutoApply", instructions=AGENT_INSTRUCTIONS)


# Prompts
@mcp.prompt()
def greet_user(user_name: str) -> str:
    """Warm introduction when user says their name."""
    return GREET_PROMPT.format(user_name=user_name)


@mcp.prompt()
def profile_created(user_name: str, email: str) -> str:
    """Called after user shares their email. Creates profile and asks for resume."""
    return PROFILE_CREATED_PROMPT.format(user_name=user_name, email=email)


@mcp.prompt()
def resume_uploaded(user_name: str, user_id: str) -> str:
    """Called after user uploads resume. Processes it and collects job preferences."""
    return RESUME_UPLOADED_PROMPT.format(user_name=user_name, user_id=user_id)


@mcp.prompt()
def run_pipeline(
    user_name: str,
    user_id: str,
    target_role: str,
    location: str,
    keywords: str,
    seniority: str = "",
) -> str:
    """Run the full pipeline: search jobs â†’ score fit â†’ write & review cover letters."""
    location_clause = f" in {location}" if location and location.lower() != "remote" else " (remote)"
    return PIPELINE_PROMPT.format(
        user_name=user_name,
        user_id=user_id,
        target_role=target_role,
        location=location,
        keywords=keywords,
        seniority=seniority or "any level",
        location_clause=location_clause,
    )


@mcp.prompt()
def improve_cover_letter(application_id: str, feedback: str) -> str:
    """Refine a cover letter based on user feedback."""
    return IMPROVE_PROMPT.format(application_id=application_id, feedback=feedback)


# Tool 1: Create or fetch user
@mcp.tool()
def create_user(name: str, email: str) -> str:
    """
    Create a new user profile or return the existing one if the email is already registered.

    Args:
        name: Full name of the user (e.g. "Zahra Yasin").
        email: Unique email address used to identify the user.

    Returns:
        JSON with user_id, name, and email.
        If the email already exists the existing record is returned unchanged.
    """
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(name=name, email=email)
            db.add(user)
            db.commit()
            db.refresh(user)

        return json.dumps({
            "user_id": str(user.id),
            "name": user.name,
            "email": user.email,
        })


# Tool 2: Upload resume from file path
@mcp.tool()
def upload_resume(user_id: str, file_path: str) -> str:
    """
    Ingest a PDF resume from a local file path, chunk it, and store embeddings.

    Args:
        user_id: UUID of the user who owns this resume.
        file_path: Absolute path to a PDF file on the local filesystem.

    Returns:
        JSON with resume_id and chunks_created on success, or an error message
        if the file does not exist or is not a PDF.
    """
    path = Path(file_path)
    if not path.exists():
        return json.dumps({"error": f"File not found: {file_path}"})

    if path.suffix.lower() != ".pdf":
        return json.dumps({"error": "Only PDF files are supported."})

    with SessionLocal() as db:
        resume = ResumeUtils.ingest_resume(db, uuid.UUID(user_id), path.read_bytes(), path.name)

        return json.dumps({
            "resume_id": str(resume.id),
            "chunks_created": len(resume.chunks),
            "message": "Resume processed successfully.",
        })


# Tool 3: Upload resume from text
@mcp.tool()
def upload_resume_text(user_id: str, resume_text: str) -> str:
    """
    Ingest a resume from raw text, chunk it, and store embeddings.

    Use this when the user uploads a PDF directly in Claude Desktop â€” extract
    the full text from the PDF and pass it here instead of a file path.

    Args:
        user_id: UUID of the user who owns this resume.
        resume_text: Full plain-text content of the resume.

    Returns:
        JSON with resume_id and chunks_created on success, or an error message
        if resume_text is empty.
    """
    if not resume_text.strip():
        return json.dumps({"error": "resume_text is empty."})

    with SessionLocal() as db:
        resume = ResumeUtils.ingest_resume_from_text(db, uuid.UUID(user_id), resume_text)

        return json.dumps({
            "resume_id": str(resume.id),
            "chunks_created": len(resume.chunks),
            "message": "Resume processed successfully from text.",
        })


# Tool 4: Search jobs via Tavily
@mcp.tool()
def search_jobs(
    user_id: str,
    target_role: str,
    location: str = "",
    keywords: str = "",
    seniority: str = "",
    max_results: int = 10,
) -> str:
    """
    Search for job postings via Tavily and store results in the database.

    This is a fallback tool. Prefer using built-in web search to find individual
    postings on greenhouse.io, lever.co, or arc.dev, then call store_job_manually
    for each one. Use this tool only when web search yields nothing.

    Args:
        user_id: UUID of the user performing the search.
        target_role: Job title to search for (e.g. "Machine Learning Engineer").
        location: City, country, or "remote". Defaults to remote if omitted.
        keywords: Comma-separated skills or technologies (e.g. "Python, LangChain").
        seniority: Experience level to include in queries (e.g. "junior", "senior", "lead").
        max_results: Maximum number of jobs to store. Defaults to 10.

    Returns:
        JSON with total count and list of stored jobs (job_id, title, company, url).
        If no results are found, returns a message instructing to use web search instead.
    """
    with SessionLocal() as db:
        discovered_jobs = JobSearchUtils.search_and_store_jobs(
            db=db,
            user_id=uuid.UUID(user_id),
            target_role=target_role,
            location=location or None,
            keywords=keywords or None,
            seniority=seniority or None,
            max_results=max_results,
        )

        if not discovered_jobs:
            return json.dumps({
                "total": 0,
                "jobs": [],
                "message": (
                    "No jobs found via Tavily. Use your built-in web search to find "
                    "5 specific job postings, then call store_job_manually for each."
                ),
            })

        return json.dumps({
            "total": len(discovered_jobs),
            "jobs": [
                {
                    "job_id": str(job.id),
                    "title": job.title,
                    "company": job.company,
                    "url": job.url,
                }
                for job in discovered_jobs
            ],
        })


# Tool 5: Store a job from pasted text
@mcp.tool()
def store_job_manually(title: str, company: str, description: str, url: str = "") -> str:
    """
    Store a single job posting found via web search or pasted by the user.

    Call this for every job discovered through built-in web search before scoring fit.
    The job is chunked and embedded so it can be matched against the user's resume.

    Args:
        title: Exact job title as shown on the posting (e.g. "Senior AI Engineer").
        company: Company name (e.g. "Anthropic").
        description: Full job description text. More content means better fit scoring.
        url: Direct URL to the job posting. Leave empty if not available.

    Returns:
        JSON with job_id, title, and company. Use job_id in get_fit_context next.
    """
    with SessionLocal() as db:
        job = JobSearchUtils.store_job_from_text(
            db=db, title=title, company=company, description=description, url=url or ""
        )

        return json.dumps({
            "job_id": str(job.id),
            "title": job.title,
            "company": job.company,
            "message": "Job stored. Call get_fit_context with this job_id to score fit.",
        })


# Tool 6: Get fit context
@mcp.tool()
def get_fit_context(user_id: str, job_id: str) -> str:
    """
    Fetch the most relevant resume excerpts and job description for fit scoring.

    Uses cosine similarity to retrieve the top resume chunks most relevant to the
    job description. Read the returned context carefully before calling save_fit_score_tool.

    Args:
        user_id: UUID of the user whose resume will be matched.
        job_id: UUID of the job to score against.

    Returns:
        JSON with job details (title, company, description) and resume_excerpts
        (the top matching chunks from the user's resume).
    """
    with SessionLocal() as db:
        fit_scoring_context = ContextUtils.get_fit_context(db, uuid.UUID(user_id), uuid.UUID(job_id))

        return json.dumps(fit_scoring_context)


# Tool 7: Save fit score
@mcp.tool()
def save_fit_score_tool(job_id: str, fit_score: float, recommendation: str, reasoning: str) -> str:
    """
    Persist Claude's fit score and recommendation for a job.

    Call this after reading get_fit_context and forming your own judgment.
    Do not call this without first reading the resume and job description.

    Args:
        job_id: UUID of the job being scored.
        fit_score: Numeric score from 0 to 100 reflecting how well the candidate fits.
        recommendation: Must be exactly "APPLY" (score >= 65) or "SKIP" (score < 65).
        reasoning: Two honest sentences explaining the score.

    Returns:
        JSON confirming the saved job_id, title, company, fit_score, and recommendation.
    """
    with SessionLocal() as db:
        scored_job = SaveUtils.save_fit_score(
            db=db,
            job_id=uuid.UUID(job_id),
            fit_score=fit_score,
            recommendation=recommendation,
            reasoning=reasoning,
        )

        return json.dumps({
            "job_id": str(scored_job.id),
            "title": scored_job.title,
            "company": scored_job.company,
            "fit_score": scored_job.fit_score,
            "recommendation": scored_job.recommendation,
        })


# Tool 8: Get cover letter context
@mcp.tool()
def get_cover_letter_context_tool(user_id: str, job_id: str) -> str:
    """
    Fetch everything needed to write a tailored cover letter.

    Retrieves the top resume chunks most relevant to the job, full job details,
    and up to two past approved cover letters from RAG memory as style reference.
    Read all returned content before writing the letter.

    Args:
        user_id: UUID of the user whose resume and memory will be used.
        job_id: UUID of the job the cover letter is being written for.

    Returns:
        JSON with job details, resume_excerpts, and past_letters (approved letters
        from memory, used as tone and style reference).
    """
    with SessionLocal() as db:
        cover_letter_writing_context = ContextUtils.get_cover_letter_context(db, uuid.UUID(user_id), uuid.UUID(job_id))

        return json.dumps(cover_letter_writing_context)


# Tool 9: Save cover letter
@mcp.tool()
def save_cover_letter_tool(user_id: str, job_id: str, cover_letter_text: str) -> str:
    """
    Save a cover letter draft to the database.

    Only call this after passing the self-check (no em dashes, no buzzwords,
    no bullets, under 400 words, company and role named in paragraph 1).
    Creates an Application record if one does not already exist for this user/job pair.

    Args:
        user_id: UUID of the user the cover letter belongs to.
        job_id: UUID of the job this cover letter targets.
        cover_letter_text: The full cover letter body text (no subject line or metadata).

    Returns:
        JSON with application_id and revision_count. Use application_id in
        save_critic_review_tool next.
    """
    with SessionLocal() as db:
        application, cover_letter = SaveUtils.save_cover_letter(
            db=db, user_id=uuid.UUID(user_id), job_id=uuid.UUID(job_id),
            cover_letter_text=cover_letter_text,
        )

        return json.dumps({
            "application_id": str(application.id),
            "revision_count": cover_letter.revision_count,
            "message": "Cover letter saved.",
        })


# Tool 10: Save critic review
@mcp.tool()
def save_critic_review_tool(
    application_id: str,
    verdict: str,
    feedback: str,
    revised_text: str = "",
) -> str:
    """
    Save a critic review verdict for a cover letter.

    On APPROVE: the cover letter is finalized, the application status is set to
    "ready", and the approved letter is automatically stored in RAG memory so
    future letters can learn from it.

    On REVISE: the revised_text replaces the current draft and revision_count
    is incremented. Rewrite the full letter before passing it here.

    Args:
        application_id: UUID of the application being reviewed.
        verdict: Must be exactly "APPROVE" or "REVISE".
        feedback: Specific critique â€” what works (on APPROVE) or what to fix (on REVISE).
        revised_text: The fully rewritten cover letter body. Required when verdict is REVISE.

    Returns:
        JSON with verdict, attempts count, critic_approved flag, final_text, and
        application status.
    """
    with SessionLocal() as db:
        critic_review_result = SaveUtils.save_critic_review(
            db=db, application_id=uuid.UUID(application_id),
            verdict=verdict, feedback=feedback, revised_text=revised_text or None,
        )

        return json.dumps(critic_review_result)


# Tool 11: Get application status
@mcp.tool()
def get_application_status(application_id: str) -> str:
    """
    Retrieve the current status of an application and its cover letter.

    Use this before improving a cover letter to read the current approved or
    draft text, revision count, and overall application status.

    Args:
        application_id: UUID of the application to look up.

    Returns:
        JSON with application_id, job_id, status, and a cover_letter object
        containing the current text (final if approved, draft otherwise),
        critic_approved flag, and revision_count. Returns an error if not found.
    """
    with SessionLocal() as db:
        application = db.query(Application).filter(Application.id == uuid.UUID(application_id)).first()

        if not application:
            return json.dumps({"error": "Application not found."})

        cover_letter = db.query(CoverLetter).filter(CoverLetter.application_id == application.id).first()

        return json.dumps({
            "application_id": str(application.id),
            "job_id": str(application.job_id),
            "status": application.status,
            "cover_letter": {
                "text": cover_letter.final_text or cover_letter.draft_text or "",
                "critic_approved": cover_letter.critic_approved,
                "revision_count": cover_letter.revision_count,
            } if cover_letter else None,
        })


# Tool 12: Retrieve past memory
@mcp.tool()
def retrieve_past_memory(user_id: str, query: str, entry_type: str = "", top_k: int = 3) -> str:
    """
    Retrieve semantically similar past memory entries using vector search.

    Searches the user's memory store using cosine similarity against the query
    embedding. Used to surface past approved cover letters, outcomes, or notes
    relevant to the current task.

    Args:
        user_id: UUID of the user whose memory to search.
        query: Natural language query used to find similar entries
               (e.g. the job title or a skill).
        entry_type: Filter by memory type. Use "approved_cover_letter" to retrieve
                    past letters. Leave empty to search all types.
        top_k: Number of results to return. Defaults to 3.

    Returns:
        JSON list of memory entries, each with entry_type, content (first 500 chars),
        and source_outcome.
    """
    with SessionLocal() as db:
        entries = MemoryUtils.retrieve_memory(
            db=db, user_id=uuid.UUID(user_id),
            query=query, entry_type=entry_type or None, top_k=top_k,
        )

        return json.dumps([
            {"entry_type": e.entry_type, "content": e.content[:500], "source_outcome": e.source_outcome}
            for e in entries
        ])


if __name__ == "__main__":
    mcp.run()



