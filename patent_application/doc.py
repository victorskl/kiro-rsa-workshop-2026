import logging
import base64
import json
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError
import streamlit as st

# ── Logging ───────────────────────────────────────────────────────────────────
# Structured server-side logging. Exceptions are logged here; the UI
# receives only a generic message (RISK-06).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Patent Classifier",
    page_icon="📄",
    layout="centered",
)

# ── Constants ──────────────────────────────────────────────────────────────────
# Claude Haiku 4.5 US geo cross-region inference profile (us-east-1)
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
AWS_REGION = "us-east-1"

# SSM parameter name for the system prompt (RISK-08).
# Falls back to the local prompt_config.txt when SSM is unavailable
# (e.g., local development without an instance role).
SSM_PROMPT_PARAM = "/patent-classifier/system-prompt"
PROMPT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "prompt_config.txt")

# File upload limits (RISK-02)
MAX_PDF_BYTES = 10 * 1024 * 1024   # 10 MB
PDF_MAGIC_BYTES = b"%PDF-"          # ISO 32000 magic bytes


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_system_prompt() -> str:
    """
    Load the system prompt from SSM Parameter Store (RISK-08).

    The parameter is stored as a plain String (not SecureString) because the
    prompt is not a secret — it is a configuration value. Storing it in SSM
    means it can be updated without rebuilding the container image, and the
    parameter value is never baked into a Docker layer.

    Falls back to the local prompt_config.txt if SSM is unreachable so that
    local development still works without an AWS session.
    """
    try:
        ssm = boto3.client("ssm", region_name=AWS_REGION)
        response = ssm.get_parameter(Name=SSM_PROMPT_PARAM, WithDecryption=False)
        prompt = response["Parameter"]["Value"].strip()
        logger.info("System prompt loaded from SSM parameter %s", SSM_PROMPT_PARAM)
        return prompt
    except (BotoCoreError, ClientError) as exc:
        logger.warning(
            "Could not load system prompt from SSM (%s); falling back to local file.",
            exc,
        )

    # Local fallback
    with open(PROMPT_CONFIG_PATH, "r", encoding="utf-8") as fh:
        return fh.read().strip()


def validate_pdf(data: bytes) -> str | None:
    """
    Server-side PDF validation (RISK-02).

    Returns an error message string if validation fails, or None if the file
    is acceptable.  Two checks are applied:

    1. Size cap — files larger than MAX_PDF_BYTES are rejected before any
       processing.  This prevents cost-based abuse of the Bedrock endpoint
       and avoids memory pressure from zip bombs.

    2. Magic-byte check — verifies that the first five bytes match the PDF
       file signature (%PDF-).  Streamlit's ``type=["pdf"]`` filter is
       enforced by the browser only; a renamed file with a .pdf extension
       can bypass it.  Checking magic bytes on the server side ensures the
       content is actually a PDF before it is forwarded to Bedrock.
    """
    if len(data) > MAX_PDF_BYTES:
        size_mb = len(data) / (1024 * 1024)
        return f"File is {size_mb:.1f} MB, which exceeds the 10 MB limit."

    if not data.startswith(PDF_MAGIC_BYTES):
        return (
            "The uploaded file does not appear to be a valid PDF "
            "(magic bytes check failed)."
        )

    return None


def classify_patent(pdf_bytes: bytes, system_prompt: str) -> str:
    """
    Send the PDF to Amazon Bedrock (Claude) and return the classification text.

    Uses the instance role for auth — no explicit credentials needed.

    Note on cross-region routing (RISK-03): the US geo inference profile
    (us.*) keeps processing within US AWS regions (us-east-1 / us-west-2).
    Input and output data are not stored in destination regions; however,
    temporary in-flight routing means the document may be processed in
    us-west-2 as well as us-east-1.  See SECURITY_RISKS.md § RISK-03.
    """
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Please classify this patent application according to the IPC.",
                    },
                ],
            }
        ],
        "max_tokens": 2048,
    }

    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(request_body),
        contentType="application/json",
        accept="application/json",
    )

    response_body = json.loads(response["body"].read())
    return response_body["content"][0]["text"]


# ── UI ─────────────────────────────────────────────────────────────────────────
st.title("📄 Patent Classifier")
st.write(
    "Upload a patent application PDF and click **Classify** to receive an "
    "IPC classification powered by Amazon Bedrock."
)

# Cross-region data routing disclosure (RISK-03)
st.info(
    "⚠️ **Data routing notice:** Uploaded documents are processed by Amazon "
    "Bedrock using a US geo cross-region inference profile. Your document may "
    "be processed in any AWS US region (us-east-1 or us-west-2). Data is "
    "encrypted in transit and is not stored in destination regions. "
    "Do not upload documents that must remain in a single AWS region, "
    "or that contain Protected Health Information (PHI) without a signed "
    "AWS Business Associate Agreement (BAA).",
    icon="🔒",
)

uploaded_file = st.file_uploader("Upload patent PDF", type=["pdf"])

if uploaded_file is not None:
    st.success(f"File uploaded: **{uploaded_file.name}**")

    if st.button("Classify", type="primary"):
        pdf_bytes = uploaded_file.read()

        # Server-side file validation (RISK-02)
        validation_error = validate_pdf(pdf_bytes)
        if validation_error:
            st.error(f"Invalid file: {validation_error}")
        else:
            with st.spinner("Analysing patent and generating IPC classification…"):
                try:
                    system_prompt = load_system_prompt()
                    result = classify_patent(pdf_bytes, system_prompt)
                    st.subheader("Classification Result")
                    st.markdown(result)
                except (BotoCoreError, ClientError):
                    # Full traceback logged server-side; only a generic
                    # message is shown to the user (RISK-06).
                    logger.exception("Bedrock invocation failed for file %s", uploaded_file.name)
                    st.error(
                        "Classification failed due to a service error. "
                        "Please try again. If the problem persists, contact support."
                    )
                except Exception:  # noqa: BLE001
                    logger.exception("Unexpected error classifying file %s", uploaded_file.name)
                    st.error(
                        "An unexpected error occurred. "
                        "Please try again or contact support."
                    )
