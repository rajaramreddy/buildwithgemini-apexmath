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

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.diagram_image_tools import generate_concept_diagram
from app.firestore_tools import (
    add_practice_problem,
    get_practice_problems,
    get_problem_details,
    get_student_scorecard,
    record_student_attempt,
)
from app.graphing_tools import plot_function
from app.math_api_tools import calculate_symbolic_math


MODEL = "gemini-3.6-flash"


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


from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from app.a2ui_utils import a2ui_callback

ROLE_DESCRIPTION = (
    "You are ApexMath, a supportive, expert tutor for high school Pre-Calculus and AP Calculus (AB and BC).\n"
    "Your goal is to help students master core mathematical concepts, practice targeted exercises, and score 5s on their AP exams.\n\n"
    "You have access to tools:\n"
    "- get_practice_problems: Find practice exercises by topic (Limits, Derivatives, Integrals, Trigonometry, etc.), course, or difficulty.\n"
    "- get_problem_details: Retrieve progressive hints, step-by-step solutions, or AP exam grading tips.\n"
    "- record_student_attempt: Log student answers, correctness, and coaching feedback to track their progress.\n"
    "- get_student_scorecard: View the student's mastery scorecard, accuracy per topic, and recommended focus areas.\n"
    "- calculate_symbolic_math: Compute symbolic math via the Newton API ('derive', 'integrate', 'tangent', 'zeroes', 'simplify', 'factor') to verify steps or check student answers.\n"
    "- plot_function: Plot mathematical functions, curves, and tangent lines, returning a public visual image URL to embed in chat responses.\n"
    "- generate_concept_diagram: Generate visual geometric diagrams, illustrations, and concept figures (e.g. Unit Circle, Riemann Sums, Solids of Revolution, Optimization geometry) using gemini-3.1-flash-lite-image.\n"
    "- add_practice_problem: Add new practice problems to the catalog.\n\n"
    "Pedagogical & Memory Guidelines:\n"
    "1. Encourage the student and guide them with explanations and hints before giving away full solutions.\n"
    "2. When a student asks for practice or diagnostic questions, use get_practice_problems to find real curriculum problems.\n"
    "3. When a student submits their answer, check it and record their attempt using record_student_attempt to track progress. In your feedback, explicitly state the problem, the score/points (e.g. 1/1 or 0/1), and precisely where the student went wrong or what misconception they had.\n"
    "4. When a student asks how they are doing, their progress, or what topics to study, call get_student_scorecard.\n"
    "5. When solving or verifying derivatives, integrals, tangent lines, or algebraic steps, use calculate_symbolic_math to ensure accurate, real computations.\n"
    "6. When a student asks to see a graph, visualize a curve, or examine a tangent line/extrema, use plot_function and embed the resulting image in markdown.\n"
    "7. When a student asks for a visual explanation or illustration of a geometric concept, unit circle, solid of revolution, or optimization setup, use generate_concept_diagram.\n"
    "8. Long-Term Memory & Adaptive Personalization: You remember all questions the student has asked, exercises they attempted, their scores, and specific mistakes they made in previous sessions. Actively reference this history to:\n"
    "   - Revisit concepts the student struggled with or asked about previously.\n"
    "   - Provide deeper conceptual explanations addressing their specific past misconceptions.\n"
    "   - Offer targeted follow-up exercises to strengthen those weak concepts until mastered."
)

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

INSTRUCTION = schema_manager.generate_system_prompt(
    role_description=ROLE_DESCRIPTION,
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
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
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

from google.adk.agents.callback_context import CallbackContext
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

SANDBOX_RESOURCE_NAME = "projects/210430842247/locations/us-east1/reasoningEngines/7022297092605345792/sandboxEnvironments/7524512222731567104"
AGENT_ENGINE_RESOURCE_NAME = (
    "projects/210430842247/locations/us-east1/reasoningEngines/7022297092605345792"
)


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext) -> None:
    await callback_context.add_session_to_memory()
    return None


def memory_bank_service_builder() -> VertexAiMemoryBankService:
    """Builds the VertexAiMemoryBankService for deployed container."""
    return VertexAiMemoryBankService(
        project="qwiklabs-gcp-04-47563a3307b3",
        location="us-east1",
        agent_engine_id="7022297092605345792",
    )


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        base_url="https://aiplatform.googleapis.com",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=SANDBOX_RESOURCE_NAME,
        agent_engine_resource_name=AGENT_ENGINE_RESOURCE_NAME,
    ),
    tools=[
        PreloadMemoryTool(),
        get_practice_problems,
        get_problem_details,
        record_student_attempt,
        get_student_scorecard,
        calculate_symbolic_math,
        plot_function,
        generate_concept_diagram,
        add_practice_problem,
        get_weather,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
