import os
import json

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from workflow.state import CreatorState

load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


def planner_agent(state: CreatorState):

    niche = state["niche"]

    # --------------------------------------------------
    # VALIDATE NICHE
    # --------------------------------------------------

    supported_niches = [
        "gardening",
        "fitness",
        "cooking"
    ]

    if niche.lower() not in supported_niches:
        raise ValueError(
            f"Unsupported niche: {niche}. "
            "Supported niches are Gardening, Fitness and Cooking."
        )

    # --------------------------------------------------
    # PLANNER PROMPT
    # --------------------------------------------------

    prompt = f"""
You are the Planner Agent for CreatorBoostAI.

Creator information:

Niche: {niche}
Platform: {state["platform"]}
Goal: {state["goal"]}

Available agents:

1. YouTube Research Agent
   - Finds successful YouTube videos.
   - Collects title, channel, publication date,
     views, likes and comments.

2. Content Strategy Agent
   - Analyzes YouTube research.
   - Identifies content patterns.
   - Recommends topics.
   - Generates video ideas.
   - Creates content direction.

Decide what work is required for this request.

For a normal new content strategy request:
- YouTube research should be required.
- Content strategy should be required.
- YouTube should be the only research source.

Do NOT use Google Trends.

Do NOT request capabilities that the current
YouTube Research Agent does not provide.

Return ONLY valid JSON in exactly this format:

{{
    "plan": [
        "Research successful YouTube videos in the selected niche",
        "Analyze the available YouTube performance data",
        "Identify content patterns and opportunities",
        "Generate a practical content strategy"
    ],
    "research_required": true,
    "research_sources": ["youtube"],
    "strategy_required": true
}}
"""

    # --------------------------------------------------
    # CALL GROQ
    # --------------------------------------------------

    response = llm.invoke(prompt)

    content = response.content.strip()

    # Remove markdown code fences if model adds them
    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    # --------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------

    try:
        decision = json.loads(content)

    except json.JSONDecodeError:

        print("\nERROR: Planner returned invalid JSON.")
        print("Raw response:")
        print(content)

        raise

    # --------------------------------------------------
    # DISPLAY PLANNER DECISION
    # --------------------------------------------------

    print("\n========== PLANNER AGENT ==========")
    print(f"Niche: {niche}")

    print("\nPLAN:")

    for task in decision["plan"]:
        print("-", task)

    print("\nResearch required:",
          decision["research_required"])

    print("Research sources:",
          decision["research_sources"])

    print("Strategy required:",
          decision["strategy_required"])

    print("===================================\n")

    # --------------------------------------------------
    # RETURN DECISION TO LANGGRAPH
    # --------------------------------------------------

    return {
        "plan": decision["plan"],
        "research_required": decision["research_required"],
        "research_sources": decision["research_sources"],
        "strategy_required": decision["strategy_required"]
    }