import base64
import uuid
from google.cloud import storage
import google.genai
from google.genai import types
from google.adk.tools import ToolContext

# Hardcode bucket name & project ID as strings per instructions
MEDIA_BUCKET_NAME = "smart-pantry-chef-media-07cb7cdcf8d2"
GCP_PROJECT_ID = "qwiklabs-gcp-02-07cb7cdcf8d2"

_genai_client = None
_storage_client = None

def _get_genai_client():
    global _genai_client
    if _genai_client is None:
        _genai_client = google.genai.Client(vertexai=True, project=GCP_PROJECT_ID, location="global")
    return _genai_client

def _get_storage_client():
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=GCP_PROJECT_ID)
    return _storage_client


async def generate_recipe_image(prompt: str, tool_context: ToolContext = None) -> dict:
    """Generates an appetizing food photograph for a dish or recipe using gemini-3.1-flash-lite-image model in global region.
    
    Saves the image artifact to Playground panel and uploads bytes directly to public Cloud Storage bucket.
    
    Args:
        prompt: Description of the food dish or recipe to generate (e.g. 'Blueberry Spinach Brain-Boost Smoothie').
        tool_context: ADK ToolContext automatically injected by the framework.
        
    Returns:
        Dictionary containing prompt, public Cloud Storage URL, and filename.
    """
    client = _get_genai_client()
    res = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=f"A high-quality, professional food photograph of: {prompt}",
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])
    )
    
    img_bytes = None
    mime_type = "image/jpeg"
    for candidate in res.candidates:
        for part in candidate.content.parts:
            if part.inline_data:
                img_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break
                
    if not img_bytes:
        return {"status": "error", "message": f"No image could be generated for prompt: {prompt}"}
        
    ext = "png" if "png" in mime_type else "jpg"
    filename = f"recipe_{uuid.uuid4().hex[:8]}.{ext}"
    
    # 1. Save artifact with tool_context for Playground Artifacts panel
    if tool_context is not None:
        try:
            artifact_part = types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as e:
            print(f"Warning: Failed to save artifact in tool_context: {e}")
            
    # 2. Upload image bytes directly to public Cloud Storage bucket (without writing local file)
    storage_client = _get_storage_client()
    bucket = storage_client.bucket(MEDIA_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(img_bytes, content_type=mime_type)
    
    public_url = f"https://storage.googleapis.com/{MEDIA_BUCKET_NAME}/{filename}"
    return {
        "status": "success",
        "prompt": prompt,
        "public_url": public_url,
        "filename": filename
    }


async def generate_recipe_video(prompt: str, tool_context: ToolContext = None) -> dict:
    """Generates a short food preparation or culinary demonstration video for a recipe or dish item using Google's Omni model (gemini-omni-flash-preview) in global region.
    
    Saves the video artifact to Playground panel and uploads video bytes directly to public Cloud Storage bucket.
    
    Args:
        prompt: Description of the food dish, recipe step, or culinary presentation to generate as a video (e.g. 'Searing salmon fillet with olive oil and herbs').
        tool_context: ADK ToolContext automatically injected by the framework.
        
    Returns:
        Dictionary containing prompt, public Cloud Storage URL, and filename.
    """
    client = _get_genai_client()
    video_bytes = None
    mime_type = "video/mp4"
    
    # Primary: Call Interactions API (gemini-omni-flash-preview in global region)
    try:
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=f"A short culinary demonstration video showing: {prompt}"
        )
        
        # 1. Check direct output_video dictionary/object
        d = interaction.model_dump(mode="python") if hasattr(interaction, "model_dump") else {}
        vid = d.get("output_video") or {}
        if isinstance(vid, dict) and vid.get("data"):
            raw_data = vid.get("data")
            mime_type = vid.get("mime_type") or mime_type
            if isinstance(raw_data, str):
                video_bytes = base64.b64decode(raw_data)
            elif isinstance(raw_data, bytes):
                video_bytes = raw_data
                
        # 2. Fallback to items list if output_video was not populated
        if not video_bytes:
            items = d.get("outputs") or d.get("content") or getattr(interaction, "outputs", None) or getattr(interaction, "content", None) or []
            for item in items:
                if isinstance(item, dict):
                    data = item.get("data") or item.get("bytes")
                    if not data and isinstance(item.get("inline_data"), dict):
                        data = item["inline_data"].get("data")
                    if data:
                        video_bytes = base64.b64decode(data) if isinstance(data, str) else bytes(data)
                        mime_type = item.get("mime_type") or (item.get("inline_data") or {}).get("mime_type") or "video/mp4"
                        break
                else:
                    data = getattr(item, "data", None) or getattr(item, "bytes", None)
                    if not data and hasattr(item, "inline_data"):
                        data = getattr(item.inline_data, "data", None)
                    if data:
                        video_bytes = base64.b64decode(data) if isinstance(data, str) else bytes(data)
                        mtype = getattr(item, "mime_type", None)
                        if not mtype and hasattr(item, "inline_data"):
                            mtype = getattr(item.inline_data, "mime_type", None)
                        if mtype:
                            mime_type = mtype
                        break
    except Exception as e:
        print(f"Notice: client.interactions.create failed: {e}")
        
    # Secondary: Fallback to generate_content if supported
    if not video_bytes:
        try:
            res = client.models.generate_content(
                model="gemini-omni-flash-preview",
                contents=f"A short culinary demonstration video showing: {prompt}",
                config=types.GenerateContentConfig(response_modalities=["VIDEO", "TEXT"])
            )
            for candidate in res.candidates:
                for part in candidate.content.parts:
                    if part.inline_data:
                        video_bytes = part.inline_data.data
                        if part.inline_data.mime_type:
                            mime_type = part.inline_data.mime_type
                        break
        except Exception as e:
            print(f"Notice: client.models.generate_content fallback failed: {e}")
            
    if not video_bytes:
        return {"status": "error", "message": f"No video could be generated for prompt: {prompt}"}
        
    ext = "webm" if "webm" in mime_type else "mp4"
    filename = f"recipe_video_{uuid.uuid4().hex[:8]}.{ext}"
    
    # 1. Save artifact with tool_context for Playground Artifacts panel
    if tool_context is not None:
        try:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as e:
            print(f"Warning: Failed to save video artifact in tool_context: {e}")
            
    # 2. Upload video bytes directly to public Cloud Storage bucket (without writing local file)
    storage_client = _get_storage_client()
    bucket = storage_client.bucket(MEDIA_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)
    
    public_url = f"https://storage.googleapis.com/{MEDIA_BUCKET_NAME}/{filename}"
    return {
        "status": "success",
        "prompt": prompt,
        "public_url": public_url,
        "filename": filename
    }


