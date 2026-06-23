import re
import uuid
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from tavily import TavilyClient

from config.settings.base import TAVILY_API_KEY
from autoapply.models.Job import Job
from autoapply.models.JobChunk import JobChunk
from autoapply.ai.utils.TextChunker import chunk_text
from autoapply.ai.utils.Embedder import Embedder


class JobSearchUtils:

    _JOB_BOARD_DOMAINS = {
        "linkedin", "indeed", "glassdoor", "monster", "ziprecruiter",
        "turing", "dice", "wellfound", "angel", "simplyhired", "careerbuilder",
        "jobstreet", "naukri", "remotive", "weworkremotely", "nodesk", "remoterocketship",
    }

    @staticmethod
    def _build_search_queries(
        target_role: str,
        location: str | None,
        keywords: str | None,
        seniority: str | None = None,
    ) -> list[str]:
        """Build queries that target company career pages, not job board listing pages."""
        location_str = f" {location}" if location and location.lower() != "remote" else " remote"
        keyword_parts = []

        if keywords:
            keyword_parts = [k.strip() for k in keywords.split(",") if k.strip()][:2]

        seniority_level = seniority.strip() \
            if seniority and seniority.lower() not in {"", "any", "open"} \
            else ""

        role_query_string = f"{seniority_level} {target_role}".strip() \
            if seniority_level \
            else target_role

        current_year = datetime.now().year
        search_queries = [
            f'"{role_query_string}" job opening{location_str} apply now {current_year}',
            f"{role_query_string}{location_str} careers hiring {' '.join(keyword_parts)}".strip(),
        ]

        for keyword in keyword_parts:
            search_queries.append(
                f"{keyword} {role_query_string} job{location_str} site:greenhouse.io OR site:lever.co OR site:workday.com"
            )

        return search_queries[:4]

    @staticmethod
    def _extract_domain_base(url: str) -> str | None:
        """Return the primary domain label (e.g. 'greenhouse' from greenhouse.io), or None."""
        try:
            hostname = urlparse(url).hostname or ""
            hostname = hostname.removeprefix("www.")
            return hostname.split(".")[0].lower() if hostname else None
        except Exception:
            return None

    @staticmethod
    def _is_job_board(url: str) -> bool:
        """Return True if the URL is a job board listing page rather than a specific posting."""
        domain_base = JobSearchUtils._extract_domain_base(url)

        return domain_base in JobSearchUtils._JOB_BOARD_DOMAINS if domain_base else False

    @staticmethod
    def _parse_company_from_url(url: str, title: str) -> str:
        """Extract company name from URL, avoiding job board domain names."""
        domain_base = JobSearchUtils._extract_domain_base(url)
        if domain_base and domain_base not in JobSearchUtils._JOB_BOARD_DOMAINS:
            return domain_base.capitalize()

        company_match = re.search(r"\bat\s+([A-Z][A-Za-z0-9& ]+)", title)
        if company_match:
            return company_match.group(1).strip()

        return "Unknown"

    @staticmethod
    def store_job_from_text(
        db: Session,
        title: str,
        company: str,
        description: str,
        url: str = "",
    ) -> Job:
        """Store a single job from manually-pasted text (no Tavily needed)."""
        existing_job = db.query(Job).filter(Job.url == url).first() if url else None
        if existing_job:
            return existing_job

        job = Job(
            title=title,
            company=company,
            url=url or f"manual://{uuid.uuid4()}",
            description=description,
        )
        db.add(job)
        db.flush()

        description_chunks = chunk_text(description)
        if description_chunks:
            chunk_embeddings = Embedder.embed_texts(description_chunks)
            for chunk_index, (chunk_text_content, chunk_embedding) in enumerate(zip(description_chunks, chunk_embeddings)):
                db.add(JobChunk(
                    job_id=job.id,
                    chunk_text=chunk_text_content,
                    embedding=chunk_embedding,
                    chunk_index=chunk_index,
                ))

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def search_and_store_jobs(
        db: Session,
        user_id: uuid.UUID,
        target_role: str,
        location: str | None = None,
        keywords: str | None = None,
        seniority: str | None = None,
        excluded_companies: list[str] | None = None,
        max_results: int = 10,
    ) -> list[Job]:
        placeholder_keys = {"tvly_your_key_here", "", None}
        if TAVILY_API_KEY in placeholder_keys:
            return []

        try:
            tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        except Exception:
            return []

        search_queries = JobSearchUtils._build_search_queries(target_role, location, keywords, seniority)
        excluded_companies_lower = [c.lower() for c in (excluded_companies or [])]

        seen_urls: set[str] = set()
        discovered_jobs: list[Job] = []

        for query in search_queries:
            if len(discovered_jobs) >= max_results:
                break

            try:
                search_response = tavily_client.search(
                    query=query,
                    max_results=5,
                    search_depth="advanced",
                    include_raw_content=True,
                )
            except Exception:
                continue

            for search_result in search_response.get("results", []):
                if len(discovered_jobs) >= max_results:
                    break

                url = search_result.get("url", "")
                title = search_result.get("title", target_role)
                description = search_result.get("raw_content") or search_result.get("content", "")
                company = JobSearchUtils._parse_company_from_url(url, title)

                if url in seen_urls:
                    continue
                if JobSearchUtils._is_job_board(url):
                    continue
                if any(excluded in company.lower() for excluded in excluded_companies_lower):
                    continue

                seen_urls.add(url)

                existing_job = db.query(Job).filter(Job.url == url).first()
                if existing_job:
                    discovered_jobs.append(existing_job)
                    continue

                job = Job(title=title, company=company, url=url, description=description)
                db.add(job)
                db.flush()

                description_chunks = chunk_text(description)
                if description_chunks:
                    chunk_embeddings = Embedder.embed_texts(description_chunks)
                    for chunk_index, (chunk_text_content, chunk_embedding) in enumerate(zip(description_chunks, chunk_embeddings)):
                        db.add(JobChunk(
                            job_id=job.id,
                            chunk_text=chunk_text_content,
                            embedding=chunk_embedding,
                            chunk_index=chunk_index,
                        ))

                discovered_jobs.append(job)

        db.commit()
        for discovered_job in discovered_jobs:
            db.refresh(discovered_job)

        return discovered_jobs
