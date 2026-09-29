from langgraph.graph import StateGraph, START, END

from workflow.state import CreatorState

from agents.planner import planner_agent
from agents.youtube_research import youtube_research_agent
from agents.rag_retrieval import rag_retrieval_agent
from agents.content_strategy import content_strategy_agent


def route_after_planner(state: CreatorState):

    if state["research_required"]:

        if "youtube" in state["research_sources"]:
            return "youtube_research"

    return "rag_retrieval"


builder = StateGraph(CreatorState)


builder.add_node(
    "planner",
    planner_agent
)

builder.add_node(
    "youtube_research",
    youtube_research_agent
)

builder.add_node(
    "rag_retrieval",
    rag_retrieval_agent
)

builder.add_node(
    "content_strategy",
    content_strategy_agent
)


builder.add_edge(
    START,
    "planner"
)


builder.add_conditional_edges(
    "planner",
    route_after_planner,
    {
        "youtube_research": "youtube_research",
        "rag_retrieval": "rag_retrieval"
    }
)


builder.add_edge(
    "youtube_research",
    "rag_retrieval"
)


builder.add_edge(
    "rag_retrieval",
    "content_strategy"
)


builder.add_edge(
    "content_strategy",
    END
)


creatorboost_graph = builder.compile()