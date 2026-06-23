IMPROVE_PROMPT = """
The user wants to refine their cover letter for application {application_id}.

Their feedback: "{feedback}"

Step 1: Acknowledge their feedback warmly and specifically.

Step 2: Call get_application_status(application_id="{application_id}") to get the current letter.

Step 3: Rewrite the cover letter incorporating their feedback. Follow ALL these rules:

LANGUAGE RULES:
• Natural human voice — as if the candidate wrote it themselves
• ZERO hyphens used as dashes — never write — or - between two phrases or clauses
  Wrong: "I built the system — it reduced errors by 30%"
  Right: "I built the system and reduced errors by 30%"
• ZERO buzzwords: dynamic, passionate, results-driven, leverage, synergy, innovative, spearheaded, utilized
• ZERO bullet points in the body
• Mix sentence lengths. Short sentences hit harder.
• First person, active voice: "I built", "I led", "I reduced"
• Confident but not arrogant

FORMAT:
• Exactly 4 paragraphs, under 400 words
• No subject line, no date, no header — start directly with the first paragraph

ATS: Weave in 3 to 5 keywords from the job description naturally. Do not stuff them.

SELF-CHECK before saving:
✗ Any em dash (—) or hyphen between phrases? Rewrite that sentence.
✗ Any buzzword? Replace with a concrete specific statement.
✗ Any bullet in body? Convert to a sentence.
✗ Over 400 words? Trim.

Step 4: Call save_critic_review_tool(
  application_id="{application_id}",
  verdict="REVISE",
  feedback="User requested: {feedback}",
  revised_text="<your fully rewritten letter>"
)

Step 5: Show the updated letter:

"Here is your updated cover letter:

---
[revised cover letter]
---

How does this feel? Happy with it, or shall we keep refining?"
""".strip()
