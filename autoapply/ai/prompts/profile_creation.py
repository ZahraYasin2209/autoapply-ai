PROFILE_CREATED_PROMPT = """
The user just shared their email address: {email}
Their name is: {user_name}

Step 1: Call create_user(name="{user_name}", email="{email}") and save the user_id returned.

Step 2: Respond like this:

---

✅ **Profile created successfully!**

Here is what I have on file:

👤 **Name:** {user_name}
📧 **Email:** {email}

---

Now let us get your resume into the system. Your resume is the foundation of everything — I will use it to score your job fit and personalize every cover letter.

📎 **Please upload your resume as a PDF** using the attachment button in this chat.

A few things to note:
- Make sure it is your most up to date version
- PDF format works best
- I will read it, break it into sections, and index it automatically

Go ahead and attach it whenever you are ready!

---

Wait for the user to upload their resume. Do not proceed until they do.
""".strip()
