import streamlit as st
from supabase import create_client, Client
import pandas as pd
import os
import requests  # For API call
from dotenv import load_dotenv
import hmac, hashlib
from streamlit_option_menu import option_menu
import base64, json
# Load environment variables
load_dotenv()

# Supabase Credentials (Replace with your Supabase details)
url: str  = os.environ.get("SUPABASE_URL")
key: str  = os.environ.get("SUPABASE_KEY")

# Initialize Supabase Client
supabase: Client = create_client(url, key)

# Function to fetch job data
def fetch_jobs(hashed_id):
    response = supabase.table("job_details").select("position, company, technical_requirements, experience, url, job_id").eq("hash_user_details", hashed_id).execute()
    if response.data:
        return pd.DataFrame(response.data)  # Convert to DataFrame
    return pd.DataFrame(columns=["Position", "Company", "Technical Requirements", "Experience", "URL"])  # Empty Table

# Function to delete a job by ID
def delete_job(job_id):
    response = supabase.table("job_details").delete().eq("job_id", job_id).execute()
    return response

# Function to hash credentials
def hash_id(user_id):
    return hmac.new(os.getenv("HASH_SECRET").encode(), user_id.encode(), hashlib.sha256).hexdigest()

def encode_pdf(pdf_bytes):
    """Encodes PDF bytes into a JSON-serializable Base64 string."""
    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")  # Convert bytes → Base64 → String
    return base64_pdf  # Store in a JSON object

# Function to call API for resume analysis
def process_resume(resume_text, user_id):
    API_URL = "https://job-scraper-backend-e616ed8dec66.herokuapp.com/get_similarity"  # Replace with actual API URL
    response = requests.post(API_URL, json={"resume_contents": encode_pdf(resume_text), "user_id": user_id})
    
    if response.status_code == 200:
        return response.json()["result"]  # Assumes JSON response with similarity_score, compatible_skills, missing_skills

# Streamlit App Configuration
st.set_page_config(page_title="Job Listings Dashboard", page_icon="📌", layout="wide")

query_params = st.query_params
user_id = query_params.get("user_id")

# Sidebar Navigation
# Sidebar Design
# Sidebar Design
# Remove radio bullets by using selectbox
with st.sidebar:
    page = option_menu(
        menu_title="🔗 Navigation Menu",
        options=["View Listings", "Resume Analysis"],
        icons=["📋", "📄"],
        default_index=0,
        menu_icon="🔗"
    )

st.sidebar.markdown("---")  # Horizontal separator
st.sidebar.write("💡 **New:** You can now access the **Resume Analysis** tab to gain **AI insights** on where you can improve!")



# ---------------- JOB LISTINGS PAGE ----------------
st.session_state["user_id"] = user_id
hashed_id = hash_id(user_id)
if not user_id:
    st.title("🔒 Job Listings Dashboard")
    st.write("Please launch this dashboard from the Chrome extension to view your job listings.")
    st.write("If you have already done so, please refresh the page.")
elif page == "View Listings":
    st.title("📌 Job Listings Dashboard")
    st.write("View and manage your scraped job listings from LinkedIn!")

    if st.button("🔄 Refresh Listings"):
        st.rerun()

    st.caption(f"✅ Logged in as: **{user_id}**")

    # Fetch jobs from Supabase
    job_data = fetch_jobs(hashed_id)

    # Rename columns for proper capitalization
    job_data.rename(columns={
        "position": "Position",
        "company": "Company",
        "technical_requirements": "Technical Requirements",
        "experience": "Experience",
        "url": "URL",
        "job_id": "Job ID"
    }, inplace=True)

    if not job_data.empty:
        # Add Headers
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6 = st.columns([2, 1, 5, 4, 1, 1.5])
        with header_col1:
            st.subheader("Position")
        with header_col2:
            st.subheader("Company")
        with header_col3:
            st.subheader("Technical Requirements")
        with header_col4:
            st.subheader("Experience")
        with header_col5:
            st.subheader("Job URL")
        with header_col6:
            st.subheader("Actions")

        st.markdown("---")
        # Display job listings
        for index, row in job_data.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 5, 4, 1, 1.5])

            with col1:
                st.write(f"**{row['Position']}**")

            with col2:
                st.write(row['Company'])

            with col3:
                st.write(row['Technical Requirements'])

            with col4:
                st.write(row['Experience'])

            with col5:
                job_url = row["URL"]
                st.markdown(f"[🔗 View Job]({job_url})", unsafe_allow_html=True)

            with col6:
                job_id = row["Job ID"]
                if st.button("❌", key=job_id):
                    delete_job(job_id)
                    st.warning(f"Deleted job: {row['Position']}")
                    st.rerun()
            st.markdown("---")
    else:
        st.info("No job listings available!")


# ---------------- RESUME ANALYSIS PAGE ----------------
elif page == "Resume Analysis":
    st.title("📄 Resume Analysis")
    st.write("Upload your resume to analyze compatibility with your job listings!")
    st.caption(f"✅ Logged in as: **{user_id}**")

    # Upload Resume
    uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])

    if uploaded_file:
        st.success("✅ Resume uploaded successfully!")
        st.caption("Make sure your PDF contains text for accurate analysis. The AI will struggle with scanned images.")
        if st.button("📤 Upload & Analyze Resume"):
            with st.spinner("Analyzing resume... This may take a few seconds."):
                # Read resume contents
                resume_contents = uploaded_file.read()

                # Call API to process resume
                result = process_resume(resume_contents, user_id)

                if result:
                    # Convert API response into a DataFrame
                    analysis_data = pd.DataFrame(result)  

                    # Ensure correct column ordering & sorting by similarity score
                    analysis_data = analysis_data[["position", "company", "similarity_score", "compatible_skills", "missing_skills"]]
                    analysis_data = analysis_data.sort_values(by="similarity_score", ascending=False)

                    # Display Table Headers
                    st.subheader("📊 Resume Compatibility Results")
                    st.write("Jobs sorted by highest similarity score:")

                    header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([1, 1, 2, 3, 3])
                    with header_col1:
                        st.subheader("Position")
                    with header_col2:
                        st.subheader("Company")
                    with header_col3:
                        tooltip = '''# How is this score calculated?
            
The similarity score is calculated using:
- BERT Similarity (Semantic meaning)
- TF-IDF Similarity (Keyword matching)
- Skill Compatibility Ratio

A higher score means a better job fit.
'''
                        st.subheader("Similarity Score", help=tooltip)
                        

                    with header_col4:
                        st.subheader("Compatible Skills")
                    with header_col5:
                        st.subheader("Missing Skills")

                    # Display each job listing in structured columns
                    for index, row in analysis_data.iterrows():
                        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 3, 3])

                        with col1:
                            st.write(f"**{row['position']}**")

                        with col2:
                            st.write(row['company'])

                        with col3:
                            similarity_score = f"{row['similarity_score']:.2%}"  # Convert to percentage
                            st.write(f"🟢 {similarity_score}")  # Add emoji for visual effect

                        with col4:
                            compatible_skills = row["compatible_skills"] if row["compatible_skills"] else "None"
                            st.write(compatible_skills)

                        with col5:
                            missing_skills = row["missing_skills"] if row["missing_skills"] else "None"
                            st.write(missing_skills)
                        
                        st.markdown("---")

                else:
                    st.error("❌ Failed to process resume. Please try again.")

    st.markdown("---")
    st.caption("Insights are generated using Gemini-2.0-Flash. Errors may occur due to the limitations and probabilistic nature of GenAI models.")
