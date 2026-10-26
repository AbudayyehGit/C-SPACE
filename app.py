import io
import json
import os
import zipfile
from bs4 import BeautifulSoup
from google import genai
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="C-SPACE ZIP Takeout Pipeline", page_icon="🧹", layout="wide"
)

st.title("🧹 C-SPACE Direct ZIP Takeout Lifecycle & Routing Pipeline")
st.markdown(
    "Upload your raw Google Takeout `.zip` export directly. The pipeline"
    " unpacks your chat history, strips fluff, routes taxonomically, and"
    " prepares your Markdown digests."
)

# Robust GCP / Vertex AI Credentials & Private Key Sanitization from Streamlit Secrets
if "GOOGLE_CLOUD_PROJECT" in st.secrets:
  os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
  os.environ["GOOGLE_CLOUD_PROJECT"] = st.secrets["GOOGLE_CLOUD_PROJECT"]
  os.environ["GOOGLE_CLOUD_LOCATION"] = st.secrets.get(
      "GOOGLE_CLOUD_LOCATION", "us-central1"
  )

  if "GCP_SERVICE_ACCOUNT_JSON" in st.secrets:
    cred_path = "/tmp/service_account.json"
    raw_secret = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]

    try:
      sa_info = (
          raw_secret if isinstance(raw_secret, dict) else json.loads(raw_secret)
      )
    except Exception:
      cleaned_secret = (
          raw_secret.strip().replace("\n", "\\n").replace("\\\\n", "\\n")
      )
      sa_info = json.loads(cleaned_secret)

    if "private_key" in sa_info:
      sa_info["private_key"] = (
          sa_info["private_key"]
          .replace("\\n", "\n")
          .replace('"', "")
          .strip()
      )
      if "BEGIN PRIVATE KEY" in sa_info["private_key"] and not sa_info[
          "private_key"
      ].startswith("-----BEGIN PRIVATE KEY-----\n"):
        sa_info["private_key"] = (
            sa_info["private_key"]
            .replace("-----BEGIN PRIVATE KEY-----", "-----BEGIN PRIVATE KEY-----\n")
            .replace("-----END PRIVATE KEY-----", "\n-----END PRIVATE KEY-----")
        )

    with open(cred_path, "w") as f:
      json.dump(sa_info, f)

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

# Existing Ecosystem Notebook Taxonomy
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

# Direct ZIP File Uploader
uploaded_file = st.file_uploader(
    "Upload Google Takeout ZIP Archive", type=["zip"]
)

if uploaded_file and "GOOGLE_CLOUD_PROJECT" in os.environ:
  if st.button("🚀 Execute Direct ZIP C-SPACE Protocol"):
    with st.status(
        "Unpacking ZIP and processing chat transcripts via Vertex AI...",
        expanded=True,
    ) as status:
      st.write("📂 Unpacking Google Takeout ZIP archive in memory...")
      chat_transcripts = []

      try:
        with zipfile.ZipFile(io.BytesIO(uploaded_file.read())) as z:
          for filename in z.namelist():
            if filename.endswith(".html") and (
                "Gemini" in filename or "chats" in filename.lower()
            ):
              with z.open(filename) as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                text_content = soup.get_text(separator="\n", strip=True)
                if len(text_content) > 50:
                  chat_transcripts.append(
                      {"source": filename, "content": text_content}
                  )
            elif filename.endswith(".json") and (
                "Gemini" in filename or "chats" in filename.lower()
            ):
              with z.open(filename) as f:
                try:
                  data = json.load(f)
                  chat_str = json.dumps(data, ensure_ascii=False)
                  if len(chat_str) > 50:
                    chat_transcripts.append(
                        {"source": filename, "content": chat_str}
                    )
                except Exception:
                  pass
      except Exception as e:
        st.error(f"Failed to unpack or read ZIP archive: {e}")
        st.stop()

      if not chat_transcripts:
        st.warning(
            "⚠️ No valid Gemini chat files (.html or .json) were found inside"
            " this ZIP archive. Please verify it's the correct Takeout export."
        )
        st.stop()

      st.write(
          f"Found {len(chat_transcripts)} valid chat transcripts. Initializing"
          " Vertex AI model client..."
      )
      client = genai.Client()

      processed_artifacts = []

      for idx, chat_obj in enumerate(chat_transcripts[:15]):
        st.write(
            f"✂️ Processing Chat #{idx + 1} ({chat_obj['source']}): Stripping"
            " fluff and organizing..."
        )
        distillation_prompt = (
            "You are the C-SPACE Lifecycle Engine. Read the following raw chat"
            " transcript text, delete and strip all transient debugging,"
            " repetition, pleasantries, and unuseful material. Organize the"
            " remaining high-value information logically into a clean,"
            " version-controlled Markdown architecture digest (e.g.,"
            f" [Topic]_Digest_v1.0.md).\n\nRaw Transcript Text:\n{chat_obj['content']}"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=distillation_prompt
        )
        distilled_content = response.text

        st.write(
            f"🗂️ Step 5: Performing taxonomic routing for Chat #{idx + 1}..."
        )
        routing_prompt = f"""
                You are the C-SPACE Taxonomic Routing Engine. 
                Evaluate the following distilled Markdown digest and determine its proper home based on these existing ecosystem notebooks and their descriptions:
                {str(EXISTING_NOTEBOOKS)}
                
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
            "source_file": chat_obj["source"],
            "destination": destination,
            "content": distilled_content,
        })

      status.update(
          label="[ZIP C-SPACE ROUTING COMPLETE]",
          state="complete",
          expanded=False,
      )

    st.success(
        "✨ ZIP C-SPACE pipeline successfully completed using your GCP"
        " credits! Review the routing destinations below, ingest the digests"
        " into their respective notebooks, and purge the raw standalone chats"
        " from your history."
    )

    st.subheader("📦 Taxonomically Sorted C-SPACE Artifacts")
    for art in processed_artifacts:
      is_new = art["destination"].startswith("CREATE_NEW:")
      badge = (
          "🆕 **Action Required: Create New Notebook Container**"
          if is_new
          else "📂 **Existing Ecosystem Notebook Match**"
      )

      with st.expander(
          f"Chat #{art['thread_id']} ({art['source_file']}) ➔ Destination:"
          f" {art['destination']}"
      ):
        st.markdown(badge)
        st.markdown(art["content"])
        st.download_button(
            label="Download Markdown Digest",
            data=art["content"],
            file_name=f"C-SPACE_Chat_{art['thread_id']}_Digest.md",
            mime="text/markdown",
            key=f"download_{art['thread_id']}",
        )
elif not "GOOGLE_CLOUD_PROJECT" in os.environ and uploaded_file:
  st.warning(
      "⚠️ Please configure your Google Cloud project secrets in Streamlit Cloud"
      " to draw from your $300 GCP credits."
  )
