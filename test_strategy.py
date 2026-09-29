import json

from agents.content_strategy import content_strategy_agent


with open("data/youtube_cache.json", "r", encoding="utf-8") as file:
    youtube_results = json.load(file)


state = {
    "niche": "Fitness",
    "platform": "YouTube",
    "goal": "Grow a new channel",
    "plan": [],
    "youtube_results": youtube_results,
    "strategy": {}
}


result = content_strategy_agent(state)

print("\nFINAL STRATEGY:")
print(result["strategy"])