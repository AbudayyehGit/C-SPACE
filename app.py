import json
import os
from google import genai
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="C-SPACE Taxonomic Routing & Lifecycle Pipeline",
    page_icon="🧹",
    layout="wide",
)

st.title("🧹 C-SPACE Taxonomic Chat Lifecycle & Routing Pipeline")
st.markdown(
    "Automate your Google Takeout Gemini chat export: *Access ➔ Read ➔ Strip"
    " Fluff ➔ Taxonomical Routing (Route to Existing Notebook or Create New)"
    " ➔ Package for Purge*."
)

# Handle GCP / Vertex AI Credentials from Streamlit Secrets (Deducts from your $300 GCP Credits)
if "GOOGLE_CLOUD_PROJECT" in st.secrets:
  os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
  os.environ["GOOGLE_CLOUD_PROJECT"] = st.secrets["GOOGLE_CLOUD_PROJECT"]
  os.environ["GOOGLE_CLOUD_LOCATION"] = st.secrets.get(
      "GOOGLE_CLOUD_LOCATION", "us-central1"
  )

  if "GCP_SERVICE_ACCOUNT_JSON" in st.secrets:
    cred_path = "/tmp/service_account.json"
    with open(cred_path, "w") as f:
      f.write(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

# Existing Ecosystem Notebook Taxonomy from Control Center
EXISTING_NOTEBOOKS = {
    "C-SPACE Knowledge Base": (
        "Master aggregation hub containing system inventories, architectural"
        " roadmaps, and lifecycle directives."
    ),
    "Peer Notebook": (
        "Web application compliance, GTM packaging, sprint backlogs, and"
        " technical documentation."
    ),
    "DxSyn 1.0": "Clinical AI platform architecture and PM deliverables.",
    "OptimumPrimers.com": (
        "Business plans, domain strategies, and landing page architecture."
    ),
    "Professional Portfolio": (
        "Systems architect career reviews and profile repositories."
    ),
    "Job Applications": (
        "Targeted job listings, resume tailoring, and interview timelines."
    ),
    "Personal Finance": "Financial planning and LA rent averages.",
    "AI Archaeology & Gibeon Research": (
        "University of Vienna doctoral roadmaps and research archives."
    ),
    "Express ISO Simulator": "El Segundo job posting details.",
    "Admin Curriculum": "Record management syllabi.",
    "AI App Builders": "App builder evaluations and alternatives.",
    "Funding Sources": "Funding targets and outreach lists.",
    "Control Center": "Active command interface.",
}

# File Uploader for Google Takeout JSON export
uploaded_file = st.file_uploader(
    "Upload Google Takeout Gemini Export (JSON)", type=["json"]
)

if uploaded_file and "GOOGLE_CLOUD_PROJECT" in os.environ:
  if st.button("🚀 Execute Taxonomic C-SPACE Protocol"):
    with st.status(
        "Executing Taxonomic Lifecycle Routing via Vertex AI...", expanded=True
    ) as status:
      # Step 1 & 2: Access & Read Chat
      st.write("📂 Step 1 & 2: Accessing and reading chat transcripts...")
      try:
        raw_data = json.load(uploaded_file)
        chats = raw_data if isinstance(raw_data, list) else [raw_data]
      except Exception as e:
        st.error(f"Failed to parse JSON export: {e}")
        st.stop()

      st.write(
          f"Found {len(chats)} chat threads. Initializing Vertex AI model"
          " client..."
      )
      client = genai.Client()

      processed_artifacts = []

      # Process a controlled batch for stability
      for idx, chat in enumerate(chats[:15]):
        chat_transcript = json.dumps(chat, ensure_ascii=False)

        # Step 3 & 4: Delete unuseful material & Organize remaining info logically
        st.write(
            f"✂️ Processing Thread #{idx + 1}: Stripping fluff and organizing..."
        )
        distillation_prompt = (
            "You are the C-SPACE Lifecycle Engine. Read the following raw chat"
            " transcript, delete and strip all transient debugging, repetition,"
            " pleasantries, and unuseful material. Organize the remaining"
            " high-value information logically into a clean, version-controlled"
            " Markdown architecture digest (e.g., [Topic]_Digest_v1.0.md)."
            f"\n\nRaw Transcript:\n{chat_transcript}"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=distillation_prompt
        )
        distilled_content = response.text

        # Step 5: Taxonomical Routing or New Notebook Creation
        st.write(
            f"🗂️ Step 5: Performing taxonomic routing for Thread #{idx + 1}..."
        )
        routing_prompt = f"""
                You are the C-SPACE Taxonomic Routing Engine. 
                Evaluate the following distilled Markdown digest and determine its proper home based on these existing ecosystem notebooks and their descriptions:
                {json.dumps(EXISTING_NOTEBOOKS, indent=2)}
                
                Rules:
                1. If the content clearly belongs in one of the existing notebooks above, output EXACTLY the notebook name.
                2. If the content does NOT fit any existing notebook taxonomically, output 'CREATE_NEW:' followed by a short, highly professional, descriptive new notebook title and a 1-sentence description.
                
                Digest Summary:
                {distilled_content[:1000]}
                """
        route_response = client.models.generate_content(
            model="gemini-2.5-flash", contents=routing_prompt
        )
        destination = route_response.text.strip()

        processed_artifacts.append({
            "thread_id": idx + 1,
            "destination": destination,
            "content": distilled_content,
        })

      # Step 6: Final Packaging Notice for Purge
      st.write(
          "🔥 Step 6: Taxonomic mapping complete. Ready for ingestion and raw"
          " chat purge."
      )
      status.update(
          label="[TAXONOMIC C-SPACE ROUTING COMPLETE]",
          state="complete",
          expanded=False,
      )

    st.success(
        "✨ Taxonomic C-SPACE pipeline successfully completed using your GCP"
        " credits! Review the routing destinations below, ingest the digests"
        " into their respective notebooks, and purge the raw standalone chats"
        " from your history[cite: 1]."
    )

    # Display results and downloadable markdown artifacts with routing indicators
    st.subheader("📦 Taxonomically Sorted C-SPACE Artifacts")
    for art in processed_artifacts:
      is_new = art["destination"].startswith("CREATE_NEW:")
      badge = (
          "🆕 **Action Required: Create New Notebook Container**"
          if is_new
          else "📂 **Existing Ecosystem Notebook Match**"
      )

      with st.expander(
          f"Thread #{art['thread_id']} ➔ Destination: {art['destination']}"
      ):
        st.markdown(badge)
        st.markdown(art["content"])
        st.download_button(
            label="Download Markdown Digest",
            data=art["content"],
            file_name=f"C-SPACE_Thread_{art['thread_id']}_Digest.md",
            mime="text/markdown",
            key=f"download_{art['thread_id']}",
        )
elif not "GOOGLE_CLOUD_PROJECT" in os.environ and uploaded_file:
  st.warning(
      "⚠️ Please configure your Google Cloud project secrets in Streamlit Cloud"
      " to draw from your $300 GCP credits."
  )
