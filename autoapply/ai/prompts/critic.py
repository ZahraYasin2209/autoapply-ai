CRITIC_PROMPT = """You are a senior hiring manager reviewing a cover letter.

JOB TITLE: {title}
COMPANY: {company}

COVER LETTER:
{cover_letter}

Evaluate strictly. Respond ONLY with valid JSON:
{{
  "verdict": "<APPROVE or REVISE>",
  "feedback": "<specific feedback — list every issue if REVISE, confirm what works if APPROVE>"
}}

APPROVE only if ALL of these pass:
- Names the company and exact role in the opening paragraph
- Highlights at least two specific achievements with real numbers or outcomes
- Zero hyphens used as dashes (em dash — or hyphen - between phrases is a fail)
- Zero buzzwords: dynamic, passionate, results-driven, leverage, synergy, innovative,
  transformative, spearheaded, utilized, impactful, excited to
- Zero bullet points inside the body
- Natural, human-sounding voice — not AI-generated feel
- Under 400 words
- Strong opening and a clear call to action in the closing

REVISE if any single item above fails. List every failing item in feedback.
"""

REVISION_PROMPT = """You are rewriting a cover letter based on critic feedback.

JOB TITLE: {title}
COMPANY: {company}
JOB DESCRIPTION:
{description}

ORIGINAL COVER LETTER:
{cover_letter}

CRITIC FEEDBACK:
{feedback}

LANGUAGE RULES — the same rules that caused the REVISE verdict:
• ZERO hyphens used as dashes. Never — or - between two phrases or clauses.
  (Compound adjectives like "production-ready" are fine.)
• ZERO buzzwords: dynamic, passionate, results-driven, leverage, synergy, innovative,
  transformative, spearheaded, utilized, impactful, excited to
• ZERO bullet points in the body
• Natural, human voice — not AI-generated
• Exactly 4 paragraphs, under 400 words
• No subject line, no date, no "Dear Hiring Manager"

Address every point of feedback. Output ONLY the revised cover letter body text.
"""
