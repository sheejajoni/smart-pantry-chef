# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

import json
import os

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.firestore_tools import (
    search_recipes,
    add_recipe,
    get_pantry_items,
    update_pantry_item,
    calculate_nutrition_and_glycemic_load,
    fetch_external_recipes,
)
from app.maps_tools import (
    geocode_address,
    find_nearby_places,
)
from app.image_tools import (
    generate_recipe_image,
    generate_recipe_video,
)


# Load Agent Engine / Memory Bank ID from environment variable or deployment_metadata.json
MEMORY_BANK_ID = os.environ.get("MEMORY_BANK_ID", "894375743381831680")
agent_engine_resource_name = f"projects/950304886351/locations/us-east1/reasoningEngines/{MEMORY_BANK_ID}"
deployment_metadata_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "deployment_metadata.json")
if os.path.exists(deployment_metadata_path):
    try:
        with open(deployment_metadata_path, "r") as f:
            metadata = json.load(f)
            if "remote_agent_runtime_id" in metadata:
                agent_engine_resource_name = metadata["remote_agent_runtime_id"]
                if "MEMORY_BANK_ID" not in os.environ:
                    MEMORY_BANK_ID = agent_engine_resource_name.split("/")[-1]
    except Exception as e:
        print(f"Warning: Failed to load deployment_metadata.json: {e}")

# Set Agent Engine / Memory Bank environment variables in process memory for ADK service_factory
os.environ["GOOGLE_CLOUD_AGENT_ENGINE_ID"] = MEMORY_BANK_ID
os.environ["GOOGLE_CLOUD_PROJECT"] = "qwiklabs-gcp-02-07cb7cdcf8d2"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-east1"

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        print(f"Notice: Memory Bank callback skipped ({e})")
    return None


from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are the Smart Pantry & Health-Focused Personal Chef Concierge. "
        "Your mission is to help users manage pantry ingredients, plan healthy meals "
        "tailored for controlling cholesterol & blood sugar, boosting cognitive/memory power, "
        "optimizing BMI, generating dish images, and locating nearby grocery stores for ingredients. "
        "CRITICAL ALLERGY & MEMORY INSTRUCTION: You MUST pay special attention to and remember all user "
        "food allergies, dietary restrictions, intolerances, and health preferences across conversations using your Memory Bank. "
        "Whenever a user states an allergy (e.g. peanuts, tree nuts, shellfish, dairy, gluten, soy, eggs, fish, curd, etc.), "
        "always acknowledge it, rely on PreloadMemoryTool to recall it in future sessions, and strictly exclude any recipes "
        "or ingredients containing those allergens."
    ),
    workflow_description="Analyze the user request, call necessary tools, and return structured UI surfaces when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=a2ui_instruction,
    tools=[
        PreloadMemoryTool(),
        search_recipes,
        add_recipe,
        get_pantry_items,
        update_pantry_item,
        calculate_nutrition_and_glycemic_load,
        fetch_external_recipes,
        geocode_address,
        find_nearby_places,
        generate_recipe_image,
        generate_recipe_video,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)


def memory_service_builder():
    return VertexAiMemoryBankService(
        project="qwiklabs-gcp-02-07cb7cdcf8d2",
        location="us-east1",
        agent_engine_id=MEMORY_BANK_ID,
    )


app = App(
    root_agent=root_agent,
    name="app",
)

