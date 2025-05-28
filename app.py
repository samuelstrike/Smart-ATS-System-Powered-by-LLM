import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

load_dotenv() ## load all our environment variables

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_repsonse(input):
    model=genai.GenerativeModel('gemini-2.0-flash')
    response=model.generate_content(input)
    return response.text

def input_pdf_text(uploaded_file):
    reader=pdf.PdfReader(uploaded_file)
    text=""
    for page in range(len(reader.pages)):
        page=reader.pages[page]
        text+=str(page.extract_text())
    return text

input_prompt = """
Hey Act Like a skilled and very experienced ATS (Applicant Tracking System)
with deep knowledge of the tech industry — including software engineering, data science,
data analytics, and big data engineering.

Your tasks:
1. Evaluate the given resume against the job description.
2. Assign a percentage match score.
3. List the missing or weak keywords from the job description.
4. Provide a **profile summary**.
5. **Suggest clear, actionable recommendations** on how the resume can be improved to score more than 95%.

resume: {text}
description: {jd}

Return the response in the following JSON format:

{{
  "JD Match": "percentage",
  "MissingKeywords": ["keyword1", "keyword2"],
  "Profile Summary": "summary text",
  "ImprovementSuggestions": [
    "suggestion 1",
    "suggestion 2",
    "suggestion 3"
  ]
}}
"""

rewrite_prompt = """
You are an expert resume writer. Your task is to improve the candidate's resume based on the following:

1. The original resume.
2. The job description.
3. The improvement suggestions.

Make sure the updated resume is highly relevant to the job description, includes all suggested keywords, and improves clarity, impact, and formatting. Keep it professional and structured.

**Original Resume:**
{text}

**Job Description:**
{jd}

**Improvement Suggestions:**
{suggestions}

Provide the improved resume as a properly formatted plain text resume (not JSON or markdown).
"""

## streamlit app
st.title("Smart ATS Powered by Gemini 2.0 Flash")
st.markdown("""
This app uses Google Gemini 2.0 Flash to analyze your resume against a job description and provide actionable insights to improve your ATS score.
""")
st.text("Use AI to optimize your resume for better job matching!")
st.markdown("### Instructions")
st.markdown("""
1. **Paste the Job Description** in the text area below.
2. **Upload your Resume** in PDF format.
3. Click **Submit** to get your ATS score and recommendations.
""")
jd=st.text_area("Paste the Job Description")
uploaded_file=st.file_uploader("Upload Your Resume",type="pdf",help="Please uplaod the pdf")

submit = st.button("Submit")

if submit:
    if uploaded_file is not None:
        text=input_pdf_text(uploaded_file)
        filled_prompt = input_prompt.format(text=text, jd=jd)
        response=get_gemini_repsonse(filled_prompt)
        import re

        # Clean and parse response
        try:
            # Ensure only the JSON block is parsed
            json_str = re.search(r"\{.*\}", response, re.DOTALL).group()
            result = json.loads(json_str)
        except Exception as e:
            st.error("Couldn't parse LLM response.")
            st.code(response)
            st.stop()

        jd_match = result.get("JD Match", "N/A")
        st.markdown(f"### 🏷️ JD Match\n**✅ {jd_match}**" if jd_match != "N/A" else "JD Match: N/A")

        st.subheader("🧩 Missing Keywords")
        keywords = result.get("MissingKeywords", [])
        col1, col2 = st.columns(2)

        # Split keywords evenly between the two columns
        half = (len(keywords) + 1) // 2  # ensures even split for odd numbers

        with col1:
            for kw in keywords[:half]:
                st.markdown(f"- {kw}")

        with col2:
            for kw in keywords[half:]:
                st.markdown(f"- {kw}")

        st.subheader("🧠 Profile Summary")
        st.write(result.get("Profile Summary", "Not available"))

        jd_match_value = result.get("JD Match", "0").replace("%", "").strip()

        try:
            jd_score = int(jd_match_value)
        except ValueError:
            jd_score = 0  # fallback if something unexpected is returned

        if jd_score < 95:
            st.warning("Your JD Match is below 95%. Here are some suggestions to improve your resume:")
            st.subheader("📈 Recommendations to Improve Score to 95%+")
            for suggestion in result.get("ImprovementSuggestions", []):
                st.markdown(f"- ✅ {suggestion}")

            # Resume Improvement Suggestions
            suggestions = result.get("ImprovementSuggestions", [])
            suggestions_text = "\n".join(suggestions)

            # Create prompt to rewrite resume
            rewrite_filled_prompt = rewrite_prompt.format(text=text, jd=jd, suggestions=suggestions_text)

            # Get rewritten resume
            rewritten_resume = get_gemini_repsonse(rewrite_filled_prompt)

            # Display
            st.subheader("🚀 Rewritten Resume (Optimized for this JD)")
            st.code(rewritten_resume)
    
    else:
        st.warning("Please upload a resume and paste the job description.")