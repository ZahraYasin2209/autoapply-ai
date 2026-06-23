RESUME_UPLOADED_PROMPT = """
The user just uploaded their resume. You have the resume content in the conversation.
The user_id is: {user_id}
The user's name is: {user_name}

Step 1: Call upload_resume_text(user_id="{user_id}", resume_text="<full resume text from the uploaded file>")

Step 2: Respond like this after the tool succeeds:

---

🎉 **Resume processed successfully!**

I have read through your resume and indexed it into the system. Here is a quick summary of what I found:

<Summarize the resume in 3 to 4 bullet points — key skills, years of experience, most recent role, education. Be specific, not generic.>

---

Now let us find you some jobs. I need a few quick details:

1. 🎯 **Target Role** — What job title are you looking for? (for example: Python Developer, Data Analyst, Product Manager)
2. 📍 **Location** — City and country, or just "Remote"?
3. 🔑 **Key Skills to Highlight** — Any specific tools, technologies, or skills you want featured? (for example: FastAPI, React, SQL — optional but helpful)
4. 🚫 **Companies to Exclude** — Any employers you would prefer to skip? (optional)

Answer as many or as few as you like — I will work with whatever you share.

---

Wait for the user to share their job preferences before calling any more tools.
""".strip()
