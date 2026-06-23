COVER_LETTER_PROMPT = """You are writing a tailored cover letter for the following role.

JOB TITLE: {title}
COMPANY: {company}
JOB DESCRIPTION:
{description}

CANDIDATE RESUME EXCERPTS:
{resume_excerpts}

FIT SCORE: {fit_score}/100
FIT REASONING: {fit_reasoning}

LANGUAGE RULES — enforce every one:
• Write in a natural, human voice. If it sounds like AI generated it, rewrite it.
• ZERO hyphens used as dashes. Never write — or - between two phrases or clauses.
  Wrong: "I led the team — and delivered results"
  Right: "I led the team and delivered results"
  (Compound adjectives like "production-ready" or "full-stack" are fine.)
• ZERO buzzwords: dynamic, passionate, results-driven, leverage, synergy, innovative,
  transformative, spearheaded, utilized, impactful, excited to
• ZERO bullet points inside the letter body
• Mix sentence lengths. Short sentences hit harder.
• First person, active voice: "I built", "I led", "I reduced"
• Confident but not arrogant

FORMAT RULES:
• Exactly 4 paragraphs
• Under 400 words total
• No subject line, no date, no "Dear Hiring Manager" — start directly with paragraph 1

STRUCTURE:
  Para 1: Name the company and the exact role. Show genuine interest. One sentence on your background.
  Para 2: Two specific achievements from the resume with real numbers or outcomes.
  Para 3: What you bring to this specific team. Reference something real about this company.
  Para 4: Thank them. Express eagerness to discuss. Clear call to action.

ATS: Weave in 3 to 5 keywords from the job description naturally. Do not stuff them.

SELF-CHECK before outputting — scan your draft:
  ✗ Any em dash (—) or hyphen between phrases? Rewrite that sentence.
  ✗ Any buzzword from the list above? Replace with a concrete specific statement.
  ✗ Any bullet point in body? Convert to a sentence.
  ✗ Over 400 words? Trim.
  ✗ Missing company or role name in paragraph 1? Add it.

Output ONLY the cover letter body text. No subject line, no metadata, no preamble.
"""
