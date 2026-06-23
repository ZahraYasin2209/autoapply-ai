PIPELINE_PROMPT = """
Run the AutoApply pipeline for {user_name}.

Context:
- user_id: {user_id}
- target_role: {target_role}
- seniority: {seniority}
- location: {location}
- keywords: {keywords}

Tools only store data. YOU do all the thinking.
Never show raw UUIDs. Always use job titles and company names.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — Find Jobs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Say: "Let me find {target_role} jobs{location_clause} for you..."

Use your web search to find 5 specific, real job postings.
Search for: {seniority} {target_role} {location}
Example query: "{seniority} {target_role} {location} site:greenhouse.io OR site:lever.co"
Look for individual postings on: greenhouse.io, lever.co, workday.com, arc.dev, company career pages.
Avoid aggregator listing pages (LinkedIn /jobs browse, Indeed search results, etc.).

For each specific posting you find, call:
  store_job_manually(
    title="[exact job title]",
    company="[company name]",
    description="[full job description text — as much as you can get]",
    url="[direct posting URL]"
  )

Show what you stored:
"Here are the jobs I found:

1. [Title] at [Company]
2. [Title] at [Company]
..."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — Score Fit (you do this)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Say: "Now let me check how well your profile matches each role..."

For EACH job:
  Call: get_fit_context(user_id="{user_id}", job_id="<job_id>")
  Read the resume excerpts and job description carefully.
  Score honestly: fit_score (0 to 100), recommendation (APPLY if 65 or above, SKIP if below), 2-sentence reasoning.
  Call: save_fit_score_tool(job_id, fit_score, recommendation, reasoning)

Show the summary:

"Here is your fit summary:

| Role | Company | Score | Verdict |
|------|---------|-------|---------|
| ...  | ...     |  82   | Apply   |
| ...  | ...     |  41   | Skip    |

Writing cover letters for the Apply roles now."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3 — Write Cover Letters (you write these)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For each APPLY job:

  Say: "Writing your cover letter for [Title] at [Company]..."
  Call: get_cover_letter_context_tool(user_id="{user_id}", job_id="<job_id>")

  Read everything: resume excerpts, job description, past approved letters.

  Write the cover letter following ALL of these rules:

  ── LANGUAGE RULES (most important) ──
  • Natural, human voice. If it sounds like AI wrote it, rewrite it.
  • ZERO hyphens as dashes. Never use — or - between two phrases or clauses.
    Wrong: "I led the backend team — and cut latency by 40%"
    Right: "I led the backend team and cut latency by 40%"
    (Hyphenated compound adjectives like "production-ready" are fine.)
  • ZERO buzzwords: dynamic, passionate, results-driven, leverage, synergy, innovative,
    transformative, spearheaded, utilized, impactful
  • ZERO bullet points in the letter body
  • Mix sentence lengths. Short sentences hit harder.
  • First person, active voice: "I built", "I reduced", "I noticed"
  • Confident but not arrogant

  ── FORMAT RULES ──
  • Exactly 4 paragraphs
  • Under 400 words
  • No subject line, no date, no "Dear Hiring Manager" — start with the first paragraph directly

  ── STRUCTURE ──
  Para 1: Name the company and the exact role. Show genuine interest. One sentence on your background.
  Para 2: Two specific achievements from the resume with real numbers or outcomes.
  Para 3: What you bring to this specific team. Reference something real about this company.
  Para 4: Thank them. Express eagerness. Clear call to action.

  ── ATS ──
  Weave in 3 to 5 keywords from the job description naturally — do not stuff them.

  ── SELF-CHECK before saving ──
  Before calling save_cover_letter_tool, scan your draft:
  ✗ Any em dash (—) or hyphen between phrases? Rewrite that sentence.
  ✗ Any buzzword? Replace with a concrete specific statement.
  ✗ Any bullet point in body? Convert to a sentence.
  ✗ Over 400 words? Trim.
  ✗ Missing company or role name in para 1? Add it.

  Only after passing all checks: call save_cover_letter_tool(user_id="{user_id}", job_id="<job_id>", cover_letter_text="<your letter>")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4 — Critic Review (you review)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Say: "Let me review this letter..."

Check every item:
  ✓ Names the company and role specifically?
  ✓ Real achievements with outcomes?
  ✓ Natural human-sounding language?
  ✓ Zero hyphens used as dashes?
  ✓ Zero buzzwords?
  ✓ Under 400 words?
  ✓ Strong opening and closing?

If ALL pass: verdict APPROVE
If ANY fail: verdict REVISE — rewrite the letter completely, then save with revised_text

Call: save_critic_review_tool(
  application_id="<application_id>",
  verdict="<APPROVE or REVISE>",
  feedback="<specific critique>",
  revised_text="<fully rewritten letter if REVISE, empty string if APPROVE>"
)

Show the final approved letter:

"Cover letter approved for [Title] at [Company].

---
[final cover letter text]
---

Ready for the next one?"

Wait for user confirmation before moving to the next job.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5 — Final Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Here is everything we did today:

Jobs found: X
Jobs to apply for: X
Cover letters approved: X

You can review everything in the admin panel: http://localhost:8000/admin

Want to search for more roles, or refine any of these letters?"
""".strip()
