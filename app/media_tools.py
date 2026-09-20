# Copyright 2026 Google LLC
# Media tools for image generation and Cloud Storage upload
import uuid
from google import genai
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

BUCKET_NAME = "simple-agent-media-11b4cbda191e"
PROJECT_ID = "qwiklabs-gcp-01-11b4cbda191e"


async def generate_workout_image(prompt_description: str, tool_context: ToolContext) -> str:
    """Generate a custom fitness, workout, or training gear illustration and return its public GCS URL.

    Args:
        prompt_description: Detailed description of the exercise, workout gear, or training scene to generate.
        tool_context: ADK ToolContext used to save the generated image artifact in Playground.

    Returns:
        The public HTTPS Cloud Storage URL of the generated image.
    """
    try:
        # 1. Initialize Vertex AI client for global region using gemini-3.1-flash-lite-image
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=f"High quality fitness illustration: {prompt_description}",
        )

        image_bytes = None
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    break

        if not image_bytes:
            return "Failed to generate image bytes from model response."

        # 2. Save image as an ADK session artifact
        filename = f"workout_image_{uuid.uuid4().hex[:8]}.jpg"
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 3. Upload image bytes directly to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type="image/jpeg")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return f"Successfully generated exercise illustration!\n\n![Exercise Illustration]({public_url})\n\nPublic Storage URL: {public_url}"
    except Exception as e:
        return f"Image generation error: {str(e)}"


async def generate_workout_video(prompt_description: str, tool_context: ToolContext) -> str:
    """Generate a short video demonstration for a fitness exercise, workout movement, or athletic technique using gemini-omni-flash-preview in the global region.

    Args:
        prompt_description: Detailed description of the exercise movement or workout scene to generate as a video.
        tool_context: ADK ToolContext used to save the generated video artifact in Playground.

    Returns:
        The public HTTPS Cloud Storage URL of the generated video (https://storage.googleapis.com/simple-agent-media-11b4cbda191e/<object>).
    """
    try:
        # 1. Initialize Vertex AI client for global region using gemini-omni-flash-preview
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
            http_options={"timeout": 300.0},
        )

        res = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=f"Generate a short video demonstration of: {prompt_description}",
            generation_config={"response_modalities": ["VIDEO"]},
            timeout=300.0,
        )

        video_bytes = None
        if hasattr(res, "output_video") and res.output_video:
            ov = res.output_video
            if isinstance(ov, list):
                for item in ov:
                    if hasattr(item, "inline_data") and item.inline_data and hasattr(item.inline_data, "data"):
                        video_bytes = item.inline_data.data
                        break
                    elif hasattr(item, "data") and item.data:
                        video_bytes = item.data
                        break
            elif hasattr(ov, "video_bytes") and ov.video_bytes:
                video_bytes = ov.video_bytes
            elif hasattr(ov, "data") and ov.data:
                video_bytes = ov.data
            elif hasattr(ov, "inline_data") and ov.inline_data:
                video_bytes = ov.inline_data.data if hasattr(ov.inline_data, "data") else ov.inline_data
            elif isinstance(ov, dict):
                video_bytes = ov.get("video_bytes") or ov.get("data") or (ov.get("inline_data", {}).get("data") if isinstance(ov.get("inline_data"), dict) else None)


        if not video_bytes and hasattr(res, "outputs") and res.outputs:
            for out in res.outputs:
                if hasattr(out, "part") and hasattr(out.part, "inline_data") and out.part.inline_data:
                    video_bytes = out.part.inline_data.data
                    break
                if hasattr(out, "inline_data") and out.inline_data:
                    video_bytes = out.inline_data.data
                    break
                if hasattr(out, "data") and out.data:
                    video_bytes = out.data
                    break
        elif not video_bytes and hasattr(res, "candidates") and res.candidates:
            for cand in res.candidates:
                if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                    for part in cand.content.parts:
                        if hasattr(part, "inline_data") and part.inline_data:
                            video_bytes = part.inline_data.data
                            break


        if not video_bytes:
            return "Video generation completed, but video bytes could not be extracted from response."

        filename = f"workout_video_{uuid.uuid4().hex[:8]}.mp4"

        # (1) Save video with tool_context.save_artifact
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # (2) Upload video bytes directly to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type="video/mp4")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        return f"Video generation error: {str(e)}"

