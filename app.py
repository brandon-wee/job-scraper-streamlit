import streamlit as st
from supabase import create_client, Client
import pandas as pd
import os
from dotenv import load_dotenv
import hmac, hashlib

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

st.set_page_config(page_title="Job Listings Dashboard", page_icon="📌", layout="wide")

query_params = st.query_params
user_id = query_params.get("user_id")
hashed_id = hash_id(user_id)

# Streamlit UI
st.title("📌 Job Listings Dashboard")

st.write("View and manage your scraped job listings from LinkedIn!")

if st.button("🔄"):
    st.rerun()

if user_id:
    st.session_state["user_id"] = user_id  # Store user ID in session state
    st.write(f"✅ Logged in as: **{user_id}**")
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
    else:
        st.info("No job listings available!")
else:
    st.write("⚠️ No user ID provided. Please launch this dashboard from the Chrome extension.")


