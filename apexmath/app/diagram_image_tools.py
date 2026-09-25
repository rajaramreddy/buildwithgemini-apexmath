"""Math diagram and illustration generator using gemini-3.1-flash-lite-image."""

import json
import uuid

from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

# Hardcode GCP Project ID and Cloud Storage Bucket name as strings
PROJECT_ID = "qwiklabs-gcp-04-47563a3307b3"
BUCKET_NAME = "apexmath-visuals-47563a3307b3"
MODEL_ID = "gemini-3.1-flash-lite-image"
LOCATION = "global"

_genai_client = None
_storage_client = None


def get_genai_client() -> genai.Client:
    """Lazy initialize GenAI client configured for Vertex AI in global region."""
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )
    return _genai_client


def get_storage_client() -> storage.Client:
    """Lazy initialize Google Cloud Storage client."""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


async def generate_concept_diagram(
    concept: str,
    tool_context: ToolContext | None = None,
) -> str:
    """Generate a conceptual mathematical diagram or illustration for AP Calculus or Pre-Calculus concepts.

    Generates visual diagrams (e.g. Unit Circle with key angles, Solids of Revolution disc/washer method,
    Riemann sum rectangular approximations, Optimization geometry, Related Rates figures).

    The image is saved to the Playground Artifacts panel and uploaded to public Cloud Storage.

    Args:
        concept: The mathematical concept, diagram, or geometric figure to illustrate
            (e.g., 'Unit circle with 30-60-90 and 45-45-90 reference triangles',
                   'Solid of revolution formed by revolving y = sqrt(x) around the x-axis',
                   'Right and Left Riemann sum approximations under a curve').
        tool_context: Injected tool context for saving artifacts in the Agent Playground.

    Returns:
        JSON string containing the public https URL, markdown image embed, and diagram description.
    """
    client = get_genai_client()

    prompt = (
        f"A clean, professional, textbook-style mathematical illustration for AP Calculus/Pre-Calculus: {concept}. "
        "Clear geometric lines, high-contrast, labeled axes and angles, white background, educational diagram style."
    )

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=[types.Modality.TEXT, types.Modality.IMAGE],
            ),
        )

        image_bytes: bytes | None = None
        for candidate in response.candidates or []:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.inline_data and part.inline_data.data:
                        image_bytes = part.inline_data.data
                        break
            if image_bytes:
                break

        if not image_bytes:
            return json.dumps(
                {
                    "error": f"No image data returned by {MODEL_ID} for concept '{concept}'."
                }
            )

        unique_id = uuid.uuid4().hex[:10]
        filename = f"diagram_{unique_id}.png"

        # 1. Save with tool_context.save_artifact for the Playground's Artifacts panel
        if tool_context is not None:
            artifact_part = types.Part.from_bytes(
                data=image_bytes, mime_type="image/png"
            )
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload same bytes directly to public Cloud Storage (no local file written)
        storage_client = get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_path = f"diagrams/{filename}"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(image_bytes, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"

        return json.dumps(
            {
                "status": "success",
                "concept": concept,
                "public_url": public_url,
                "markdown_embed": f"![{concept}]({public_url})",
                "artifact_filename": filename,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {"error": f"Failed to generate diagram for '{concept}': {e!s}"}
        )
