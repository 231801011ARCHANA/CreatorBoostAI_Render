from agents.rag_retrieval import rag_retrieval_agent


test_state = {
    "niche": "Gardening",
    "platform": "YouTube",
    "goal": "Grow a new channel",

    "plan": [],

    "research_required": True,
    "research_sources": ["youtube"],
    "strategy_required": True,

    "youtube_results": [],
    "youtube_analysis": {},

    "rag_context": [],

    "strategy": {}
}


result = rag_retrieval_agent(test_state)


print("\n\n========================================")
print("          RAG TEST RESULT")
print("========================================")


print("\nRetrieved RAG Context:")

for item in result["rag_context"]:

    print("\nNiche:", item["niche"])
    print(item["content"])


print("\n========================================")