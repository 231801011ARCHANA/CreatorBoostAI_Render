from typing import TypedDict


SUPPORTED_NICHES = [
    "gardening",
    "fitness",
    "cooking"
]


class CreatorState(TypedDict):
    niche: str
    platform: str
    goal: str
    channel_url: str

    plan: list[str]

    research_required: bool
    research_sources: list[str]
    strategy_required: bool

    youtube_results: list
    youtube_analysis: dict

    creator_youtube_results: list
    creator_youtube_analysis: dict
    rag_context: list

    strategy: dict

    evaluation_mode: bool
    evaluation: dict