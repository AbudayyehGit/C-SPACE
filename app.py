import collections
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
    "Upload your raw Google Takeout `.zip` export and your GCP Service Account"
    " JSON key to process your entire chat archive using your $300 GCP"
    " credits."
)

# Sidebar Configuration for GCP Credentials (Bypasses TOML Secrets bugs)
st.sidebar.header("🔑 GCP & Vertex AI Configuration")
project_id_input = st.sidebar.text_input(
    "GCP Project ID",
    value=(
        st.secrets["GOOGLE_CLOUD_PROJECT"]
        if "GOOGLE_CLOUD_PROJECT" in st.secrets
        else ""
    ),
    placeholder="e.g. my-cspace-project",
)
location_input = st.sidebar.text_input(
    "GCP Region / Location", value="us-central1"
)

sa_file = st.sidebar.file_uploader(
    "Upload Service Account JSON Key",
    type=["json"],
    help="Upload your downloaded Google Cloud Service Account JSON file here.",
)

# Configure Environment Variables
if project_id_input:
  os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
  os.environ["GOOGLE_CLOUD_PROJECT"] = project_id_input
  os.environ["GOOGLE_CLOUD_LOCATION"] = location_input

  if sa_file is not None:
    try:
      cred_path = "/tmp/service_account.json"
      file_bytes = sa_file.read()
      sa_info = json.loads(file_bytes.decode("utf-8"))
      with open(cred_path, "wb") as f:
        f.write(file_bytes)
      os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
      st.sidebar.success(
          "✅ Service Account loaded successfully from uploaded file!"
      )
    except Exception as e:
      st.sidebar.error(f"Invalid JSON file: {e}")

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

# Initialize Session State for persistence across interactions
if "processed_artifacts" not in st.session_state:
  st.session_state["processed_artifacts"] = []

# Render cached results if available
if st.session_state["processed_artifacts"]:
  st.success(
      "✨ Loaded cached C-SPACE artifacts from session state. No API re-run"
      " required!"
  )
  processed_artifacts = st.session_state["processed_artifacts"]

  # Automatically group artifacts by destination container
  containers = collections.defaultdict(list)
  for art in processed_artifacts:
    containers[art["destination"]].append(art)

  st.subheader(
      "📦 Automated C-SPACE Container Packaging & Master Prompt Output"
  )
  st.markdown(
      f"Your {len(processed_artifacts)} chat threads have been successfully"
      " grouped into existing ecosystem notebooks and newly proposed container"
      " categories."
  )

  # Generate Master Containerized Text Payload for Gemini Ingestion
  master_payload_lines = [
      "You are the C-SPACE Master Ecosystem Ingestion Engine.",
      (
          "Review the following pre-distilled chat digests, categorized by"
          " their target container (existing notebooks or new proposed"
          " containers). Ingest and establish these containers accordingly:"
      ),
      "=" * 50,
  ]
  for dest_name, arts in containers.items():
    master_payload_lines.append(f"\n# CONTAINER: {dest_name}")
    master_payload_lines.append(
        f"--- Contains {len(arts)} distilled chat digests ---"
    )
    for art in arts:
      master_payload_lines.append(f"\n## Source: {art['source_file']}")
      master_payload_lines.append(art["content"])
      master_payload_lines.append("\n" + ("-" * 30))

  full_master_text = "\n".join(master_payload_lines)

  st.text_area(
      "📋 Master Containerized Prompt Output (Copy and feed directly into"
      " Gemini):",
      value=full_master_text,
      height=300,
  )

  # Build Master Containerized ZIP in memory
  container_zip_buffer = io.BytesIO()
  with zipfile.ZipFile(
      container_zip_buffer, "w", zipfile.ZIP_DEFLATED
  ) as zip_out:
    for dest_name, arts in containers.items():
      if dest_name.startswith("CREATE_NEW:"):
        raw_title = dest_name.replace("CREATE_NEW:", "").strip()
        clean_title = (
            raw_title.split("-")[0].replace("/", "_").replace(":", "").strip()
        )
        safe_folder_name = f"✨_NEW_NOTEBOOK_{clean_title}"
      else:
        safe_folder_name = dest_name.replace("/", "_").strip()

      for art in arts:
        file_name = f"{safe_folder_name}/Chat_{art['thread_id']}_Digest.md"
        zip_out.writestr(file_name, art["content"])

  container_zip_buffer.seek(0)
  col1, col2 = st.columns(2)
  with col1:
    st.download_button(
        label="📥 Download Master Containerized ZIP (Sorted Folders)",
        data=container_zip_buffer,
        file_name="C-SPACE_Containerized_Archive.zip",
        mime="application/zip",
    )
  with col2:
    st.download_button(
        label="📥 Download Master Prompt Payload (.txt)",
        data=full_master_text,
        file_name="C-SPACE_Master_Containerized_Prompt.txt",
        mime="text/plain",
    )

  if st.button("🔄 Clear Cache & Reset Pipeline"):
    st.session_state["processed_artifacts"] = []
    st.rerun()

  st.markdown("---")
  st.subheader("🗂️ Inspect Individual Container Allocations")
  for dest_name, arts in containers.items():
    is_new = dest_name.startswith("CREATE_NEW:")
    badge = (
        "🆕 **New Container Required**"
        if is_new
        else "📂 **Existing Ecosystem Notebook**"
    )

    with st.expander(
        f"Container: {dest_name} ({len(arts)} chat digests assigned)"
    ):
      st.markdown(badge)
      for art in arts:
        st.markdown(f"**Source:** {art['source_file']}")
        st.markdown(art["content"])
        st.markdown("---")

else:
  uploaded_file = st.file_uploader(
      "Upload Google Takeout ZIP Archive (.zip)", type=["zip"]
  )
  is_configured = "GOOGLE_CLOUD_PROJECT" in os.environ and os.path.exists(
      os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
  )

  if uploaded_file and is_configured:
    if st.button("🚀 Execute Direct ZIP C-SPACE Protocol"):
      with st.status(
          "Unpacking ZIP and processing chat transcripts via Vertex AI...",
          expanded=True,
      ) as status:
        st.write(
            "📂 Unpacking Google Takeout ZIP archive and scanning all files..."
        )
        chat_transcripts = []

        try:
          with zipfile.ZipFile(io.BytesIO(uploaded_file.read())) as z:
            for filename in z.namelist():
              if filename.endswith(
                  (".json", ".html")
              ) and not filename.startswith("__MACOSX"):
                with z.open(filename) as f:
                  content_bytes = f.read()
                  if filename.endswith(".json"):
                    try:
                      data = json.loads(
                          content_bytes.decode("utf-8", errors="ignore")
                      )
                      if isinstance(data, list):
                        for idx_item, item in enumerate(data):
                          text_parts = []
                          if isinstance(item, dict):
                            for k, v in item.items():
                              if isinstance(v, str) and len(v) > 10:
                                text_parts.append(v)
                              elif isinstance(v, list):
                                for sub in v:
                                  if isinstance(sub, dict):
                                    for sk, sv in sub.items():
                                      if isinstance(sv, str) and len(sv) > 10:
                                        text_parts.append(sv)
                          if text_parts:
                            combined = "\n".join(text_parts)
                            if len(combined) > 50:
                              chat_transcripts.append({
                                  "source": f"{filename} (#{idx_item + 1})",
                                  "content": combined,
                              })
                      elif isinstance(data, dict):
                        chat_str = json.dumps(data, ensure_ascii=False)
                        if len(chat_str) > 50:
                          chat_transcripts.append(
                              {"source": filename, "content": chat_str}
                          )
                    except Exception:
                      pass
                  elif filename.endswith(".html"):
                    try:
                      soup = BeautifulSoup(content_bytes, "html.parser")
                      text_content = soup.get_text(separator="\n", strip=True)
                      if len(text_content) > 50:
                        chat_transcripts.append(
                            {"source": filename, "content": text_content}
                        )
                    except Exception:
                      pass
        except Exception as e:
          st.error(f"Failed to unpack or read ZIP archive: {e}")
          st.stop()

        if not chat_transcripts:
          st.warning(
              "⚠️ No valid chat records were found inside this ZIP archive."
          )
          st.stop()

        st.write(
            f"Found {len(chat_transcripts)} valid chat records. Initializing"
            " Vertex AI model client..."
        )
        client = genai.Client()

        processed_artifacts = []

        for idx, chat_obj in enumerate(chat_transcripts):
          st.write(
              f"✂️ Processing Record #{idx + 1} of {len(chat_transcripts)}"
              f" ({chat_obj['source']}): Distilling and organizing..."
          )
          distillation_prompt = (
              "You are the C-SPACE Lifecycle Engine. Read the following raw"
              " chat transcript text, delete and strip all transient"
              " debugging, repetition, pleasantries, and unuseful material."
              " Organize the remaining high-value information logically into a"
              " clean, version-controlled Markdown architecture digest (e.g.,"
              f" [Topic]_Digest_v1.0.md).\n\nRaw Transcript Text:\n{chat_obj['content']}"
          )

          response = client.models.generate_content(
              model="gemini-2.5-flash", contents=distillation_prompt
          )
          distilled_content = response.text

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

        # Save to session state
        st.session_state["processed_artifacts"] = processed_artifacts

        status.update(
            label="[ZIP C-SPACE ROUTING COMPLETE]",
            state="complete",
            expanded=False,
        )
      st.rerun()

  elif uploaded_file and not is_configured:
    st.warning(
        "⚠️ Please enter your **GCP Project ID** and upload your **Service"
        " Account JSON Key** in the sidebar to run the pipeline using your $300"
        " GCP credits."
    )
