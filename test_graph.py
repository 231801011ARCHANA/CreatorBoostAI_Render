from workflow.creatorboost_graph import creatorboost_graph


initial_state = {
    "niche": "Gardening",
    "platform": "YouTube",
    "goal": "Grow a new channel",

    "channel_url": "https://www.youtube.com/@AnkitTerraceGardening",
    "plan": [],

    "research_required": False,
    "research_sources": [],
    "strategy_required": False,

    "youtube_results": [],
    "youtube_analysis": {},

    "creator_youtube_results": [],
    "creator_youtube_analysis": {},

    "rag_context": [],

    "strategy": {}
}


result = creatorboost_graph.invoke(initial_state)


print("\n\n========================================")
print("       CREATORBOOSTAI FINAL RESULT")
print("========================================")


print("\nPLAN:")

for item in result["plan"]:
    print("-", item)


print("\nRESEARCH REQUIRED:")
print(result["research_required"])


print("\nRESEARCH SOURCES:")
print(result["research_sources"])


print("\nSTRATEGY REQUIRED:")
print(result["strategy_required"])


print("\nYOUTUBE ANALYSIS:")
print(result["youtube_analysis"])


print("\nYOUTUBE RESULTS:")

for video in result["youtube_results"]:
    print(video)


print("\nSTRATEGY:")
print(result["strategy"])


print("\n========================================")