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
import json
import os
import urllib.request
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from app.a2ui_utils import a2ui_callback
from app.firestore_tools import add_firestore_item, get_firestore_catalog
from app.maps_tools import find_nearby_places, geocode_address
from app.media_tools import generate_workout_image, generate_workout_video
from app.rag_tools import consult_herbal_rag_corpus



async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: After each turn, send the session to Memory Bank for fact extraction."""
    await callback_context.add_session_to_memory()
    return None


def get_outdoor_workout_weather(latitude: float = 37.7749, longitude: float = -122.4194) -> str:
    """Fetch live outdoor workout weather forecast and safety recommendations from Open-Meteo API.

    Args:
        latitude: Latitude coordinate for location (default 37.7749 for San Francisco).
        longitude: Longitude coordinate for location (default -122.4194 for San Francisco).

    Returns:
        Formatted summary of live outdoor weather, temperature, wind, and workout safety advice.
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ADK-Weather-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            current = data.get("current_weather", {})
            temp_c = current.get("temperature", 0)
            temp_f = (temp_c * 9 / 5) + 32
            wind = current.get("windspeed", 0)
            code = current.get("weathercode", 0)

            condition = "Clear/Sunny" if code in (0, 1) else "Partly Cloudy" if code in (2, 3) else "Rainy/Overcast"
            safety_advice = "Great conditions for outdoor training!" if temp_f < 85 and wind < 20 else "Use caution: Stay hydrated and monitor conditions."

            return (
                f"☀️ Live Outdoor Weather Forecast ({latitude:.2f}, {longitude:.2f}):\n"
                f"- Temperature: {temp_f:.1f}°F ({temp_c:.1f}°C)\n"
                f"- Condition: {condition}\n"
                f"- Wind Speed: {wind} km/h\n"
                f"- Safety Advice: {safety_advice}"
            )
    except Exception as e:
        return f"Weather API request error for location ({latitude}, {longitude}): {str(e)}"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


def log_allergy(allergy_type: str, severity_or_notes: str = "") -> str:
    """Explicitly record and confirm a user allergy (e.g., penicillin, latex, peanuts, shellfish, gluten).

    Args:
        allergy_type: Type of allergy (e.g. 'penicillin', 'latex', 'peanuts', 'gluten').
        severity_or_notes: Notes on severity or symptoms if provided.

    Returns:
        Confirmation message that the allergy has been recorded in persistent Memory Bank.
    """
    notes = f" ({severity_or_notes})" if severity_or_notes else ""
    return f"SAFETY MEMORY LOGGED: User allergy to '{allergy_type}'{notes} has been committed to persistent Memory Bank."


def calculate_1rm_and_calories(
    weight_lifted_lbs: float,
    reps: int,
    duration_minutes: float = 30.0,
    body_weight_lbs: float = 170.0,
) -> str:
    """Calculate estimated 1-Rep Max (1RM) strength benchmarks and workout calorie burn.

    Args:
        weight_lifted_lbs: Weight lifted in pounds (e.g. 150.0).
        reps: Number of repetitions completed (e.g. 8).
        duration_minutes: Duration of workout in minutes (default 30.0).
        body_weight_lbs: Athlete body weight in pounds (default 170.0).

    Returns:
        Formatted summary of 1RM benchmark estimates and estimated calories burned.
    """
    if reps <= 0 or weight_lifted_lbs <= 0:
        return "Please provide positive numbers for weight and reps."

    # Epley formula: 1RM = weight * (1 + reps / 30)
    epley_1rm = weight_lifted_lbs * (1 + reps / 30.0)
    # Brzycki formula: 1RM = weight * (36 / (37 - reps))
    brzycki_1rm = weight_lifted_lbs * (36.0 / (37.0 - reps)) if reps < 37 else epley_1rm
    avg_1rm = (epley_1rm + brzycki_1rm) / 2.0

    # Estimated MET for weight lifting ~ 5.0 METs
    # Calories = MET * 3.5 * weight_kg / 200 * duration
    body_weight_kg = body_weight_lbs * 0.453592
    est_calories = 5.0 * 3.5 * body_weight_kg / 200.0 * duration_minutes

    return (
        f"📊 Fitness Calculation Results:\n"
        f"- Estimated 1RM (Epley): {epley_1rm:.1f} lbs\n"
        f"- Estimated 1RM (Brzycki): {brzycki_1rm:.1f} lbs\n"
        f"- Recommended 1RM Benchmark: {avg_1rm:.1f} lbs\n"
        f"- Estimated Calorie Expenditure ({duration_minutes:.0f} mins @ {body_weight_lbs:.0f} lbs): {est_calories:.0f} kcal"
    )


def fetch_wger_exercise_library(limit: int = 5, api_key_env: str = "WGER_API_KEY") -> str:
    """Fetch curated exercise routines and muscle group details from the open Wger Workout Database (public-apis).

    Args:
        limit: Number of exercise items to fetch (default 5, max 10).
        api_key_env: Optional environment variable name if an API key is configured.

    Returns:
        Formatted summary of exercises, target muscles, equipment, and instructions.
    """
    import os

    # Read optional API key from environment variable if configured
    api_key = os.environ.get(api_key_env, os.environ.get("WGER_API_KEY", ""))

    url = f"https://wger.de/api/v2/exerciseinfo/?limit={min(limit, 10)}"
    headers = {"User-Agent": "ADK-Wger-Tool/1.0"}
    if api_key:
        headers["Authorization"] = f"Token {api_key}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = data.get("results", [])
            output = [f"🏋️ Open Wger Workout Database (Top {len(results)} Exercises):\n"]
            for item in results:
                cat = item.get("category", {}).get("name", "General")
                muscles = ", ".join([m.get("name_en", m.get("name", "")) for m in item.get("muscles", [])]) or "Full Body"
                equip = ", ".join([e.get("name", "") for e in item.get("equipment", [])]) or "Bodyweight"

                # Extract English title from translations
                title = cat
                for t in item.get("translations", []):
                    if t.get("language") == 2 and t.get("name"):
                        title = t.get("name")
                        break

                output.append(f"- {title} [{cat}]\n  Target Muscles: {muscles}\n  Equipment: {equip}")

            return "\n".join(output)
    except Exception as e:
        return f"Error fetching from Wger API: {str(e)}"


a2ui_schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_prompt = a2ui_schema_manager.generate_system_prompt(
    role_description="You are a helpful AI fitness, training, health, and athletic assistant designed to provide accurate and useful information.",
    workflow_description="Analyze the request and return structured UI when appropriate.",
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


sandbox_code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name="projects/100148393249/locations/us-east1/reasoningEngines/2789120151063101440",
)


root_agent = Agent(
    name="root_agent",
    code_executor=sandbox_code_executor,
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        a2ui_prompt + "\n\n"
        "CULPEPER HERBAL RAG CORPUS:\n"
        "Use `consult_herbal_rag_corpus` to search for traditional herbal remedies, medicinal plant uses, and historical herbal knowledge from Culpeper's Complete Herbal.\n\n"
        "AI IMAGE GENERATION & PUBLIC STORAGE:\n"
        "Use `generate_workout_image` to create custom high-quality illustrations for exercises, workout gear, or athletic action scenes.\n"
        "Saves the image as a Playground Artifact and returns its public HTTPS Cloud Storage URL.\n\n"
        "AI VIDEO GENERATION & PUBLIC STORAGE:\n"
        "Use `generate_workout_video` to generate short video demonstrations for exercise items or workout movements using gemini-omni-flash-preview in the global region.\n"
        "Saves the video as a Playground Artifact and returns its public HTTPS Cloud Storage URL.\n\n"
        "GOOGLE MAPS GEOLOCATION & PLACES:\n"
        "Use `geocode_address` to convert address text into geographic coordinates (latitude and longitude).\n"
        "Use `find_nearby_places` to search for nearby facilities (e.g. gym, park, sports_complex) around coordinates.\n\n"
        "OPEN WGER EXERCISE DATABASE:\n"
        "Use `fetch_wger_exercise_library` to retrieve open exercise routines, target muscle groups, and required equipment from the Wger workout API.\n\n"
        "LIVE OUTDOOR WEATHER:\n"
        "Use `get_outdoor_workout_weather` to fetch live outdoor temperature, weather conditions, and training safety advice for given coordinates.\n\n"
        "FITNESS & STRENGTH CALCULATIONS:\n"
        "Use `calculate_1rm_and_calories` whenever the user asks for 1-Rep Max benchmarks, strength estimates, or calorie expenditure for lift sets.\n\n"
        "FIRESTORE CATALOG TOOLS:\n"
        "Use `get_firestore_catalog` to search and retrieve items from the live Firestore catalog collection.\n"
        "Use `add_firestore_item` to add new custom items to the Firestore catalog.\n\n"
        "CRITICAL ALLERGY & HEALTH SAFETY RULE:\n"
        "You remember user preferences, dietary constraints, health facts, and allergies across conversations.\n"
        "Whenever the user mentions any allergy (e.g., peanuts, penicillin, latex, shellfish, gluten, dairy), "
        "you MUST call `log_allergy` to explicitly record and acknowledge it, permanently retain it in Memory Bank, "
        "and NEVER recommend any food, medicine, or items that conflict with their recorded allergies."
    ),
    tools=[
        PreloadMemoryTool(),
        consult_herbal_rag_corpus,
        generate_workout_image,
        generate_workout_video,
        geocode_address,
        find_nearby_places,
        fetch_wger_exercise_library,
        get_outdoor_workout_weather,
        calculate_1rm_and_calories,
        get_firestore_catalog,
        add_firestore_item,
        log_allergy,
        get_weather,
        get_current_time,
    ],

    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
