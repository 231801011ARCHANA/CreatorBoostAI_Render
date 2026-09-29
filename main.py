from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

from evaluation import evaluate_all_niches, evaluate_generation
from workflow.creatorboost_graph import creatorboost_graph


# --------------------------------------------------
# FASTAPI APP
# --------------------------------------------------

app = FastAPI(
    title="CreatorBoostAI API",
    description="AI-powered content strategy generator",
    version="1.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# REQUEST MODEL
# --------------------------------------------------

class StrategyRequest(BaseModel):
    niche: str
    platform: str = "YouTube"
    goal: str = "Grow a new channel"

    # Optional YouTube channel URL
    channel_url: str = ""


# --------------------------------------------------
# GENERATE STRATEGY
# --------------------------------------------------

@app.post("/generate")
def generate_strategy(data: StrategyRequest):

    # --------------------------------------------------
    # INITIAL LANGGRAPH STATE
    # --------------------------------------------------

    initial_state = {
        # User inputs
        "niche": data.niche,
        "platform": data.platform,
        "goal": data.goal,
        "channel_url": data.channel_url,

        # Planner Agent
        "plan": [],
        "research_required": False,
        "research_sources": [],
        "strategy_required": False,

        # YouTube Research Agent
        "youtube_results": [],
        "youtube_analysis": {},

        # Creator-specific YouTube Research
        "creator_youtube_results": [],
        "creator_youtube_analysis": {},

        # RAG Retrieval Agent
        "rag_context": [],

        # Content Strategy Agent
        "strategy": {},

        # Evaluation
        "evaluation_mode": False,
        "evaluation": {}
    }

    # --------------------------------------------------
    # START TIMER
    # --------------------------------------------------

    start_time = time.perf_counter()

    # --------------------------------------------------
    # RUN 4-AGENT CREATORBOOSTAI GRAPH
    # --------------------------------------------------

    result = creatorboost_graph.invoke(initial_state)

    # --------------------------------------------------
    # END TIMER
    # --------------------------------------------------

    execution_time_seconds = time.perf_counter() - start_time

    # --------------------------------------------------
    # EVALUATE THE GENERATED RESULT
    #
    # This does not make another YouTube/Groq call.
    # It evaluates the result already produced by the graph.
    # --------------------------------------------------

    evaluation = evaluate_generation(
        result,
        execution_time_seconds
    )

    # --------------------------------------------------
    # API RESPONSE
    # --------------------------------------------------

    return {
        # User information
        "niche": result["niche"],
        "platform": result["platform"],
        "goal": result["goal"],
        "channel_url": result.get("channel_url", ""),

        # Planner Agent
        "plan": result.get("plan", []),
        "research_required": result.get(
            "research_required",
            False
        ),
        "research_sources": result.get(
            "research_sources",
            []
        ),
        "strategy_required": result.get(
            "strategy_required",
            False
        ),

        # YouTube Research Agent
        "youtube_results": result.get(
            "youtube_results",
            []
        ),
        "youtube_analysis": result.get(
            "youtube_analysis",
            {}
        ),

        # Creator-specific YouTube Research
        "creator_youtube_results": result.get(
            "creator_youtube_results",
            []
        ),
        "creator_youtube_analysis": result.get(
            "creator_youtube_analysis",
            {}
        ),

        # RAG Retrieval Agent
        "rag_context": result.get(
            "rag_context",
            []
        ),

        # Content Strategy Agent
        "strategy": result.get(
            "strategy",
            {}
        ),

        # Evaluation
        "evaluation": evaluation
    }


# --------------------------------------------------
# EVALUATE SYSTEM
# --------------------------------------------------

@app.post("/evaluate")
def evaluate_system():

    return evaluate_all_niches()