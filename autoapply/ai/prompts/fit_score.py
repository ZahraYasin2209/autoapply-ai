FIT_PROMPT = """You are a career advisor evaluating how well a candidate fits a job.

JOB TITLE: {title}
COMPANY: {company}
JOB DESCRIPTION:
{description}

CANDIDATE RESUME EXCERPTS (most relevant sections):
{resume_excerpts}

Evaluate the fit and respond ONLY with valid JSON in this exact format:
{{
  "fit_score": <integer 0-100>,
  "recommendation": "<APPLY or SKIP>",
  "reasoning": "<2-3 sentences explaining the score>"
}}

Rules:
- fit_score >= 65 → recommendation must be APPLY
- fit_score < 65 → recommendation must be SKIP
- Be honest and specific in reasoning
"""
