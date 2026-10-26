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

# Bulletproof GCP / Vertex AI Credential & Private Key Sanitization
if "GOOGLE_CLOUD_PROJECT" in st.secrets:
  os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
  os.environ["GOOGLE_CLOUD_PROJECT"] = st.secrets["GOOGLE_CLOUD_PROJECT"]
  os.environ["GOOGLE_CLOUD_LOCATION"] = st.secrets.get(
      "GOOGLE_CLOUD_LOCATION", "us-central1"
  )

  # Handle both TOML table format and raw JSON string format
  try:
    if "gcp_service_account" in st.secrets:
      sa_info = dict(st.secrets["gcp_service_account"])
    elif "GCP_SERVICE_ACCOUNT_JSON" in st.secrets:
      raw_secret = st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
      sa_info = (
          raw_secret if isinstance(raw_secret, dict) else json.loads(raw_secret)
      )
    else:
      sa_info = None

    if sa_info:
      # Explicitly fix private key newline formatting for cryptography backend
      if "private_key" in sa_info:
        pk = sa_info["private_key"]
        # Replace literal \\n or escaped variants with actual newlines
        pk = pk.replace("\\\\n", "\n").replace("\\n", "\n")
        if not pk.startswith("-----BEGIN PRIVATE KEY-----"):
          pk = "-----BEGIN PRIVATE KEY-----\n" + pk.strip()
        if not pk.endswith("-----END PRIVATE KEY-----"):
          pk = pk.strip() + "\n-----END PRIVATE KEY-----\n"
        sa_info["private_key"] = pk

      cred_path = "/tmp/service_account.json"
      with open(cred_path, "w") as f:
        json.dump(sa_info, f)
      os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
  except Exception as e:
    st.error(f"Credential configuration error: {e}")
